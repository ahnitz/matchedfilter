# The CPU direct refine

A hierarchical plan refines each pair its last coarse tier passes. Until now that was a
whole-block inverse transform per pair: an n-point FFT and a peak scan over every lag, to
find a peak the coarse tiers had already placed within a few samples. The direct refine
evaluates only the lags around that place, by direct correlation of the series with the
template's real FIR taps.

## What it computes

For template t with L taps and centre c = L // 2 (the filter whose spectrum the plan holds,
`time_domain._tap_spectra` at a tap/data rate ratio of 1), the refine's value at block lag
tau inside the template's valid range is exactly

    z[tau] = sum_{k < L} taps[k] * x[tau - c + k]

with no wrap and no 1/n scale -- the transform's value to float32 rounding (~5e-7 relative
on the captured calls). The kernel (`src/td-inl.h`) vectorises across consecutive output
lags: every load is unit stride, each tap is one broadcast, and a single survivor fills
every lane. One Highway source serves every x86 and ARM target. About 0.09 ticks per
lag x tap on a Zen 5 core; a 33-lag window of a 215-tap filter is ~600 ticks against
~3,300 for the 2048-point transform refine.

## Where it looks

With one bin per pair (the consumer's mode: `binsize = n`), direct refinement returns the
largest |z| within its local refinement window. It does not establish the maximum over the
whole requested output bin. The refine evaluates `halfwidth` coarse samples either side of the pair's
largest last-tier coarse lag (the tier already reports it). `halfwidth` comes from the gate
model itself (`gatechain.direct_halfwidth`), on the draws the thresholds are set from
(`signal_draws(..., lags_too=True)`: the same simulation, search window and draw count),
every tier applied with its threshold. Among the draws every tier passes and the fine stage
keeps, it takes the distance from the last tier's coarse maximum to the fine peak; the
model's half-width is the smallest whole number of coarse samples (at least 1) beyond which
at most `_LOCALISE_SHARE` (5%) of fd of those draws lie, and the plan runs that plus one
coarse sample (`HierarchicalFilter._direct_halfwidth`). The window therefore adds at most
that share to the chain's dismissals, on top of the gates' budget. It is a property of the
reference profile and the chain, in samples, not a constant. Some draws always lie far out:
a noise peak elsewhere in the window can be the last tier's maximum while the signal is the
fine one. Where they exceed the share, the half-width grows to reach them, up to the whole
window, and the per-pair pricing (below) then takes the transform. When the rule was
introduced (b1519cf9, 2026-10-26), every chain checked at fd 1e-2 stayed within 8 coarse
samples, and at fd 1e-3 a chain ending in band 512 on the inspiral profile at n = 2048
lost 5% of its budget at any half-width.

Checked on captured `pycbc_inspiral_fir` calls (12 groups, 1.08M pairs, n = 2048, threshold
6): every above-threshold fine peak -- 34 noise triggers and 25,487 signals drawn as the
model draws them -- lay within 0.5 coarse samples of a last-tier lag at or above threshold,
and at most 4.5 coarse samples from the last tier's argmax.

## When it does not apply

- Several bins per pair: one window cannot promise every bin's maximum; the transform runs.
- A window that would read outside the block (never, inside the valid range).
- A maximum on a window edge that the search window did not put there: the peak may be
  outside, and the pair takes the transform.
- Priced dearer than the transform (wide window x long filter): per pair, from both prices
  timed on the core when the plan turns it on.
- Rate ratio != 1 (the spectra are then cut or padded; the taps are not the filter), GPU
  plans, `ap_hmf_run` without a time series, and `MF_DIRECT_REFINE=0`.

**One documented difference.** With one bin per pair and two above-threshold excursions in
one block (two signals, or two lobes of a glitch), the direct refine reports the excursion
at the last tier's coarse maximum, which need not be the larger fine one. Both are
triggers; the transform reports the larger. In Gaussian data at threshold 6 the case is
~1e-9 per pair (34 triggers in 1.08M pairs); `tests/test_direct_refine.py` pins it down.
Removing it needs the last tier to report every lag above threshold, not just its maximum.

Set `MF_DIRECT_REFINE=0` before constructing the bank when downstream code requires the
full-bin maximum for every surviving pair. This retains hierarchical screening and its
calibrated dismissal behavior, but uses a full transform for refinement. The edge fallback
only detects a local maximum running into the refinement-window boundary; it cannot exclude
a stronger, disconnected excursion elsewhere in the bin. Values from direct correlation
agree with the transform at the reported lag to floating-point rounding, rather than being
bit-identical.

## What it buys

The cost model charges a chain the cheaper of the measured transform refine and the direct
refine priced for its last band (`CostModel.with_direct`), so the chain choice sees the
cheaper confirmation, and the chain-choice key and a standalone plan's trial key say whether
it is priced in (`HierarchicalFilter._direct_key`, `_plan_trial_key`).
On the captured calls (Zen 5, chains locked by their own trials, interleaved in one
process and cost file): 13.7% less wall, identical peaks. The larger part is the chain:
with confirmation cheap, half the groups lock a 128-point first tier, (128, 256, 512), where
without it every group runs (256, 512, 1024). With the chain pinned to (256, 512) the refine
alone goes from 8.6% to 3.6% of the call. Hosts whose transform is slower relative to their
FMA rate (AVX2: dev1, Haswell, where the refine was ~20% of the call on 2026-10-04) should
gain more; not yet measured.

## Next

- Measure on Haswell and dev1 through the consumer.
- The GPU refine has the same whole-block waste, and more (a survivor's full forward is
  recomputed first): the same localisation, a direct kernel per backend.
- Let the last tier report its above-threshold lags (removes the documented difference and
  lets the window shrink to the excursion).
