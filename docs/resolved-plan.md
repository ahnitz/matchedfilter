# The resolved plan

Before a hierarchical filter runs, it settles everything that decides which pairs are
refined. That settled set is the **resolved plan**. This note says what it holds, where it
is resolved today, what it guarantees with and without a shared cost file, and what of it
is public. Robustness-plan E6 (one `resolve()` per filter) implemented it on
2026-10-22.

## What it holds

For one `HierarchicalFilter` (and each plan of a `TimeDomainFilterBank`):

- **chain**: the coarse bands, one per tier;
- **thresholds**: one per tier, from the reference model for that chain (or explicit);
- **Q15**: whether the CPU int16 screen runs as the first tier;
- **direct refine**: on or off, and its window half-width;
- **GPU**: each tier's coarse layout and the calibrated gate;
- **bank**: the block layout (`TimeDomainFilterBank.chosen_layout`).

It is a function of the filter's inputs (n, block and template counts, SNR and first-stage
SNR, false-dismissal budget, search window, reference, taps, device) and of two
machine-level facts: the measured cost models and the locks of the measured choices.

## Where it is resolved

`HierarchicalFilter._resolve` computes the chain, one threshold per tier, the model's
refine reach, each tier's share of the reference's power and, on the CPU with taps, the
direct refine's half-width, once, as an immutable `_Resolved`. Every setter that changes an
input drops it (`set_reference`, `set_first_stage`, `set_coarse_threshold`, `set_taps`), as
does building a new CPU plan. The CPU plan applies it once per plan and resolution
(`_execution_plan`); the GPU path reads it (`_gpu_calibration`).

| Item | Where |
|---|---|
| chain | `_choose_chain`: the model's ranking (cached per profile in `_chains._CHAIN_CHOICE`), or `MF_CHAIN_FORCE` for measurement; a pinned chain as given |
| thresholds | `_thresholds` (via `gatechain.chain_thresholds`), or explicit |
| Q15 | the plan's joint-trial arm (`_arm_q15`): the arm's setting, else the cost model's (`_chains._Q15_MODEL`); off for a pinned chain |
| direct refine | `_resolve`: the half-width of the thresholds' plan (`gatechain.plan_chain`, through `_thresholds`); none with explicit thresholds |
| GPU kernels | the device's kernel choices: the coarse layout and gate way per band (`_gpuhier`) |
| bank layout | the bank's joint trial (`TimeDomainFilterBank.set_reference`, `time_domain._joint_round`) |

The Q15 setting and the bank layout are joint-trial arms: they are applied by each
instance's `use_arm` and `lock_arm`, outside the `_Resolved` record.

## What it guarantees

**With a shared `MF_COST_FILE`:**
- **Measurements are shared:** cost models are measured once and stored, and a stored lock
  is final. Only locks are stored, not the rounds of an open contest; when two processes
  run the same open contest, the first lock written stands and the other adopts it.
- **Every process resolves the same plan:** each item is a deterministic function of the
  inputs, the stored models and the locks. The direct refine's window comes from a seeded
  simulation.
- **Results are bit-identical:** the same build on the same machine gives the same peaks.
  `tests/test_reproducible_choices.py` checks this.

**Without a cost file:**
- Each process measures afresh, so two processes can choose different chains or layouts on
  timing noise.
- Every plan they can resolve meets the false-dismissal budget, since the thresholds come
  from the model for whichever chain is chosen. Results are equivalent statistically, but
  pairs near a threshold can be refined in one process and not in another.

**Known caveat:**
- `chain_thresholds` reuses a cached result for a profile that agrees with an earlier one
  in shape (cosine) and in every band's signal response (`gatechain._similar_get`). A
  process's thresholds can therefore depend on which profiles it saw first.
- `_resolve` keys on the profile it is given. E6 added no persisted record of the resolved
  plan, since no divergence remained to need one; one would be the fix if a divergence
  appears.

## What is public

- `HierarchicalFilter.config` is the chain in use.
- `TimeDomainFilterBank.chosen_layout` is the bank layout.
- An explicit band (a pinned chain) with `set_coarse_threshold` replaces the model.
- `MF_CHAIN_FORCE` and `MF_COARSE_LAYOUT` force items for measurement.

Everything else in the record is private and may change.
