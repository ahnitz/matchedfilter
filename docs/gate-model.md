# The budget split's selection bias and per-plan scatter, 2026-10-27

A multi-tier chain searches threshold splits on the draws it is judged on and keeps
the cheapest, so its dismissal on fresh draws exceeds the budget. 3390d4f3 cut each
multi-tier budget by `gatechain._SPLIT_TOLERANCE_Z = 0.75` standard errors of the
dismissed count, the measured size of that bias, in place of the one-sided 95% cut
(1.645), which left multi-tier plans at 0.92 of the budget. The comment at
`_SPLIT_TOLERANCE_Z` and the commit message hold the measurement (200k independent
draws, n = 2048, fd 1%, 10 profiles, 30 plans).

The mean is then on budget, but each plan's realised dismissal scatters about it.
Measured at 33e22fa7 on dev2 (one pinned core, GPU hidden, load 5-7; 28 s at fd 1e-2 and
4 min 54 s at 1e-3):

- Profiles: `tools/fdr_audit.default_profiles()` (10), each at n = 2048, snr 5.5,
  window 192..1856.
- Chains: (256), (512), (256, 512), (256, 1024), (128, 512) and (256, 512, 1024),
  where every band is usable.
- Thresholds from `gatechain.chain_thresholds` on the model's own draws (seed 13), with
  no cost model, so the split is chosen on the operation count (the commit found flop and
  calibrated costs give the same bias).
- Each plan judged on N independent `signal_draws` (seed 977): the fraction of the kept
  draws (fine maximum at least snr) that some tier dismisses, over fd.

| fd | N | tiers | plans | mean | median | p90 | max | sd | check noise sd |
|---|---|---|---|---|---|---|---|---|---|
| 1e-2 | 200,000 | 1 | 20 | 1.032 | 1.049 | 1.150 | 1.207 | 0.106 | 0.029 |
| 1e-2 | 200,000 | 2 | 30 | 0.991 | 0.993 | 1.097 | 1.283 | 0.101 | 0.029 |
| 1e-2 | 200,000 | 3 | 10 | 1.012 | 1.002 | 1.109 | 1.131 | 0.077 | 0.029 |
| 1e-3 | 2,000,000 | 1 | 20 | 0.997 | 1.012 | 1.115 | 1.134 | 0.086 | 0.029 |
| 1e-3 | 2,000,000 | 2 | 30 | 0.950 | 0.943 | 1.050 | 1.133 | 0.078 | 0.029 |
| 1e-3 | 2,000,000 | 3 | 10 | 0.959 | 0.943 | 1.068 | 1.077 | 0.074 | 0.029 |

The check's own counting noise (last column) is small beside the spread, so the spread
is the plans'. It is the same for one tier, which has no split search, as for two and
three, and about what counting the ~100 dismissed draws a budget rests on gives
(`gatemodel._nsamp_for`; 1/sqrt(100) = 0.1). So it comes from the finite model draws,
not from the split search: a larger multi-tier cut would move those plans' mean below
the budget without narrowing the spread, and more model draws would narrow it.

Two observations are not settled by this run. The worst plan is 1.28 of the budget at fd
1e-2 and 1.13 at 1e-3, and no plan exceeds 1.3. At fd 1e-3 the multi-tier plans average
0.95 and 0.96 of the budget, where at 1e-2 they average 0.99 and 1.01; the cut was
measured at 1e-2 only. The plans of one profile share its model draws and its check
draws, so the 40 multi-tier plans are not independent, and one model seed and one check
seed cannot say whether that difference is real.

The script, for re-running it (from the repository root, `PYTHONPATH=python`):

```python
# split_spread.py FD NDRAWS: per-plan realised dismissal / fd on independent draws, at the shipped
# z, for 1-, 2- and 3-tier chains; with the binomial noise of the check itself.
import sys, numpy as np
sys.path.insert(0, "tools")
from fdr_audit import profile, default_profiles
from matchedfilter import gatechain as gc
n, snr, win = 2048, 5.5, (192, 1856)
fd, N = float(sys.argv[1]), int(sys.argv[2])
chains = [(256,), (512,), (256, 512), (256, 1024), (128, 512), (256, 512, 1024)]
res = {1: [], 2: [], 3: []}; noise = {1: [], 2: [], 3: []}
for name in default_profiles():
    p = gc._norm_profile(profile(name, n), n)
    bands = gc.usable_bands(p, n)
    ev = gc.signal_draws(p, n, bands, snr, N, seed=977, window=win)
    keep = ev[1][:, 0] >= snr
    for chain in chains:
        if not set(chain) <= set(bands):
            continue
        pl = gc.chain_thresholds(p, n, snr, fd, chain, window=win)
        if pl is None:
            continue
        ok = keep.copy()
        for b, t in zip(chain, pl["thresholds"]):
            ok &= ev[0][:, bands.index(b)] >= t
        lost = keep.sum() - ok.sum()
        res[len(chain)].append(lost / keep.sum() / fd)
        noise[len(chain)].append(np.sqrt(fd * keep.sum()) / (fd * keep.sum()))
print("z=%.2f fd=%g draws=%d" % (gc._SPLIT_TOLERANCE_Z, fd, N))
for k in (1, 2, 3):
    r = np.sort(np.array(res[k]))
    if not r.size:
        continue
    print("tiers %d: %3d plans  mean %.3f  median %.3f  p90 %.3f  max %.3f  share>1.25 %.2f  share>1.5 %.2f  | check noise sd ~%.3f  observed sd %.3f"
          % (k, r.size, r.mean(), np.median(r), np.quantile(r, 0.9), r.max(), np.mean(r > 1.25), np.mean(r > 1.5),
             np.median(noise[k]), r.std()))
```

# One simulation for signal and noise, 2026-10-26

The gate model is one simulation (`gatechain._simulate`, `_core.simulate`). Each
draw is a block's n bins with variance p_k. The fine statistic is their n-point
transform, and band b's statistic is the b-point transform of bins [0, b). A
signal arriving at a uniformly random time (16 sub-sample phases) is added
through linearity. Every maximum is taken over the whole searched window, as the
engine takes it.

- `signal_draws` reads each statistic's running-maximum records outward from
  the signal, so any window is two lookups, with the engine's coarse alignment.
- `noise_block_maxima` reads the same draws without the signal.

The two are one model of one noise, and the tests check that they agree.

This replaces the local lag window, the Cholesky neighbourhood draws and the
pairing with noise from elsewhere in the window. The local window missed remote
coarse maxima: in the 1% sweeps the flat profile's gates dismissed nothing, and a
bimodal profile's side lobes reached 1.74x its budget.

The sweeps through the C engine (fd 1%, 14 profiles x 4 chains, n = 2048 and
4096) are on budget. The one flagged case (inspiral, single tier, n = 2048) is
the model's own ±10% sampling: its gate is +1.4 sd over model seeds.

Only draws whose fine statistic reaches snr somewhere in the block hold records.
Where few do, as at snr = 1000, the simulation runs longer, up to 4x, until
half its draws' worth are kept.

# Retiring the accuracy table, 2026-09-26

`choose_threshold` now calls `gatemodel.gate_for` directly. The model uses
the complete reference power profile, the coarse grid and the correlated
coarse/fine Gaussian noise. ACC, ACC2, ACC2R and THR lookups are gone, along
with their files, margin placement, SNR envelopes and obsolete producers.
There is no accuracy-table fallback. Unresolvable budgets refuse; an
explicit band and coarse threshold still bypass model calculation.

The single-band functions here (`gate_for`, `dismissal`) are the one-tier
case of the gate-chain model in `gatechain`, computed from the same joint
draws. `MF_ACCURACY`, `MF_THRESHOLD`, `MF_COST` and the `tuning` argument are
gone.

## The full-band blocker was a reference mismatch

At n=4096, band=2048, SNR=5 and fd=.001, the inspiral reference produces a
gate of **4.654114**. Modelled dismissal is **.00099356**; 100,000 independent
filter injections measured **.00101235**. This is not a quantile-placement
failure.

The old test ran sixteen different template profiles against that one
reference. The matched bank loses **0 of 48** fixed-seed noise triggers;
the heterogeneous bank loses **7 of 78**. Both retain all spectral power,
but the coarse step is still two fine samples: odd-lag peaks scallop.
Full spectral coverage does not imply identical coarse and fine maxima.

| Template power-law exponent | Own fd=.001 gate | Model dismissal at 4.654114 |
|---|---:|---:|
| −7/3 | 4.6541 | .000994 |
| −2 | 4.4227 | .00919 |
| −5/3 | 4.0665 | .04396 |
| −4/3 | 3.6491 | .12263 |

The replacement tests distinguish matching references, heterogeneous banks,
and deterministic loss between coarse-grid lags. They do not replace a
budget assertion with a permissive gate. The model's gate is unchanged by
this diagnosis. Reference groups or an explicitly validated common gate
are necessary for heterogeneous banks.

## Resolution and limitations

Samples have per-component noise variance one. They are conditioned on the
fine maximum crossing SNR before the coarse quantile is taken. fd=.01,
.001 and .0001 request 20,000, 200,000 and 2,000,000 draws respectively.
Roughly half survive conditioning, leaving approximately 100 tail events:
roughly 10% relative counting uncertainty, not an exact probability bound.
Budgets with fewer than eight conditional tail observations are refused.
Obviously unresolvable requests are rejected before allocating samples.

The covariance calculation and sampling run at plan preparation, not in the
filter loop. An LRU cache is capped at 64 entries **and 64 MiB**. Its key
includes normalized profile bytes, exact SNR, band, length, draw count and
seed. This fixes the previous omitted-seed and rounded-SNR cache aliases.
The recovered fraction is clamped against floating-point overshoot at one,
preventing a negative out-of-band variance at full coverage.

(Superseded 2026-10-26: the model now takes whole-window maxima; see the top.)
The model samples a local lag window. It is validated closely for the
recorded profiles and bands, not universally exact for every spectrum or
noise population. At band 128, n=4096, fd=.001, the inspiral-profile gate
2.5550 dismissed **0 of 100,000** trial injections. This is consistent with the local approximation omitting remote coarse
maxima; that mechanism has not been separately isolated here. This
conservatism can cost throughput. The tests assert budget compliance there,
not falsely claim two-sided 10% agreement. Non-Gaussian noise and template
profiles unlike the reference are outside the calibration assumptions.

An old strict xfail asserted that *measured* dismissal must fall when the
band widens, despite choosing a different gate for each band. That is not
an invariant: one gate can underspend its budget. Its replacement tests
that every band respects the requested budget, with sufficient counts.

## Independent 1e-4 measurement

At n=1024, band=256, SNR=5.5, the benchmark reference gave gate **4.1241884**.
With a seed independent of the model and 1.5 million requested injections:

- fine detections: **860,549**;
- dismissed: **82**;
- measured FDR: **9.5288e-5**;
- model FDR at that gate: **9.9967e-5**.

Reproduce with:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/audit_gate_model.py \
  --n 1024 --band 256 --snr 5.5 --fd .0001 --trials 1500000 --seed 417
```

The standard suite now runs a real `_bench_hier` point at fd=1e-4 and checks
quantile placement at all three budgets. The benchmark already swept 1e-4;
it can now produce actual timings rather than table-coverage refusals.
Its noise-only timing rows report **requested** FDR, not measured signal
loss. `audit_gate_model.py` reports empirical counts and Wilson intervals.

## Cost migration and performance

> **Historical.** The cost tables described in this section were retired when
> configurations became gate chains: tier costs are now calibrated in-process
> on the running machine (see [the hierarchical filter](hierarchical.md)), and
> `MF_COST`, the cost files and their tools no longer exist. The section is
> kept as the record of the gate-model migration.

Cost measurements remain hardware-specific. The obsolete gate-scale axis
had inconsistent provenance across generations and cannot be interpreted
as an absolute gate for this model. Migration retains each cell's measured
baseline (the scale nearest one), with its numeric cost unchanged, and
removes the scale column. At that migration, the format was:

```
COST n band U K snr f beff relative_cost
```

Old ten-field cost files are rejected with a regeneration instruction.
Current CPU and GPU retunes use an explicit
`# format cost-fd-pairs-v1` header and place `fd` and `pairs` between
`snr` and `f`; this distinguishes eleven-field rows from the obsolete
scale rows. Older custom cost files can keep nine fields.
Cost SNR coverage is resolved per configuration, so a sparsely measured SNR
cannot hide competing bands. Costs only rank bands; they never change a gate.
At the gate-model migration the cost table was an approximate ranking without
a budget or batch-shape axis. Both shipped retunes now measure those axes.
Retuning for a workload remains useful; neither table claims globally optimal
band selection.

Interleaved 8×32 timing on the same native build selected the same bands in
five checked cases. The comparison separates a changed gate from changed
selection. Full records and the harness are in
[audits/gate-model-2026-09-26](audits/gate-model-2026-09-26).

| n / SNR (fd=.001) | Old table gate (ms) | Model gate (ms) |
|---|---:|---:|
| 1024 / 5 | .0372 | .0393 |
| 4096 / 5 | .2055 | .2652 |
| 4096 / 6 | .1063 | .0990 |
| 16384 / 5 | 2.4205 | 2.8655 |
| 16384 / 6 | 1.6887 | 1.3624 |

These are not zero-cost changes: where the new gate admits more pairs, the
filter performs more refinement. No execution kernel changed in this
migration. Cold selection at fd=.001 cost .13–.14 seconds in these cases;
warm selection cost .09–.41 milliseconds. Tighter budgets increase cold
sampling cost. Comparing unsafe table gates solely on throughput would
hide the accuracy correction this task was requested to make.

## Teaser

The regenerated [teaser](assets/teaser.svg) uses the same matched-profile
bank for flat and hierarchical paths. The old heterogeneous bank did not
satisfy the reference contract. It now includes fd=.01, .001 and .0001 as
overlapping hierarchical bars: every boundary marks total throughput.
[Raw measurements](assets/teaser.json) include selected bands and refine rates.

Both filter devices time warm public `run()` calls; GPU readback and result
assembly are included. Baselines time full-batch inverse transforms only.
FFTW uses one thread, unnormalized execution and PATIENT planning capped at
15 seconds. rocFFT operates on initialized resident storage and amortizes
synchronization over eight executes. It is no longer labelled as saturating
memory bandwidth based on an unrelated historical measurement. Historical
Apple M2 constants are not mixed into a fresh model-generated figure.

At fd=1e-4, the 16×1024, n=4096 teaser measures **8.82 ms CPU** and
**.274 ms GPU**, versus flat **46.99 ms** and **1.347 ms**. This is a workload
example, not a general speed guarantee.

## Verification and shared-checkout isolation

Isolated validation: **844 passed, 6 skipped** on the Ryzen AI MAX+ 395 and
Radeon 8060S, with hardware GPU execution enabled. There are no remaining
xfails in that run. Linux CI without GPU hardware retains CPU/model checks;
Apple CI remains responsible for Metal execution.

A concurrent session was editing the class and GPU cache implementation.
Validation used a copy of committed code plus this task's changes, with the
same native extension (SHA-256
`e242d3696275d283950008e6331c485c6057dbe7b9dd960da3f9c6dee958c21d`).
The binary matches the concurrently committed CPU broadcast optimization.
Uncommitted class/cache changes were excluded from both the validation and
teaser timings. The shared checkout was not reset or overwritten.

The teaser was remeasured after competing jobs finished, using sustained
warmup and timing blocks: with the retuned GPU costs, fd=.01 reaches
**83.71 M/s**. See the
[throughput investigation](audits/gate-model-2026-09-26/gpu-throughput-investigation.md)
for historical timing differences and concurrent-workload evidence.

After the concurrent class/cache changes were committed, the combined
working tree passed **892 tests, 6 skipped** on CPU and Radeon 8060S.

## Radeon 8060S cost retune

The 8060S now ships a device-specific, FDR- and pair-count-aware cost table.
It ranks bands separately at three budgets and two measured batch sizes;
calibration still comes only from the reference gate model. See the
[retune audit](measurements/gpu-cost-retune-2026-09-26.md), including raw
measurements and independent holdout results. The prior gfx11 family table
remains for other hardware.

## Chain choice: useless tiers and stable ties (2026-10-10)

* **How (64, 256) gets in.** Through the model's candidate list (not reproduced here as the
  winner, but present): for a reference whose power
  sits above bin 64, band 64 is still "usable" (nonzero power), and the budget split gives
  it a threshold at which it passes ~every pair (modelled reach 1.0). Its own cost is tiny
  and the sparse tier-2 price at density 1.0 is a clamped extrapolation of the 1%/10%
  calibration, so the chain could rank near the top. (The order is not narrower-then-wider:
  the GPU prints the cascade as (band, cascade_band); the chain is (64, 256).)
* **Now:** `choose_chain` skips any split in which a tier passes more than
  `_USELESS_PASS = 0.5` of its pairs on to another tier (pinned chains still get thresholds;
  the last tier's pass rate into the refine is left to the cost, since at low snr every
  chain refines most pairs). Trials record a call whose first tier passed more than that
  fraction to the next tier as infinitely slow, so such a chain cannot lock.
  `test_a_tier_that_passes_most_pairs_is_never_chosen` reproduces the (64, ...) candidates
  without the rule.
* **Stable ties.** Candidates within `TIE = 5%` are treated as tied: the model breaks ties on
  the calibration-free flop proxy, trials on (fewer tiers, smaller bands), the block size on
  the smaller n. On dev2's GPU the choice repeated across processes after this, (2048, (256,
  1024)) in every run, as on main.
* **Host cost.** A first attempt charged all of (wall - device) per block; it moved the bank
  to n = 4096 and the fine stage got 1.4x slower, because most of that residue is per call.
  Now `calibrate_costs_gpu` times the same call at two block counts and fits
  host = host_call + host_block * blocks; `price_block_sizes` charges host_block per block
  (a bank makes one call per segment, so host_call does not depend on n) and breaks ties on
  the host term. On the 8060S: host_block 2.1 us at n = 2048 and 5.7 us at 4096, against
  device block work of ~0.3/0.7; with it the n = 2048 margin over 4096 went from ~6% (inside
  the noise that made it flip) to ~30%.

## Host term removed from block-size pricing (2026-10-10)

The per-block host term added in gate/chain-stability is not charged any more. Its fit grows
the series with the block count, so it measured a per-sample staging cost (5/10/20 us per block
at n = 2048/4096/8192 on the 8060S): the same per valid sample at every n, several times the
device terms, and 2x noisy under load. It could only reshuffle near-ties, so neighbouring length
batches of one bank landed on different block sizes run to run. That fragments banks into more
template groups, hence more calls. It is a candidate for the fine-call growth on 437367c
(54 -> 258 calls per segment); the review agent's bisect decides.

dev3 Renoir, Vulkan, load < 1, 3 interleaved processes each, autotune on (2 tops x 6 segments):

| | run 1 | run 2 | run 3 |
|---|---|---|---|
| main 437367c, fine | 2.33 s | 1.80 s | 1.87 s |
| main, layout | 4096 (mixed chains) | 2048 | 2048 + 138 templates at 4096 |
| host term off, fine | 1.90 s | 1.85 s | 1.73 s |
| host term off, layout | 2048 | 2048 | 2048 + 69 templates at 4096 |

### Unused host calibration removed (2026-10-20)

The two measurement batches for that unused host fit have now been removed as
well, along with its model fields and serialization. At the default five
repetitions, this removes twelve calibration-plan calls and ten clock-reference
measurements per uncached GPU cost model. This counts removed work, not a
measured wall-time improvement. Device costs, gate thresholds, and the
smaller-block tie break are unchanged; existing cost files still load, ignoring
their obsolete `host_call` and `host_block` entries.

## Forward priced per chain (2026-10-10)

Vulkan can write only the widest tier's band of each block's spectrum and recompute the
full spectra of blocks with a refined pair (docs/vulkan-8060s-roofline.md section 13); it does
so when the refine-block fraction f < (n - B)/2n. A chain that refines few blocks therefore
pays a cheaper forward, which the cost model did not credit.

* `CostModel.forward` is the full forward per block (on the GPU, `block`: per-block fixed work
  is the forward plus small bookkeeping, and one submission cannot time it apart), and
  `band_forward` is a backend capability (`_BAND_FORWARD = {"vulkan"}`).
* `forward_cost(chain, f)` applies the backend's own byte rule: full, or a band write
  `forward * (1/2 + B/2n)` (same series read, B of n written; 0.75 at B = n/2 against
  2.8/3.8 = 0.74 measured) plus `f * forward` of recompute.
* f: only the measured fraction (`note_refine_blocks`, called by Vulkan's band measurement,
  keyed by (n, widest band)); without one a chain gets no credit. The model's
  1 - (1 - P(refine))^templates was tried first and moved 1757 of 4249 ladder templates to
  n = 8192, making the fine stage 1.4-1.7x slower. The fraction itself is right (refine density
  matches the model within 10-25%, "Refine density on realistic data" on the refine-density
  branch). What failed is that the per-term GPU costs it corrects are noisier than the credit,
  so it tipped near-ties the wrong way. The model's f waits for end-to-end block-size trials.
  Measured values do not enter the choice cache key, so a choice made once stays made within
  a process.
* `choose_chain(..., ntemplates=)` adds each chain's forward change from the full forward
  (already in `block`), shared by the templates; HierarchicalFilter and block-size pricing
  pass their template counts. With few templates a credit can take a total below zero, so
  the tie window is now `lo + TIE * |lo|`. (Adding the whole forward to every chain instead
  widened every relative tie window and, by itself, moved templates to n = 8192.)

Effect: with the model's f, (256, 1024) at n = 2048 (f = 1%) gained the band credit and tied
(256, 512); on the ladder the credit at n = 8192 went the wrong way (above). With measured-only
f, a process's first choices are the base's, and later choices see Vulkan's measured fraction.

## Block-size trials (2026-10-10): built, measured, net loss -- not ready

`time_domain._BlockTrials` builds the model's top block-size layouts (within 30% of its
cheapest; at most 2) at the first reference, while the taps are still held. Each batch of
`filter_series_many` puts every trialling bank on one candidate rank and times the batch from
submission to the last result, per template x series sample. Batches in which a bank
switched layout are not timed. The model's rank runs first. After one clean sample per
rank, the fastest within gatechain.TIE is locked (ties keep the model's choice); the
others are dropped. `tests/test_block_trials.py` checks that a clearly worse rank (1.5-10x)
is never locked, in either order, that ties keep rank 0, and that a bank's switch and lock
work end to end.

Measured on dev3's Renoir (Vulkan, load < 1), 3 interleaved processes, autotune on, 2 tops
x 6 segments, steady fine stage:

| | run 1 | run 2 | run 3 |
|---|---|---|---|
| main | 1.83 s | 1.82 s | 2.29 s |
| branch | 2.67 s | 3.81 s | 2.50 s |

The branch is slower in every run, including runs where it locked rank 0, so the cost is
not the choice itself. The likely cause, not yet proven: building a second layout doubles
each bank's GPU-resident spectra and plans on an iGPU with a small shared budget. The
dropped layout's device storage is evicted only by LRU, so live data is re-uploaded in
steady state. Two further caveats:
- One sample per rank is thin: the locked ranks differed 12-27% on single batches.
- Main itself chooses differently across processes on this host ((2048, (512,)),
  (2048, (256, 512)), mixed 2048/4096), so the baseline is not a fixed point.

Needed before this can ship:
1. Free the dropped layout's device storage explicitly at lock (GPU cache API), or build the
   alternative only for the batches that trial it.
2. Take more than one sample per rank, still within the warm-up: time per bank rather than
   per batch.
3. Then re-measure.

Until then the forward credit stays measured-only.

### Block-size trials, second round (2026-10-10): still a net loss; why

Changes:
- Trial batches run each bank alone, so each bank gives a paired sample: rank r against rank 0
  on the same bank. There are 22-27 samples per rank within the warm-up.
- A lock evicts the dropped layout's device storage, and only if that layout ever ran.
- Banks built after the lock adopt the winner with no trial batch.

dev3 Renoir, load < 1, steady fine stage:

| | main | trials off (MF_BLOCK_TRIAL_RANKS=1) | trials on |
|---|---|---|---|
| run 1 | 2.25 s | 2.32 s | 2.80 s (locked rank 1, paired ratio 0.90) |
| run 2 | 2.32 s | 1.79 s | 3.15 s (locked rank 1, 0.89) |

The machinery costs nothing: with trials off the branch matches main. What the trials lock is
wrong. Rank 1 is "the second-cheapest n per length batch", and that mixes block sizes within
a bank (2596 templates at 2048 and 2102 at 4096 in one run). Timed alone, each bank was ~10%
faster that way. In steady state the banks run fused and concurrently, and the extra
template groups -- more calls, smaller dispatches -- cost more than that.

Two conclusions:
1. Candidates must be whole-bank layouts at one n each (n = 2048, 4096, ...), not per-batch
   rank mixes.
2. A solo per-bank sample does not predict fused steady-state time. A representative sample is
   a whole fused batch, at roughly one per batch. Two or three candidates at three samples each
   do not fit a two-segment warm-up. They fit if the lock is persisted in MF_COST_FILE (keyed by
   device and the bank's candidate set), so a machine pays for the trial once rather than once
   per process. That also makes the choice stable across processes.

Not shippable as is.

### Block-size trials, round 3 (2026-10-11): whole-bank candidates, fused-batch samples, persisted lock

- **Candidates per bank.** The model's own layout is rank 0. After it come the whole bank at each
  of its cheapest single block sizes: sizes every length batch can use, ranked by their summed
  modelled cost. A single size whose partition equals the model's is skipped. There are at most
  3 candidates (`_BLOCK_TRIAL_RANKS`). `price_block_sizes(ahead=)` prices that many sizes past the
  first dearer one so that they exist.
- **Samples.** A sample is one whole `filter_series_many` batch, fused and concurrent as in steady
  state, timed from submission to its last result, per template x series sample. A rank's first
  batch after a switch only settles (it uploads). There are 2 samples per rank. Rank r > 0 wins
  only if its median beats rank 0's by more than gatechain.TIE, so a tie keeps the model's layout.
- **Persisted lock.** The winner is stored in MF_COST_FILE under `choice|block-trial|<device>|<candidate
  set>` (`block-trial|...` before 2026-10-21). A bank whose key is on file adopts it at its first reference with no trial, and only
  layouts that ran are evicted from the device at a lock.
- **Only where the lock can be kept.** Without MF_COST_FILE (or with MF_AUTOTUNE=0) no candidates
  are built and no trial runs. The bank is the model's layout, exactly main's behaviour. A trial in
  every process would cost that process its warm-up and more (the trial process below), for a few
  percent.

dev3 Renoir, Vulkan, load < 1. Each side has its own fresh MF_COST_FILE, the processes are
interleaved, the configuration is 2 tops x 6 segments, and the figure is the steady fine stage.
Main with a cost file is the fair baseline: with persisted cost models it is itself stable,
(2048, (256, 512)) at 1.14-1.26 s, against 1.8-2.3 s and varying layouts without a file.

| process | main | branch |
|---|---|---|
| 1 (branch runs its trial) | 1.26 s | 4.09 s (trial: 8192 at 2.1x, 4096 at 1.08x, locked the model's) |
| 2 | 1.15 s | 1.09 s |
| 3 | 1.14 s | 1.09 s |
| 4 | 1.14 s | 1.09 s |
| 5 | 1.20 s | 1.08 s |

Second set (final code: candidates built only with a cost file), fresh cost files:

| process | main | branch |
|---|---|---|
| 1 (trial) | 1.36 s | 4.39 s (4096 at 2.4x, 8192 at 6x; locked the model's) |
| 2-4 | 1.35 / 1.34 / 1.34 s | 1.34 / 1.34 / 1.35 s |

After the one trial process, the branch is never slower than main (equal in the second set, 4-10% faster in the first), and the
same layout in every process. In both sets the trial confirmed the model's layout; the gain in the
first set comes from the calibrated cost models in that file, not from a different layout.
Where the model is right, trials buy stability and a guard against its mistakes, not speed. The trial costs one process's fine stage once per machine and
candidate set, not once per process.

### Model-f proposals, pooled trials, and persisted chain locks (2026-10-11)

- **Model f proposes, the trial decides.** Block-size trial candidates are ranked with the band-
  forward credit at the model's refine-block fraction (`price_block_sizes(model_f=True)`,
  `CostModel.chain_forward_delta(model_f)`). Rank 0 stays the model's own layout, priced without
  that credit, so model f can only add a candidate. Its own pricing never changes a choice. On the
  dev3 ladder the proposals are the same sizes as without the credit (4096, 8192), and the trial
  keeps the model's 2048 layout.
- **Pooled trials, cheap adoption.**
  - The trial key is the device plus the candidate block sizes. Ranks mean the same in every bank:
    0 is its model layout, k is its k-th proposed size. All banks of a search pool into one trial.
  - Each bank's proposal list is kept in MF_COST_FILE under its model layout. A later process maps
    the lock's rank to the bank's size without pricing proposals, and builds only the winner.
  - Pricing extra sizes (`ahead`) happens only when proposing. Keys per bank fragmented the trial,
    so the first version re-ran trials and paid ~30 s of warm-up in every process.
- **Chain-trial locks are persisted too** (`choice|chain-trial|n|snr|fd|tiers|device` since
  2026-10-21, used only if the stored chain is on the plan's shortlist).

**The unexplained 4-10% gain, isolated.** It was not the block-size layout. In matched processes
with the same layout and the same chain, (2048, (256, 512)), main's steady fine stage was 1.08-1.12 s
and the branch's 0.94-0.96 s. Main runs its chain trials in every process: one candidate needs
MF_CHAIN_TRIALS = 6 calls, and the trials run past the two warm-up segments into the steady ones.
Some processes even lock a different chain, e.g. (256, 1024) at 1.12 s. With the lock on file, no
trial runs and the steady segments are clean.

dev3 Renoir, load ~1. Each side has its own fresh MF_COST_FILE, the processes are interleaved, the
configuration is 2 tops x 6 segments, and the figure is the steady fine stage:

| process | main (block-trials round 3) | branch |
|---|---|---|
| 1 (trials run, files written) | 4.12 s | 4.58 s |
| 2 | 1.09 s | 0.94 s |
| 3 | 1.09 s | 0.95 s |
| 4 | 1.12 s, chain (256, 1024) | 0.96 s |
| 5 | 1.08 s | 0.94 s |

After the first process the branch is 12-15% faster in steady state, and identical from process
to process. The first process of each side carries both kinds of trials, once per machine.

### Every measured choice is per machine (2026-10-11)

`gatechain.stored_choice` / `store_choice` keep a measured choice in MF_COST_FILE next to the
cost models, the chain locks and the block-size locks:
- CUDA's coarse kernel variant, timed at first use per device and band
  (`cuda-coarse|<device>|<band>|<variant set>`).
- Vulkan's fused interleave depth per batch shape (`vk-interleave|<device>|<shape>`).

Metal has no timed choice today. Each choice is valid, but made afresh per process they
differed on noise (variants round differently), so borderline pairs gated differently in 1-3
jobs per segment. With a cost file a machine makes each choice once.
`tests/test_reproducible_choices.py` runs three processes on one cost file, on the CPU and
on gpu:0 where present, and requires identical triggers, layout and chains: the second and
third processes against each other, and against the first process's locked segments.

## CPU paired trials and bounded measurement (2026-10-15)

CPU Q15 and block-size trials now use complete rounds on identical workloads.
Q15 replays the same series call; block-size trials replay the same batch of jobs
at every candidate layout, holding each layout's inner chain and Q15 trials.
Each arm settles before timing, and execution order reverses between rounds.
The decision uses per-round ratios against the model and requires 75% agreement
beyond the existing 5% tie margin. A single contaminated round affecting only one arm cannot
win a five-round trial. Sustained or systematically arm-correlated interference
can still bias the result; this is robust sampling, not a guarantee under arbitrary load.

CPU block trials take at least five complete rounds (or MF_BLOCK_TRIALS if larger)
and cap an ambiguous contest at twice that minimum. Q15 takes at least six by
default and caps at twelve. Complete partial rounds persist between processes.
Old unpaired partial block samples are not valid paired evidence and are restarted;
existing final locks are preserved. No additional candidate is excluded. The GPU
measurement and decision paths retain their existing behavior.

This increases first-run calibration work: each round executes every candidate,
including an untimed settling call. It does not promise that two fixed warmup
segments will suffice. `tools/ladder.py` reports `cpu_trial_work_in_steady` and
`steady_valid`, with a warning if CPU trial work occurs after the first steady
boundary. The counters include Q15 replays, CPU block rounds, and CPU chain calls
(including chain switching); they do not measure all cost-model construction in
initial setup. For multiple tops the first boundary is conservative: later tops'
calibration also invalidates the report.

Use the bounded study driver to keep calibration out of accepted CPU timing:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 6 python tools/cpu_trial_check.py \
  --bank BANK.hdf --profiles PROFILES.npz --out NEW_DIRECTORY --starts 10
```

Each independent start uses a fresh cost file. By default it permits at most four
six-segment processes, retaining every log, report, and lock transition. A run is
accepted only if no CPU trial occurs after the steady boundary, no trial lock
changes during that process, and no persisted trial remains unfinished. Failure
to settle is reported as failure, not silently labelled steady. Compare two code
versions only after comparing their complete trial-lock dictionaries; force the
same locks when measuring execution overhead rather than choice quality.

### Chain-trial audit and remaining limitation

CPU chain trials still pool cost-per-pair observations from different calls and
plan shapes. Their candidate union can grow as plans with different shortlists
join; candidates need not be feasible on every plan. They therefore have the same
comparability risk as the old Q15 trial. Unlike Q15, chains can change borderline
outputs, and switching rebuilds plans, templates, and thresholds. This patch
instruments that calibration work but does not change chain selection, feasibility,
existing usefulness checks, or the shared GPU decision rule. A follow-up should
pair each challenger with a feasible incumbent on the same input and preserve the
candidate union explicitly; normalizing unrelated timings by pair count is not a
substitute. Persisted chain locks and reproducibility behavior remain intact.

Raw cold-start records, frozen-source identities, and controlled timing are in
[the CPU trial measurement record](measurements/cpu-trial-reliability-20261015/README.md).

## Replacing cost planning: feasibility study (2026-10-20)

The current infrastructure contains runtime price calibration, scientific gate
selection, and several persisted execution trials. It also stores device
capability decisions such as accurate GPU trigonometry. Removing price curves
does not remove the need for valid gate thresholds, reproducible resolved plans,
or those capability checks.

Two study tools separate the questions:

* `tools/cost_model_ablation.py` uses captured reference profiles and model
  windows to compare measured-cost planning with the existing `cost=None`
  operation-count proxy. Both price the same accuracy-valid candidates. It
  reports thresholds, candidate counts, shortlist coverage, and setup phases.
  Its regret is a **cost-model estimate**, not a runtime measurement.
* `tools/real_probe_study.py` freezes the prepared production chain and
  thresholds, then tests float-only, ordinary Q15, and delayed-recheck Q15 on
  one native plan. It uses the full template bank and stratified whole native
  groups of real input, validates sparse outputs and native output counts, and
  separately times full calls. A duplicate baseline configuration measures
  timing noise; it is not credited as a policy improvement.

On the retained 72 CPU leaf captures, there is **one distinct reference profile**
and two model windows, `[128,1920)` and `[192,1856)`. These are not 72 independent
gate-model validations. Measurements used one pinned core, one numerical-library
thread, fixed n=2048, production thresholds, and no `MF_HMF_PROF`.

| Experiment | Observation |
|---|---|
| Fresh CPU n=2048 cost model | 1.31 s |
| Signal draws, two windows' noise draws, candidate enumeration | 2.01 s additional setup |
| Global operation-count top five | All start at band 128; exclude the current model's `(256,512,1024)` winner |
| Best operation-count candidate per first band | Five representatives include that winner |
| Same-source, interleaved full leaf replay of the proxy's choice | `(128,256,512)` without Q15 takes 1.304 times the baseline time |
| Outputs in that chain comparison | 207 versus 205 peaks; one capture differs |
| Fixed-science Q15 execution study | All three variants reproduce the prepared bank's 205 peaks exactly |

For the two selected chains, operation-count and current-cost threshold vectors
coincided. Thus the chain replay tests the proxy's selected chain and screen
choice without an additional threshold-allocation difference. In general costs
also select a threshold-budget split; changing them is not just rescheduling an
unchanged decision.

The 32-block pilot took a median 5.0 ms per bank, including switching, warm calls,
validation and selection; 71 of its 72 samples had fewer than ten refinements.
Starting its selector from float-only still chose a Q15 variant in every case,
using the recorded pilot times alone. Distinguishing the two Q15 orders was much
less reliable. Against the fastest of separately measured full-arm medians, the
32-block choices had 0.62% aggregate apparent regret, with ten captures outside
2%. Identical baseline configurations themselves differed by as much as 6.2%
between measurements. These numbers do not establish a small speedup or a
no-regression replacement. The full-arm minimum is also optimistic under noise.

The probe still uses seeded costs to prepare its scientific plan. It does not
remove calibration end to end, and none of these results is a whole-search
benchmark or an independent false-dismissal bound. Larger 64- and 128-block
pilots cost more and did not establish a better selector on this dataset.

The promising replacement is a small, diverse menu of accuracy-valid complete
plans, followed by one bounded real-input trial and an optional saved resolved
plan. That record should contain literal thresholds and compatible execution
settings, not a rank into a changing candidate list. First-band diversity is a
useful starting point; coverage across other profiles, block sizes, devices and
real GPU batch/fusion modes still needs measurement. Rare refinement choices
need more evidence than a small dense-screen pilot supplies.

Production selection remains unchanged in this branch. Only the unused host
calibration described above is removed. This preserves active cost arithmetic
and avoids introducing another production tuning mode before the replacement
has passed cold-start and settled full-search comparisons.

### Block sizes decided on real calls, by absolute rank (2026-10-26; superseded below)

- **Why.** The CPU cost model is calibrated on hot-cache microbenchmarks (64 templates, 32 blocks).
  On a loaded Haswell node real per-stage costs were 1.1-2.4x the calibrated ones, differently per
  block size (later tiers 1.32x at 2048, 2.43x at 4096), so the model priced 4096 at 1.2x 2048
  where it ran 1.6-1.95x, and fresh processes put 0-231 of test67's 323 banks on 4096. Correcting
  the model from the running size's own calls cannot fix that (2048's factors applied to 4096
  predicted 1.41x, against 1.95x on the same calls).
- **What.** The block-size trial runs without MF_COST_FILE: its lock is the process's, pooled over
  every bank of a search, so the first reference's banks settle it. CPU leaves of a search run as
  one filter_series_many batch, where the CPU trial's paired rounds sample.
- **Ranks.** A bank's candidates are the whole bank at its smallest single sizes, smallest first,
  then the model's layout. A rank is the same size for every bank of a trial, a tie keeps the
  smallest size, and the model's layout is kept only when it wins outright. Ranks whose built
  layouts are the same object share their samples (they can only tie). A locked size is built
  without any block-size pricing, so later banks skip the larger sizes' simulations.

## One joint trial for block size, chains and the screen (2026-10-26)

Supersedes the block-size, chain and Q15 trials described above. They were three mechanisms
for one decision. They differed in what a candidate was (model-relative ranks; one chain for
every plan; a screen setting per full chain), in what a sample was (paired rounds; single
unpaired calls; batches; replays inside one call), and in what they pooled. Each of those
differences caused an error that has been measured:

* Candidates relative to the model chose among the model's errors. The block trial's rank 1
  could mean 4096.
* The chain trial pooled plans of every profile into one lock, one chain for all of them.
  Paired on the same input, each plan's own model chain was faster than that lock per steady
  call: dev2 -7%, dev1 -10%, Haswell -11% to -14%, Ivy -2% (test67 leaves).
* The Q15 trial was keyed by the full chain, although the screen concerns only the first
  band. With plans on four chains, four paired Q15 trials opened for what is one decision.

### The mechanism (`_trial`)

One trial per key decides every coupled dimension at once, over complete configurations:

* **Arms.** `default` puts every dimension at its default: the bank's smallest candidate block
  size, each plan's model chain, and the model's screen setting for that chain. It is the
  preference. In the first pass every other arm moves one dimension, and the model fills in
  the rest conditional on it:
  * `n=4096`: the next single block size;
  * `n=model`: the model's own priced layout;
  * `q15=0` and `q15=1`: the screen off or on.

  Chains are not arms: each plan runs its model chain. A pooled chain decision, sampled on a
  search's first banks, picked a chain faster there and 5-10% slower over the rest.

  An instance that cannot take an arm's value runs its default there, for example a chain
  outside a plan's feasible set, or a screen its first band does not have.
* **Resolution.** Each instance (a bank, or a plan used on its own) resolves an arm to its own
  configuration. Arms an instance resolves alike are one configuration, timed once, so they
  can only tie.
* **Rounds.** A sample is a paired round (`Choice.play`, the engine every trial uses). Every
  distinct configuration of the live arms runs the same work back to back, each timed run
  right after an untimed run of the same configuration (on a GPU, replays until no recording
  is built): a GPU batch run second ran 20-30% faster, so every timed run is a second run.
  The order reverses each round. On the CPU the untimed runs cost the cap67 replay at most
  0.35 s more than settling each configuration once (under 0.5% of the job). Rounds pool as ratios to `default` (`paired_choice`),
  so banks and plans of different cost pool into one trial. That pooling is also why a round
  needs only a few banks: it replays two of the batch's trial banks (`_ROUND_BANKS`, rotated
  from round to round over the batch), and the rest of the batch runs once on `default`. A
  test67 batch holds 17 leaf banks. Replaying all of them twice per configuration cost 11 s of
  a 74 s job; two banks per round, settled once, cost 2.6 s.
* **Elimination.** An arm is dropped from later rounds once it can no longer win, that is,
  once its wins plus every round still to come cannot reach the share `paired_choice` needs
  at the cap (`_choice.can_still_win`). The rule is exact: a test enumerates every win/loss
  history against `paired_choice`. Arms that only tie with `default` leave after three
  rounds, and so does a clearly slower arm.
* **Confirmation.** An arm the rule picks over `default` is not locked at once. A fresh
  contest of `default` against it alone must pick it again, or `default` stands. On a loaded
  node a round's ratios swing by +-30% (Haswell at load 55: one arm read 0.65, 1.07, 0.84,
  1.08 and 0.98 of `default`, its true ratio about 1). With seven challengers, one passes the
  75% rule on noise more often than one alone does: an unconfirmed trial on a loaded Ivy
  Bridge locked a fixed chain with the screen off, and ran 18% slower.
* **Passes.** A pass locks at its first confirmed winner, keeps its base on a tie, and stops
  at its cap (`2 x MF_TRIAL_ROUNDS` rounds) or its budget of calls that could not be rounds.
  A pass that locks an arm other than its base opens the next pass around that arm: the arm,
  and the arm with each dimension it has not moved moved too (`n=4096,q15=0`;
  `_trial.current_pass`, `_settings.around`). The trial ends at a pass that keeps its base.
  A first pass that keeps `default` ends it, so only a trial that moved pays a second pass.
  The GPU device trials (`gpu-batch`, `gpu-kernels`) search the same way.
* **Locks.** The trial's end is applied by each instance resolving the winning label,
  including instances made later. A bank made after a lock builds only the winner's layout.
  For a lock that moves no block size, or moves it to a single size, no block size is priced
  at all. Each pass is kept in `MF_COST_FILE` (`choice|joint|<key>`, then
  `choice|joint|<key>|<base>`) when one is set, and an open pass resumes in the next process.

Banks run their rounds in `filter_series_many` (`time_domain._joint_round`), on the CPU and
GPU alike. A plan inside a bank is governed by the bank's trial. A plan used on its own runs
its rounds in `run_series`.

### Why `default` is the smallest size, not the model's layout

The first version made the model's layout the preference. On the test67 replay at 12 calls
per bank (the job's mean) it was 19% slower than main. A tie kept the model's layout, which
put some banks on 4096, and every bank built after the lock paid for block-size pricing.
With the smallest size as the default, a tie keeps the layout that needs no pricing. That is
the rule step 1 of this work had already measured for block sizes.

### Coupling

Before building it, I checked that deciding jointly was needed. Each bank (every fourth bank
of test67) ran 8 complete configurations, paired: {2048, 4096} x {each plan's model chain, one
chain for all} x {Q15 on, off}. On dev2, dev1, Haswell and Ivy no dimension's ranking depended
on another:

* 2048 with per-plan chains and Q15 on was best everywhere.
* The single chain cost +2% to +8.5%.
* Q15 off cost +18% to +46%.
* 4096 cost +50% to +84%.

The one interaction was at 4096 on Haswell, where the single chain beat per-plan chains by
6%. 4096 lost by 50% there, so it changes no decision. The joint form is still the one
mechanism, and it would catch a coupling on a machine where one exists.

### Calls per bank

A test67 job (2048 s of data, dev2) calls each of its 319 leaf banks 12.6 times on average
(median 10, max 66), plus 5 single-template follow-ups. Bank calls took 22.3 s of the 73 s
job, against 4.2 s in `set_reference`. The setup replay tools capture only a bank's first call
per reference; replay at `K = 12` for the production regime.

### Results

test67 replay, all 323 banks, 12 calls each, interleaved with main (5fbcc4fc):

| machine | main | joint | |
|---|---|---|---|
| dev2 (Zen 5) | 21.6, 21.9 s | 20.8, 20.7 s | -4.6% |
| dev1 (Zen 3) | 47.1, 47.3, 47.4 s | 44.4, 44.2, 44.8 s | -6.0% |
| Haswell | RESULTS | | |
| Ivy Bridge | RESULTS | | |

Every bank ends on 2048 with the screen on for every plan (main left two plans' screens off),
and each plan runs its own model chain.

`MF_TRIAL_ROUNDS` replaces `MF_BLOCK_TRIALS` and `MF_CHAIN_TRIALS`. `tools/migrate_cost_file.py`
removes the superseded trial records from a cost file.
