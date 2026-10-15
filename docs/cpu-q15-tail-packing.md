# Q15 template-tail packing

This optimization starts from `b3c1b022`, after later-tier data preparation became
conditional on incoming survivors. It addresses unused lanes in the AVX-512
N256 Q15 screen. It does not alter quantization, thresholds, error margins,
floating-point rechecks, or final peak selection.

## Implementation

The ordinary kernel computes 32 templates for one data block. A partial final
template group still executes all 32 lanes. The new path handles an aligned
partial group with at most 24 active templates by combining independent data
blocks in those lanes:

| Active templates | Tile layout |
|---|---|
| 1–8 | Four blocks × eight template lanes |
| 9–16 | Two blocks × sixteen template lanes |
| 17–24 | A sixteen-template tile followed by an eight-template tile |
| 25–32 | Original one-block kernel |

Only complete groups of four data blocks enter this path. Leftover blocks,
calls with fewer than four blocks, and partial leading groups retain the
original kernel. Every block in a tile searches the same requested window.
Other transform sizes and CPU targets retain their existing path. Capability
is checked against the plan's retained backend, including after an ISA switch.

Templates keep their existing storage; there is no expanded temporary tile.
Each frequency's eight or sixteen template values are broadcast across the
vector, while masked broadcasts place each block's quantized data in its
assigned lanes. The generated product codelet changes only those loads. Pass
2, window clipping, squared maxima, and per-pair scale conversion use the
same operations as before. Existing scratch storage is reused.

Tail scheduling lives in a separate helper. Ordinary data preparation retains
its original position immediately before a block's first screen, and remains
inlined even though the tail helper adds another caller. This avoids changing
the fallback's preparation order or enlarging its scheduling loop.

The [padding estimate](cpu-work-avoidance.md#q15-tail-tiles-quantified-opportunity-not-a-measured-speedup)
predicted 5,056→4,800 vector transforms for one complete 32-block group in each
of the cap401 bank's 27 fine plans: 5.063% fewer transforms. That calculation
does not include packing overhead or the actual distribution of edge groups.

## Measurements

The [measurement artifacts](measurements/cpu-q15-tail-20261014/README.md) retain
raw paired samples, build/input hashes, configuration and reproduction commands.
The final native binary has SHA-256 prefix `b7fc2583ceea`. The host is a Ryzen
AI Max+ 395, pinned to CPU 4, with other agent CPU jobs idle. The representative
workload uses top 4 of the cap401 bank, 4,698 fine templates in 27 middle banks,
H1 reference profiles, N2048 and chain 256/512/1024. Q15, thresholds, real taps,
bins and input seed are fixed.

Four fresh processes ran in candidate/baseline/baseline/candidate order, with
24 segments per process and the first excluded as warmup. The table averages
the two processes per build:

| Stage | Baseline, ms/segment | Tail packing, ms/segment | Less time |
|---|---:|---:|---:|
| Q15 screen | 136.687 | 130.749 | 4.3% |
| Fine stage | 295.241 | 288.938 | 2.1% |
| Whole segment | 359.926 | 353.458 | 1.8% |

The two baseline fine-stage means were 295.025 and 295.457 ms; the final build's
were 288.908 and 288.968 ms. All four output hashes and stage counts match.
These are measurements of this workload on this host, not speed guarantees for
other hardware or template distributions. This is a seeded synthetic-input API
workload using a real bank and profiles, not a full PyCBC production job.

The kernel/series matrix covers eight template counts, groups 1/2/3/4/32,
two call types and AVX3/AVX2/SSE4: 240 cases, all with identical outputs. At group
32, the six targeted AVX3 tails improve direct-screen throughput by 1.107–1.204x
and synthetic series throughput by 1.039–1.065x. Complete and nearly complete
template groups serve as controls; those cases do not enter the new path.

AVX2 and SSE4 series medians over the matrix are 1.002x and 0.998x. Small-group
controls have several-percent variation between fresh processes. The three
AVX3 cases below 0.98x in the matrix reached 1.000–1.028x in a reversed-position
repeat, while other controls became slower. SSE4 at 162 templates/group 4 was
0.980x in the matrix, 0.979x in a reversed repeat, and 1.003x in another fresh
normal-order repeat; an identical-baseline control measured 0.999x. These controls
limit any claim of unchanged performance for each individual fallback shape.
No speedup is claimed for narrow ISAs, and no ARM or GPU performance was measured.

An earlier prototype gained AVX3 throughput but consistently slowed SSE4 series
by 1–4%, including aligned controls. It was rejected. Isolating the tail caller
and restoring inlined preparation in the ordinary loop removed that broad
shift. Its measurements remain separately labeled in the artifacts and are
not pooled with the final build.

## Correctness checks

[The regression harness](../tests/test_q15_tail_packing.py) compares grouped
calls with single-block calls through the unchanged kernel. It requires exact
pass masks, counts and float32 statistic bits, with guards around the output
arrays. It covers both balanced and pair-batched storage, all supported Q15
bands, every lane tail and rotating template offset, data groups 1–5 and 31–33,
full/clipped/single-lag windows and the broad `[20,236)` N256 window. Input
updates and zero scales exercise quantized-copy invalidation and pass handling.
Additional cases cover partially allocated final template groups and retained
plans across CPU-target changes, both before and after Q15 initialization.
Separate-process checks compare final hierarchical peaks and non-timing
counters against the frozen baseline, so both paths cannot agree merely because
they share a new error.

The final build matches all **143,360 grouped-screen comparisons and 288
hierarchical-output comparisons** across AVX3, AVX2 and SSE4. The
[exactness artifact](measurements/cpu-q15-tail-20261014/exactness-final.json)
records each configuration's baseline/final digest and the binary hashes.
The broader regression selection passes **317 tests per target**, with 63
platform/backend skips per target, including all 20 new tail tests with no skips. The documentation builder also
passes all 20 tests.

The source review also checked that reversing the generated tile-load
substitutions yields the existing product codelet exactly, and that extracting
the shared pass-2/max helper leaves its body unchanged. These checks establish
equivalence to the existing Q15 screen; they do not replace its documented
statistical error model with a new worst-case error guarantee.

## Reproduction

Save each build's `python` directory after compiling its native extension, and
use separate processes so a previously imported extension cannot contaminate
the comparison. The baseline and candidate must use the same target and inputs.

```sh
taskset -c 4 python tools/bench_q15_tails.py BASE/python CANDIDATE/python \
  --isas AVX3 AVX2 SSE4 --kinds screen series --rounds 7 --sample-ms 20 \
  --output tails.json

PYTHONPATH=CANDIDATE/python taskset -c 0 \
  python tests/test_q15_tail_packing.py --target AVX3 --output exact.json
```

The timing harness excludes setup and warm quantization, alternates immutable
workers, and verifies masks, statistics and final outputs outside the timer.
Its full and nearly full template groups, plus small data groups, are controls.
The representative ladder uses the real cap401 bank and H1 profiles with seeded
synthetic input; it is not a full PyCBC production-job timing.
