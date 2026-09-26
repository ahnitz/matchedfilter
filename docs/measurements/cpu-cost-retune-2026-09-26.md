# CPU cost retune, 2026-09-26

The CPU cost table used one FDR budget (`.001`) even though the model gate
changes the fraction of pairs that need full refinement at each budget. On
the n=4096, 16×1024-pair teaser workload at SNR 5.5, the old table chose
band 512 at all budgets. The retained retune at fd=.0001 measured 9.57 ms
for band 512 and 8.25 ms for band 1024. The table now measures FDR and pair count, using
the same `cost-fd-pairs-v1` format as the current GPU table. Costs only rank
bands; the profile gate model still computes accuracy independently.

`tools/regen/cost_cpu.py` timed warm public-API calls with distinct templates
on an AMD Ryzen AI MAX+ 395. Each band in a group saw the same fixed noise
batch, with timing order rotated and reversed across five blocks. The sweep
covered all nine previously shipped lengths (1024–262144), SNR 5, 5.5, 6
and 6.5, FDR .01, .001 and .0001, and four power-law reference profiles
(exponents −7/3, −2, −5/3 and −4/3). The base shape was 8×64 pairs;
n=4096 also used 16×1024 and the real PyCBC reference profile. Follow-up
measurements added 8×128 at n=8192 and 32768, plus exponents −1.5 and −1.45
at both batch sizes for those two lengths. The cost of each band is normalized to the widest band
measured on the same profile, SNR, FDR and shape. Taps are metadata because
execution uses the raw coarse maximum. Raw per-block timing, gates and
refinement fractions are in
[`cpu-cost-2026-09-26.json`](cpu-cost-2026-09-26.json).

Groups with a timing block spread above 25% were remeasured with
`--repair-outliers`; the final 696 groups (3456 band measurements) have no
block spread above 25%. On those measured workloads, the new table is over
5% faster than the old table in 377 cases, tied within 5% in 319, and over
5% slower in none. The geometric mean time ratio is 0.817 (new/old). This
is an in-sample score, not evidence of generalization.
The case-level score is in
[`cpu-cost-score-2026-09-26.json`](cpu-cost-score-2026-09-26.json).

An 8×128-pair, different-noise-seed holdout at n=4096, 8192, 16384 and
65536 has 24 cases. The new table is over 5% faster in 16, tied in eight,
and slower in none; the geometric mean ratio is 0.782. That holdout uses
the −5/3 profile, which was added to the calibration grid after its first
version revealed a 65K misranking. It tests shape and noise variation, not
unseen profile generalization. Its measurements and case-level score are in
[`cpu-cost-holdout-2026-09-26.json`](cpu-cost-holdout-2026-09-26.json) and
[`cpu-cost-holdout-score-2026-09-26.json`](cpu-cost-holdout-score-2026-09-26.json).

Two further 8×128 holdouts use new exponents and noise seeds. At −1.8 and
−1.5, 31 of 60 cases improve by over 5%, with none slower by over 5%
(geometric mean ratio 0.827). At −1.55 and −1.45, 15 of 24 improve by over
5% and one is 6% slower (geometric mean ratio 0.842). That one case is
n=32768, SNR 6, fd=.01, where bands 8192 and 16384 exchange rank across
noise realizations. Eight independent seeds split 4–4; their mean runtime
ratio (8192/16384) is 1.001. It is a near tie in expectation, not evidence
that a fixed wider-band override would improve the workload. The raw
holdouts, scores and seed check are retained beside this note as
`cpu-cost-fresh-holdout-*`, `cpu-cost-interp-holdout-*`, and
[`cpu-cost-seed-check-2026-09-26.json`](cpu-cost-seed-check-2026-09-26.json).

The new table chooses band 512 for the n=4096 teaser profile and 16×1024
pairs at fd=.01 and .001, then band 1024 at fd=.0001. This is the crossover
that the single-budget table missed. Unmeasured profiles, batch shapes and
CPUs can have different winners; `MF_COST` remains available for local
measurements.

To reproduce on an otherwise idle CPU:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/regen/cost_cpu.py --include-pycbc
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/regen/cost_cpu.py --sizes 8192,32768 --shape 8x128 --teaser-shape 8x128
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/regen/cost_cpu.py --sizes 8192,32768 --profiles=-1.5,-1.45 --shape 8x64 --teaser-shape 8x64
OPENBLAS_NUM_THREADS=1 PYTHONPATH=python python tools/regen/cost_cpu.py --sizes 8192,32768 --profiles=-1.5,-1.45 --shape 8x128 --teaser-shape 8x128
```

Run `--repair-outliers` with the same size, profile and shape arguments for
each subset to remeasure timing spreads above 25%. The previous CPU table
is in commit `e31e03a`; use `tools/score_cpu_cost_retune.py` with that file
as `--old` to reproduce the case-level comparisons.
