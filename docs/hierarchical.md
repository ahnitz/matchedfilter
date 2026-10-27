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
floating-point accuracy, except that the [CPU direct refine](cpu-direct-refine.md)
searches only near the last tier's coarse maximum. The hierarchy can omit triggers.

## Choosing the gate

Set the reference to the expected output power versus frequency (for the
usual whitened matched filter, proportional to `|H|² / S`). Its amplitude
cancels, but its **complete shape** matters. The gate model
(`gatechain.signal_draws`, `gatechain.noise_block_maxima`) simulates the
joint coarse and fine statistics from it, including correlated noise,
spectral truncation and lag-grid scalloping, with every maximum taken over
the whole searched window as the engine takes it. A tier's threshold is the
requested conditional false-dismissal quantile at the constructor's `snr`
(`gatemodel.gate_for` for one tier, `gatechain.chain_thresholds` for a chain).

`fd` is a mean target for matching signals under Gaussian noise, not a
bound on every plan, population or finite realization. Each plan's budget
rests on about a hundred dismissed draws, so individual plans scatter about
it; see [what `fd` means](architecture.md#what-fd-means) and the
[dated model log](gate-model.md).

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
`max_tiers` (default 3; a GPU runs at most two) power-of-two bands is priced:

* **thresholds** -- the false-dismissal budget `fd` is split between the
  tiers from the same joint signal draws (`gatechain.chain_thresholds`);
* **noise pass rates** -- simulated from the reference over the block's
  searched lags, jointly across tiers (nested tiers share their noise);
* **tier costs** -- measured once per process on the machine itself, through
  the engine's per-tier counters on the CPU (`gatechain.calibrate_costs`, well
  under a second) and device timers on a GPU
  (`_calibration.calibrate_costs_gpu`). Nothing is tabulated or shipped.

The plan runs the model's cheapest chain; chains within 5% of it are tied
and go to the cheaper one on a calibration-free operation count
(`gatechain.pick_stable`). The chain is not measured on the workload: its
merit depends on the profile. What is measured on the real calls is the Q15
screen as the first tier (on CPU back ends that have one) and, in a
`TimeDomainFilterBank`, the block size, in one joint trial
([measured choices](architecture.md#measured-choices)). `MF_AUTOTUNE=0` keeps
the model's settings instead, and `MF_CHAIN_FORCE` forces a chain for
measurement.

Tier costs are timed, so under varying machine load two runs can calibrate
differently and pick different chains or budget splits -- each within the
dismissal budget, but not with the same triggers near threshold. For
reproducible runs set `MF_COST_FILE=<path>`: cost models are read from that JSON
file and any missing one is measured once and added. With the file populated
and `MF_AUTOTUNE=0`, the choice is deterministic.
`config` reports the chain in use. `autotune_info` reports it too, with its source
(status `model`, `forced` when `MF_CHAIN_FORCE` replaced the model's chain, or `pinned`)
and the joint-trial arm the plan runs.

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

The model runs at plan preparation, not in the filtering loop. Its
simulations, draws and plans are cached by entry count (least recently used
first) and shared by profiles that agree in shape and in each band's signal
response (`gatechain._similar_get`). Tighter budgets need more signal draws
(20,000 at .01, 200,000 at .001, 2,000,000 at .0001; `gatemodel._nsamp_for`).
Requests below the available resolution refuse rather than falling back to
an obsolete table. Kernel execution is unchanged.

Cost is approximately first-tier work, plus each later tier's work on its
survivors, plus the refined fraction times full-filter work. `refine_rate`
reports the refined fraction over the plan's lifetime, and `tier_stats` each
tier's passes and time (CPU plans). `tools/fdr_audit.py` measures chains'
dismissal by injection against the flat filter, two-sided, and runs in the
merge gate; `tools/audit_gate_model.py --chain ...` measures one chain.
