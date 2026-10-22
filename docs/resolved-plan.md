# The resolved plan

Before a hierarchical filter runs, it settles everything that decides which pairs are
refined. That settled set is the **resolved plan**. This note says what it holds, where it
is resolved today, what it guarantees with and without a shared cost file, and what of it
is public. It is the design that robustness-plan E6 (one `resolve()` per filter)
implements.

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

## Where it is resolved today

| Item | Where |
|---|---|
| chain | `_choose_chain`: model ranking, chain trial, a stored lock, `MF_CHAIN_FORCE` |
| thresholds | `_thresholds` (via `gatechain.chain_thresholds`) |
| Q15 | the Q15 trial (`_q15_trial`) |
| direct refine | `_execution_plan` (`_direct_halfwidth`) |
| GPU calibration | `_gpu_calibration` |
| bank layout | `time_domain` (block-size trial) |

These sites run lazily, are invalidated by separate flags (`_thr_applied`, `_gcal`), and
each re-reads the cost model. E6 replaces them with one `resolve()` that returns an
immutable record, invalidated by the setters that change an input: `set_reference`,
`set_first_stage`, `set_coarse_threshold`, `set_taps`, and a chain switch at a trial's end.

## What it guarantees

**With a shared `MF_COST_FILE`** (one writer per open contest):
- **Measurements are shared:** cost models are measured once and stored, and a stored lock
  is final.
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
- `chain_thresholds` reuses a cached result for a profile within its cosine-similarity
  tolerance of an earlier one. A process's thresholds can therefore depend on which
  profiles it saw first.
- `resolve()` keys on the profile it is given. If a divergence remains after that, a
  persisted record of the resolved plan is the fix (E6), not before.

## What is public

- `HierarchicalFilter.config` is the chain in use.
- `TimeDomainFilterBank.chosen_layout` is the bank layout.
- An explicit band (a pinned chain) with `set_coarse_threshold` replaces the model.
- `MF_CHAIN_FORCE` and `MF_COARSE_LAYOUT` force items for measurement.

Everything else in the record is private and may change.
