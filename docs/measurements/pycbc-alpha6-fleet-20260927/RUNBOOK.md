# Handoff: PyCBC alpha-6 fleet benchmark

Read [README.md](README.md) for the result, chart, interpretation, and
measurement limits. `results.json` contains each of the three clean repeats
and the separate profile. `logs.tar.gz` contains the original text logs;
`analyze.py` regenerates the JSON and SVG. The benchmark is complete for the
six **CPU** environments requested. No code changes to matchedfilter or
PyCBC were needed for this measurement.

## Remote benchmark locations

| Host | SSH target | Benchmark directory | Pinned CPU | Alpha-6 import |
|---|---|---|---:|---|
| dev1 | `dev1` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/alpha6-fleet` | 0 | `target/` |
| dev2 | `dev2` | `/home/ahnitz/projects/claude/searchdev/work/alpha6-fleet-dev2` | 2 | `target313/` |
| dev3 | `gravity-dev3.syr.edu` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/alpha6-fleet` | 0 | `target/` |
| dev4 | `gravity-dev4.syr.edu` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/alpha6-fleet` | 0 | `target/` |
| sugwg-login2 | `su2` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/alpha6-fleet` | 0 | `target/` |
| Haswell | `ssh -J su2 ahnitz@10.5.201.169` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/alpha6-fleet` | 3 | `target/` |

SSH uses `/home/ahnitz/.ssh/config` on the originating workstation. The
Haswell host was reached through `su2`. Files and caches on Haswell should
stay under its existing `hosts/og-node-169` tree, as required by its
original handoff at
`/home/ahnitz/projects/claude/searchdev/benchmark-handoff/og-node-169/BASELINE.md`.

On dev1/dev3/dev4, a CPython 3.13 alpha-6 wheel was installed in `target/`
because system compilers or current setuptools were unavailable. On su2 and
Haswell, the alpha-6 source distribution was built into `target/`. Dev2's
working PyCBC virtualenv is Python 3.13; its compatible alpha-6 wheel is in
`target313/`. The alpha tag is `v0.1.0a6`, commit `c9f9d4d`. None of these
steps replaced the old installed package.

## Exact CPU workload

All hosts used `run_fir_search.sh` with:

```bash
--bank-file fir_three_level_spin_mchirp_wider.hdf \
--fft-backends fftw \
--ratio-filter-engine matchedfilter-hierarchical \
--ratio-filter-false-dismissal 0.001 \
--snr-threshold 5.5 \
--gps-end-time 1000002000 \
--output OUTPUT.hdf
```

`PYCBC_RATIO_DEVICE=cpu`, `PYCBC_RATIO_UPPER_TIMING=1`, and single-thread
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` were set for
all clean runs. `taskset -c` pinned the CPU listed above. The five-segment
search has 68 lower groups per segment. Only segments 1–4 enter the rate:
8,848,032 template-seconds divided by the sum of logged group batch times
and upper segment totals. The 3 clean logs per host are `clean-{1,2,3}.log`
except dev2, whose correct logs are `source-clean-{1,2,3}.log`.

The separate native profile sets `PYCBC_RATIO_TIMING=1`,
`PYCBC_RATIO_PHASE=1`, and `MF_HMF_PROF=1`. It is `native-phase.log` in each
host's benchmark directory except dev2's `source-native-phase.log`. These
counters add overhead; the clean repeats determine performance. Native
`[prof]` lines report cumulative cycles per pair. `analyze.py` differences
segments 0 and 4 for each group and weights by the logged pair counts to
estimate coarse, gate, refine, and fill shares.

On dev2, `PATH` must put
`/home/ahnitz/projects/claude/searchdev/pycbc-work/apogee/bin` **before**
`pycbc-work/venv-apogee/bin`, and `PYTHONPATH` must put the alpha target and
the `pycbc-work/apogee` source first. The virtualenv's stale launcher accepts
the filter flags but omits upper-stage timing, so it yields a misleadingly
high reported rate. The other hosts use the copied PyCBC tree at
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/src/apogee` with the
project virtualenv first on `PATH`.

The original Haswell baseline is in that handoff file.
All six new searches have 4,386 identical trigger template hashes/end times.
The new Haswell file matches its original `results/triggers-pinned-1.hdf` in
those fields and in SNR values. The dev2 corrected launcher matches those
trigger identities; its maximum SNR difference is `2.38418579e-6`.

## Suggested next measurement

Measure `PYCBC_RATIO_DEVICE=gpu` on dev2, dev3, and dev4 in separate runs.
The alpha discovers Radeon 8060S, Radeon Renoir, and Iris Xe respectively.
Do not combine GPU timing with this CPU table: PyCBC processes individual
filter blocks and will incur upload, submission, and synchronization costs
that differ from the library's batched GPU microbenchmarks. Preserve the
trigger identity check and record the same lower/upper timing breakdown.
If a complete GPU search is too costly, report the maximum completed steady
segment and a comparable per-group sample rather than extrapolating a full
search rate without evidence.
