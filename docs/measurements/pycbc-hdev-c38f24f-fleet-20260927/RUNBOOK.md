# Reproduction and provenance

The timed new build was `c38f24f2b230ed7a5345f1aec3eb4e9097f57f02`.
Its nondefault-layout correctness fix is `33991f4` on `hdev`; the default
`MF_ILAY=1` timed code path is identical. The prior comparison build was
`5e56728785ea0f447edcf3a37a56f4d3263f4543`. All builds report the
same package version, `0.1.0a6`, so distinguish them by commit and binary
hash. The cp313 wheel SHA256 for timed `c38f24f` is
`7238918d980904105c163f813ef9aa0233d3f0a3e50ffc6f2dedfeb4a3ea0cde`.
Its native `_core` SHA256 is
`6f99a0040030d7f831f6b3af2f436a98ff4716eb194a30949094c15c12175f03`
on dev1–dev4 and
`4bf30f9bf3ee0e6a2c048854c69b30c4351cbdaa2eb1044b831bcbf2639`
on sugwg-login2 and Haswell. The source is a `git archive` plus Highway
submodule commit `2607d3b`.
The fixed cp311 wheel used for the 31-round no-regression check has
SHA256 `caedb143849a17390247b84da86750107db9db41275580088e839fc3b48edf4b`.
It is installed on Haswell under
`hosts/og-node-169/hdev-33991f4/target`.

The new package targets are
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/hdev-c38f24f/target`
on dev1/dev3/dev4/sugwg-login2,
`/home/ahnitz/projects/claude/searchdev/work/hdev-c38f24f-dev2/target`
on dev2, and
`/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/hdev-c38f24f/target`
on Haswell. The previous `hdev` and alpha6 target paths are in adjacent
handoff runbooks. CPU pinning was dev1/dev3/dev4/sugwg-login2 CPU0,
dev2 CPU2, and Haswell CPU3.

The existing `run-paired.sh` launcher runs the same five-segment,
5,883-template wider-bank PyCBC FIR search with FFTW, SNR threshold 5.5,
FDR 0.001, `PYCBC_RATIO_DEVICE=cpu`, upper-stage timing enabled, and
single-thread OpenMP/BLAS. `paired-A*.log` is alpha6 versus timed
`c38f24f`; `old-v-new/paired-A*.log` is `5e56728` versus `c38f24f`.
The first comparison has two pairs per host, and the direct Haswell
comparison four. Two additional reverse-order pairs (`B3 A3 A4 B4`, using
`run-reverse.sh`) were run on dev2, dev3, and dev4 to check drift.
Dev2's PyCBC source bin
must precede its virtualenv bin. On sugwg-login2 and Haswell set
`LD_LIBRARY_PATH=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/lib:${LD_LIBRARY_PATH:-}`
for FFTW discovery.

The per-run denominator is `4 * 5883 * 376 = 8,848,032`
template-seconds for steady segments 1–4, divided by lower plus upper
seconds. `analyze.py` reuses the adjacent alpha6 log parser and requires
all 68 groups in all five segments and five upper totals. Unpack the
archive and run:

```bash
mkdir -p /tmp/hdev-c38f24f-logs
tar -xzf docs/measurements/pycbc-hdev-c38f24f-fleet-20260927/logs.tar.gz -C /tmp/hdev-c38f24f-logs
python docs/measurements/pycbc-hdev-c38f24f-fleet-20260927/analyze.py /tmp/hdev-c38f24f-logs
```

The Haswell captured-workload fixture is
`hosts/og-node-169/capture/hier-00.npz` on that host. It was measured
with `tools/compare_captured_series.py` for 31 interleaved rounds on CPU3.
The diagnostic trace came from an isolated, instrumented build of the
corrected source and one captured call. It is evidence of path selection,
not a timed performance sample. The Haswell phase profile used
`PYCBC_RATIO_TIMING=1 PYCBC_RATIO_PHASE=1 MF_HMF_PROF=1` and is also
separate from the clean timing runs.
