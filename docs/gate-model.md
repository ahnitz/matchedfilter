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
- **Persisted lock.** The winner is stored in MF_COST_FILE under `block-trial|<device>|<candidate
  set>`. A bank whose key is on file adopts it at its first reference with no trial, and only
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
- **Chain-trial locks are persisted too** (`chain-trial|n|snr|fd|tiers|device`, used only if the
  stored chain is on the plan's shortlist).

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
