# Defer the Q15 float recheck until after the next gate

This change starts from `702e6af8`, after Q15 tail packing. It changes the order
of existing decisions, rather than the transform arithmetic or gate thresholds.
The representative Zen 5 ladder uses 3.5% less fine-stage time and 2.9% less
whole-segment time, with identical outputs.

## Why order matters

The logical chain remains `(256, 512, 1024)`. With Q15 enabled, ordinary execution
is Q15 → float256 → float512 → float1024 → refinement. When the scheduling model
selects delayed rechecking, execution is Q15 → float512 → float256 → float1024
→ refinement. Every surviving pair must still pass all the same gates.

The initial two-segment diagnostic evaluated float512 on every Q15 survivor
without changing normal filtering decisions. It observed 585,333 Q15 survivors,
395,899 float256 passes, 33,974 float512 passes and 31,825 passes of both float
gates. Thus only 5.8% of Q15 survivors needed the float256 check when it ran
second. Those counts include warmup; the final steady-run counts below are separate.
The diagnostic's final output hash matched the unchanged build.

This preserves the conjunction of the gate decisions. Reordering can change
which pairs are packed together, so exact numerical agreement is also tested.
The final 1024 gate remains last, preserving the coarse peak location used by
direct refinement. No new approximation, rejection threshold, Q15 margin,
false-dismissal allocation or public filtering argument is introduced.

## Selection and implementation

Automatic selection is limited to the measured AVX3 N2048 `(256,512,1024)` chain
with a reference profile. At plan configuration, existing noise simulations and
measured kernel costs price the two orders. Let `q` be the modelled Q15 pass
fraction, `f256` and `f512` the individual float-gate pass fractions, `c256` the
measured recheck cost and `c512(f)` the pooled 512 cost at density `f`:

```
ordinary = q * c256 + f256 * c512(f256)
delayed  = q * c512(q) + min(q, f512) * c256
```

The second expression uses an upper estimate of recheck work within the model:
the intersection cannot exceed either individual pass fraction. It does not
assume independence between Q15 and float512. The existing 5% tie margin must
favor delayed rechecking; missing cost coverage retains the ordinary order.
This Gaussian/profile model predicts scheduling cost, not arbitrary-data timing.

The choice is made when thresholds/reference configuration changes, not inside
the pair loop. Existing Q15 on/off trials still work: delayed rechecking has no
effect while Q15 is off, or when its recheck uses the FP16 gate. AVX2, SSE4,
other chains and other lengths retain automatic selection of the ordinary order.
The low-level native switch permits cross-ISA correctness tests.

A shared `run_gate_pairs` helper owns window mapping, lazy input preparation
and pooled execution for selected pairs. The new order compacts the existing
Q15 pair arrays in place; it needs no new per-pair allocation or template layout.
Logical gate identity is separate from the order in which the first two gates run.

## Counters

Each native gate now records its actual input count. `work_counts()['checked']`
uses these counts instead of inferring inputs from the preceding logical gate's
passes. `tier_stats` remains in logical band order; its pass counts describe
pairs actually evaluated and need not decrease in that order. A separate count
of passes from the first executed gate keeps the chain trial's usefulness check
meaningful. Q15, total-pair and final-refinement counts keep their existing roles.

Timing attribution also follows the executed gate. Some decision/compaction work
moves between gate timers and the forward/ingestion/bookkeeping remainder; the
whole fine stage and segment are the acceptance measurements.

## Representative results

Four fresh processes ran candidate/baseline/baseline/candidate, with 24 segments
each and the first excluded as warmup. The host is an AMD Ryzen AI Max+ 395,
pinned to CPU 4, with other test jobs stopped. The cap401 top-id-4 bank has
4,698 fine templates in 27 middle groups, matching H1 profiles, two detectors,
N2048, chain 256/512/1024, fixed thresholds and deterministic seed-1 input.
This is a real-bank API workload with synthetic input, not a full production job.

| Measurement | Baseline | Delayed recheck |
|---|---:|---:|
| Fine stage, ms/segment | 286.620 | 276.709 |
| Whole segment, ms | 350.702 | 340.601 |
| Q15 inputs/segment | 4,337,904 | 4,337,904 |
| float256 inputs/segment | 292,381 | 17,619 |
| float512 inputs/segment | 197,447 | 292,381 |
| float1024 inputs/segment | 16,515 | 16,515 |
| Final refinement inputs/segment | 916.87 | 916.87 |

The 256 recheck executes 94.0% fewer pairs. Float512 executes 48.1% more pairs;
the gain depends on paying for that extra work. Q15 time itself is unchanged.
All four final-output hashes agree. Fine-stage process means were 285.181 and
288.060 ms for baseline, 276.746 and 276.672 ms for the final implementation.
These measurements establish a gain for this workload, not every profile or CPU.

The 27 ordinary-order fallback controls had median speedups of 0.991x on AVX3,
1.000x on AVX2 and 1.001x on SSE4. Reversing build positions and repeating all nine
AVX3 controls gave a 0.998x median. The two original approximately 2% slow cases
were within 0.3% of parity in that repeat, while another case was 2.6% slower.
Individual small-shape measurements remain sensitive to fresh-process variation;
these data do not establish unchanged timing for every fallback shape.

## Validation and reproduction

The regression selection passed 385 tests per AVX3/AVX2/SSE4 target, with 65
platform/backend skips. The final gate-order suite passed 25 tests per target;
it extends the 10 cases included in the regression selection, for 400 distinct
passing cases per target. Additional calibration-contract/invariant checks passed.

Gate-order tests cover complex, real and strided-real input; reused data slots;
zero-padded tails; repeated and clipped windows; multiple bins; spectral data and
template subranges; input updates; rejecting/all-pass gates; Q15 on/off transitions;
last-gate direct refinement; actual-work counters; and configuration invalidation.
They require exact output arrays and the expected final gate intersection.

[Measurement artifacts and reproduction](measurements/cpu-gate-order-20261015/README.md)
retain the diagnostic patch, separate prototype results, final build identities,
input/output hashes and paired timing samples. The earlier prototype and final
selective implementation are not pooled. No GPU or ARM timing is claimed.
