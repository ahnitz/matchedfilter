# Reproduce the PyCBC fleet comparison

Start with [README.md](README.md) for the result table, the two throughput
plots, the lower/upper cost plot, correctness, and interpretation. This
directory is a portable handoff: `logs.tar.gz` is the source data;
`analyze.py` and `log_parser.py` generate `results.json` and all three SVGs.
Python's standard library is enough to reproduce the numbers and charts.

## Rebuild the published table and figures offline

Run from the repository root:

```bash
folder=docs/measurements/pycbc-hdev-c38f24f-fleet-20260927
mkdir -p /tmp/pycbc-hdev-c38f24f-logs
tar -xzf "$folder/logs.tar.gz" -C /tmp/pycbc-hdev-c38f24f-logs
python "$folder/analyze.py" /tmp/pycbc-hdev-c38f24f-logs
git diff -- "$folder/results.json" "$folder/chart.svg" \
  "$folder/alpha6-chart.svg" "$folder/cost-breakdown.svg"
```

The final `git diff` should be empty. The analyzer rejects incomplete
five-segment searches: each log needs 68 groups in each segment and all five
upper-stage totals. `results.json` keeps every parsed run and the lower and
upper times; the table uses the mean of each interleaved build's loop times,
then divides `4 × 5,883 × 376 = 8,848,032` template-seconds by that mean.
The whiskers on the throughput charts are the ranges of paired A/B ratios.
They are not confidence intervals. Host-to-host rates are descriptive, not
a pooled benchmark; dev2's startup drift especially matters.

## Repeat the search on a host

The exact invocation is in `run-paired.sh`. It runs the five-segment wider
bank with FFTW, hierarchical ratio filter, FDR 0.001, SNR threshold 5.5,
CPU device, upper-stage timing, one OpenMP/BLAS thread, and a pinned CPU.
The positional arguments are `base output A_target B_target cpu pycbc_source
venv source_first rounds`. `base` contains `run_fir_search.sh` and
`fir_three_level_spin_mchirp_wider.hdf`; `pycbc_source` is the PyCBC source
tree whose `bin/` contains the working launcher. Set `source_first=yes` on
dev2: its virtualenv launcher is stale and silently omits upper timing.

| Archive name | SSH | CPU | A=alpha6 target | A=prior hdev target | B=timed new target |
|---|---|---:|---|---|---|
| dev1 | `dev1` | 0 | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/alpha6-fleet/target` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/hdev-5e56728/target` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/hdev-c38f24f/target` |
| dev2 | `dev2` | 2 | `/home/ahnitz/projects/claude/searchdev/work/alpha6-fleet-dev2/target313` | `/home/ahnitz/projects/claude/searchdev/work/hdev-5e56728-dev2/target` | `/home/ahnitz/projects/claude/searchdev/work/hdev-c38f24f-dev2/target` |
| dev3 | `gravity-dev3.syr.edu` | 0 | same as dev1 | same as dev1 | same as dev1 |
| dev4 | `gravity-dev4.syr.edu` | 0 | same as dev1 | same as dev1 | same as dev1 |
| su2 | `su2` | 0 | same as dev1 | same as dev1 | same as dev1 |
| haswell | `ssh -J su2 ahnitz@10.5.201.169` | 3 | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/alpha6-fleet/target` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/hdev-5e56728/target` | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/hdev-c38f24f/target` |

For dev1, dev3, dev4, su2, and Haswell, `pycbc_source` is
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/src/apogee` and `base`
is its fleet benchmark host directory containing the bank and launcher.
For dev2, `pycbc_source` is
`/home/ahnitz/projects/claude/searchdev/pycbc-work/apogee` and `venv` is
`/home/ahnitz/projects/claude/searchdev/pycbc-work/venv-apogee`. Check
`base`, `venv`, and both target directories exist before timing; the
original remote tree may have changed. On su2 and Haswell, add
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/lib` to `LD_LIBRARY_PATH`
to resolve FFTW. Preserve the existing output and use a fresh directory.

Copy the two launcher scripts to the host, or invoke their contents there.
For example, from a shell on dev2 (with the scripts in the current directory):

```bash
root=/home/ahnitz/projects/claude/searchdev
base=$root/work/alpha6-fleet-dev2
pycbc=$root/pycbc-work/apogee
venv=$root/pycbc-work/venv-apogee
alpha=$root/work/alpha6-fleet-dev2/target313
old=$root/work/hdev-5e56728-dev2/target
new=$root/work/hdev-c38f24f-dev2/target
bash run-paired.sh "$base" "$base/recheck-alpha" "$alpha" "$new" 2 "$pycbc" "$venv" yes 2
bash run-paired.sh "$base" "$base/recheck-old" "$old" "$new" 2 "$pycbc" "$venv" yes 2
bash run-reverse.sh "$base" "$base/recheck-old" "$old" "$new" 2 "$pycbc" "$venv" yes 2
```

`run-paired.sh` orders runs `A1 B1 A2 B2`. `run-reverse.sh` appends
`B3 A3 A4 B4`, so an order or warmup effect becomes visible. In the
archive, top-level `paired-A/B` means alpha6/new and `old-v-new/paired-A/B`
means prior hdev/new. For a new candidate, use isolated install targets,
record the exact Git SHA and binary SHA256, and keep the same bank, PyCBC
source, CPU pin, environment, and run order. Check `PYTHONPATH` imports the
intended target before timing. Do not time an instrumented path trace or
native phase profile as if it were a clean run.

## Validate before interpreting a speedup

Each A/B representative HDF pair is in `logs.tar.gz`. The expected result
is 4,386 identical sorted `(template_hash, end_time)` identities for every
host; the maximum absolute SNR difference by host is in `validation.json`
(overall maximum `2.384185791015625e-6`). A new benchmark should repeat
that check and the package's full test suite on the exact candidate source.
The original `c38f24f` fails two `MF_ILAY=0` cases. The corrected `hdev`
head `33991f4` passes 689 tests with 330 skips; its default timed path is
identical. This distinction is essential when deciding whether to merge.

Haswell's diagnostic trace in the archive identifies the actual path:
`stageA_prod_32 W=8 N1=32 N2=32 fuse=2 ilay=1 bblk=1 precomputed=1` and
`binmax_fused32 ... full_window=0`. Thus the new twiddles execute, but the
new full-window scan shortcut does not execute for the captured PyCBC
window. The separate `haswell/hdev-profile.log` reports 21.425 s lower,
3.651 s upper, and 20.886 s inside the lower kernel; native counters put
89.1% of lower-kernel cycles in coarse work. Instrumentation adds overhead,
so use these values to locate cost, and use the paired clean runs to decide
whether the candidate is faster.

For build identities, wheel hashes, fixture procedure, and remote path
details, see [RUNBOOK.md](RUNBOOK.md). The 31-round captured Haswell result
is in `haswell/fixture-old-v-new.json` inside the archive: new/prior
`0.988×`, six wins. A 31-round corrected/unfixed check is in
`haswell/fixture-fix-vs-unfixed.json`: `1.001×`, 16 wins.
