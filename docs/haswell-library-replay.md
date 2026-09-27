# Haswell library-only replay, 2026-09-26

The og-node-169 capture now replays without PyCBC or NumPy FFTs. Both the
hierarchical and flat references use matchedfilter `run_series`, including its
native forward FFT. The standalone driver is `tools/bench_captured_series.py`;
a copy is installed in the host's benchmark directory. No production kernel
or shared remote installation was changed.

## Workload and checks

Host: two Xeon E5-2698 v3 CPUs, AVX2, pinned logical CPU 3. The remote source
baseline is reported as cef06a3cfe89a8ce06463273dd74e59125b8ea45. The final
report records the actual loaded native binary SHA-256 and module path.

The fixture is one real lower-stage call: n=4096, 236 blocks, 64 templates,
15,104 pairs, threshold 5.5, false-dismissal request 0.001, band=1024 and U=8.
It lives at
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/capture/hier-00.npz`.
Its SHA-256 is recorded in each report. The original capture records requested
band=0 (automatic), not its selected band. The old replay passed zero into
the constructor, causing the reported failure. This driver pins the configuration
observed in the full-search profile and uses the packaged calibration via the
captured reference. It does not introduce calibration fallback.

All runs reproduce all 28 captured peaks with identical indices and complex
values within rtol=atol=1e-5. The flat library reference also finds 28 peaks,
with no hierarchical misses. Every timed sample is checked for exact repeatability
against that plan's warm output, outside the timing interval. Setup and two
warmup calls are excluded. Raw outputs are copied before buffer reuse.

This is an optimization fixture, not a statistical certification of the 0.001
false-dismissal rate, nor a replacement for the full 68-group workload.
The capture does not store the resolved coarse threshold, so unchanged capture
outputs alone cannot prove future calibration-table selection is identical.

## Measurements

Raw reports are in `docs/audits/haswell-library-replay-2026-09-26/`.
Hierarchical and flat calls alternate order within each process.

| Uninstrumented run | Samples per path | Hierarchical median | Flat median |
|---|---:|---:|---:|
| 1 | 15 | 84.587 ms | 240.381 ms |
| 2 | 21 | 81.839 ms | 247.053 ms |
| 3 | 21 | 80.789 ms | 238.497 ms |

The final run is about 2.95x faster hierarchically, with hierarchical samples
79.891–81.626 ms. Thread CPU time closely tracks wall time in that run.
Earlier runs contain substantial slow intervals (hierarchical up to 126 ms,
flat up to 410 ms). The host is shared. Those earlier reports lack thread CPU
time, so their slowdown cannot be assigned conclusively to descheduling versus
frequency/cache contention. A future candidate needs interleaved baseline and
candidate runs, not comparison to a single number in this table.

The separate instrumented run reports native ticks/pair:

| Native region | Ticks/pair | Share of recorded native regions |
|---|---:|---:|
| Coarse transform/product/peak pass (`even`) | 12,597 | 92% |
| Refinement | 1,088 | 8% |
| Rejected-output fill | 27 | <1% |
| Recorded gate comparison | 1 | <1% |

337 of 15,104 pairs reach refinement per call (2.23%). These counters exclude
forward transforms, data preparation and some gate bookkeeping, including the
early-rejected comparison branch. They are not a complete end-to-end time
decomposition. Nevertheless, the coarse pass is the clear first target among
the measured native regions. `U=8` is recorded configuration, not evidence
that eight separate coarse passes execute.

## Full-search output cross-check

The three saved pinned runs and the profiled run all have exactly the same
sorted template-hash and end-time arrays as the unpinned baseline: 4,386 events.
Maximum SNR absolute difference is 2.3842e-6; maximum chi-square difference
is 9.9183e-5. The full outputs are not bitwise equal. In particular,
`psd_var_val` differs by up to 0.147672, and `sigmasq` by up to 3 in absolute
units. The cause and downstream significance of the PSD-variation differences
were not established in this library-only investigation. Preserve that caveat
when assessing full-pipeline equivalence. The comparison script and per-field
results are saved with the reports.

## Rerun on the host

```sh
P=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926
R=$P/hosts/og-node-169
export PYTHONPYCACHEPREFIX=$R/cache/pycache TMPDIR=$R/tmp
export XDG_CACHE_HOME=$R/cache LD_LIBRARY_PATH=$P/lib
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
taskset -c 3 "$P/venv/bin/python" "$R/bench_captured_series.py" \
  "$R/capture/hier-00.npz" --repeats 21 \
  --output "$R/results/library-next.json"
```

Add `--profile` in a separate process to obtain native phase counters on stderr.
The driver explicitly clears inherited `MF_HMF_PROF` for uninstrumented runs.
Use a candidate's Python environment/module path when comparing builds and check
the recorded native binary hash. Before accepting a production change, expand
coverage to other groups/tail batches and rerun the full search plus the standard
accuracy/calibration suite.
