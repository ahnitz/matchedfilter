# The hierarchical matched filter

The filter gates pairs with a **chain** of coarse tiers before paying for the
full correlation. A tier at band `b` correlates the first `b` spectral bins
on a lag grid spaced by `n / b` and rejects a pair when its maximum is below
the tier's threshold. Tier 0 runs on every (block, template) pair; each
later tier, at a wider band, runs only on the previous tier's survivors; the
survivors of the last tier run the full matched filter. A single coarse gate
is the one-tier chain. CPU and GPU follow
this algorithm; arithmetic precision can move decisions near the gate.
Every reported survivor agrees with the flat filter within the backend's
floating-point accuracy. The hierarchy can omit triggers.

## Choosing the gate

Set the reference to the expected output power versus frequency (for the
usual whitened matched filter, proportional to `|H|² / S`). Its amplitude
cancels, but its **complete shape** matters. `gatemodel.gate_for` samples the
joint coarse and fine statistics, including correlated noise, spectral
truncation and lag-grid scalloping. It chooses the requested conditional
false-dismissal quantile at the constructor's `snr`.

`fd` is a model target for matching signals under Gaussian noise, not a
bound on every population or on every finite realization. Sampling error,
the local lag approximation and numerical precision remain. At narrow
bands the local approximation can be conservative because the real coarse
pass searches more lags. See [model validation and limitations](gate-model.md).

```python
hf = matchedfilter.HierarchicalFilter(n, ndata=16, ntemplates=32,
                                     snr=5.5, fd=1e-3)
hf.set_reference(power)
hf.set_templates(templates)
hf.set_data(data)
peaks = hf.run(binsize=n, threshold=5.5)
```

## Choosing the chain

With a reference set, the filter chooses its own chain. Every chain of up to
`max_tiers` (default 3) power-of-two bands is priced:

* **thresholds** -- the false-dismissal budget `fd` is split between the
  tiers from the same joint signal draws (`gatechain.chain_thresholds`);
* **noise pass rates** -- simulated from the reference over the block's
  searched lags, jointly across tiers (nested tiers share their noise);
* **tier costs** -- measured once per process on the machine itself, through
  the engine's per-tier counters (`gatechain.calibrate_costs`, well under a
  second). Nothing is tabulated or shipped.

The model only has to keep the cheapest chain on a short list. Chains within
its error margin of the best (`MF_CHAIN_MARGIN`, default 0.30) are then
**measured on the real workload**: plans with the same short list run it
round-robin, and the chain with the lowest measured time per pair is kept by
all of them. `MF_AUTOTUNE=0` keeps the model's choice instead (deterministic).
`config` reports the chain in use; `autotune_info` the model's choice, the
short list and whether the trial has finished.

To pin a chain, pass it; to bypass the model, give one threshold per tier:

```python
hf = matchedfilter.HierarchicalFilter(n, chain=(256, 512))
hf.set_coarse_threshold((3.9, 4.6))
```

A pinned chain with explicit thresholds needs no reference. With no
reference, coarse templates use their own in-band power fractions.
`set_coarse_threshold(None)` restores model gating and requires a reference.
`set_first_stage(snr)` changes the model's design SNR without changing the
final threshold or the chain.

## Reference groups and full-band scalloping

A single reference is not sufficient for an arbitrary heterogeneous bank.
Templates with the same in-band fraction can have different peak shapes,
and therefore different coarse-grid losses. Group compatible profiles or
validate an explicit gate for the entire bank.

Even retaining **all spectral power** does not make coarse and fine maxima
identical: the coarse grid still skips fine lags. A full-band gate may
therefore dismiss a trigger. Use `MatchedFilter` when an identical trigger
list is required; do not use `f=1` as a zero-dismissal guarantee.

## Cost and initialization

The model runs at plan preparation, not in the filtering loop. Conditional
samples are reused across gate queries and bounded by a 64 MiB LRU cache.
Tighter budgets need more samples (20,000 at .01, 200,000 at .001,
2,000,000 at .0001). Requests below the available resolution refuse rather
than falling back to an obsolete table. Kernel execution is unchanged.

Cost is approximately first-tier work, plus each later tier's work on its
survivors, plus the refined fraction times full-filter work. `refine_rate`
reports the refined fraction over the plan's lifetime, and `tier_stats` each
tier's passes and time. `tools/audit_gate_model.py --chain ...` measures a
chain's dismissal by injection against the flat filter.
