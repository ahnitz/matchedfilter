# Reproduction notes

The `hdev` branch head is `08519ef211c426e5e2e1c69f336153933252ac26`.
The local isolated cp313 wheel SHA256 is
`cbf6532a03a002db7aae685107bae607c9a007abc08027354d2d0cd75e26a731`.
Generated codelets were regenerated and hash-identical to the branch copy.
No source changes were made to `hdev` for these benchmarks.

The native `_core` SHA256 is
`661575788882dc1b0095542816a6f20a8d6706152ad51c3545ad5cc181daaff7`
on dev1–dev4 cp313,
`1adf54534a76150ecc5a012bb67a72ff876f1e5d138f8a265dd19a64ec05c0ff`
on sugwg-login2 cp311, and
`d1c0d7512f6aabb24900c79465d292170d1e4d14f790756fa9c1e5997dbc27bc`
on Haswell cp311.

The isolated `hdev` packages are at
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/hdev-08519ef/target`
on dev1/dev3/dev4/sugwg-login2,
`/home/ahnitz/projects/claude/searchdev/work/hdev-08519ef-dev2/target`
on dev2, and
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/hdev-08519ef/target`
on Haswell. Alpha6 target locations and the complete FIR command are in
the adjacent alpha6 [RUNBOOK](../pycbc-alpha6-fleet-20260927/RUNBOOK.md).

All clean runs set `PYCBC_RATIO_DEVICE=cpu`,
`PYCBC_RATIO_UPPER_TIMING=1`, `OMP_NUM_THREADS=1`,
`OPENBLAS_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`. CPU pinning was 0 for
dev1/dev3/dev4/sugwg-login2, 2 for dev2, and 3 for Haswell.
`PYCBC_RATIO_TIMING=1`, `PYCBC_RATIO_PHASE=1`, and `MF_HMF_PROF=1` were
added only to the separate `hdev-profile.log` run. On dev2, the source
`pycbc-work/apogee/bin` must precede the venv bin on `PATH`; the stale
venv launcher silently omits upper timing. The correct PyCBC source also
must lead `PYTHONPATH`.

The original host log layout is `/tmp/mf-hdev-fleet/HOST/` locally and
`hosts/hdev-08519ef/` in the benchmark directory on each host (Haswell:
`hosts/og-node-169/hdev-08519ef/`). The preserved archive mirrors the
local layout. Unpack it and run:

```bash
python docs/measurements/pycbc-hdev-fleet-20260927/analyze.py /path/to/unpacked/fleet
```

This regenerates `results.json` and `chart.svg` with only the Python
standard library. `analyze.py` reuses the adjacent alpha6 log parser.
Every clean log is checked for all 68 groups in all five segments and all
five upper totals before computing a rate. A/B repetitions are matched by
their numeric suffix. The actual execution was interleaved (A/B/B/A or
A/B/B/A/A/B/B/A); suffix pairing is for spread visualization, while the
reported speedup is mean A wall time divided by mean B wall time.

The Haswell fixture is `hosts/og-node-169/capture/hier-00.npz` on the
remote machine. Its 31-round interleaved diagnostic used
`tools/compare_captured_series.py` and compared exact output arrays.
The target is reachable through `su2` at `10.5.201.169`.
