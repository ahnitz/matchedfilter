# Reproduction and provenance

The measured new head is `5e56728785ea0f447edcf3a37a56f4d3263f4543`;
old `hdev` is `08519ef211c426e5e2e1c69f336153933252ac26`.
The alpha6 build is the one in the adjacent
[alpha6 fleet runbook](../pycbc-alpha6-fleet-20260927/RUNBOOK.md).
All three packages report version `0.1.0a6`; the version string does not
identify the build. The new isolated cp313 wheel SHA256 is
`db2d4b908584e7ce107016573e93495e5e6ecc4e18dbf2e3aa67eac679803a68`.
Its native `_core` SHA256 is
`7f6b6df8ce188075d5b359ce90a3d1be485e5dca4b09fadcfc8f63781c50bec6`
on dev1–dev4 cp313 and
`96053d0f9bed94a031dbf0f5fd1e5f47aeef48c91516c600f6956e93e01831a9`
on sugwg-login2 and Haswell cp311. It was built from a `git archive`
of the pinned head plus the same Highway submodule commit `2607d3b`.

New isolated package targets:

| Host | New package target | Pinned CPU |
|---|---|---:|
| dev1/dev3/dev4/sugwg-login2 | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/hdev-5e56728/target` | 0 |
| dev2 | `/home/ahnitz/projects/claude/searchdev/work/hdev-5e56728-dev2/target` | 2 |
| Haswell | `/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/hdev-5e56728/target` | 3 |

The corresponding old `hdev` and alpha6 targets are in the preceding
`pycbc-hdev-fleet-20260927` and `pycbc-alpha6-fleet-20260927` runbooks.
`run-paired.sh` is the exact launcher used here. It runs the copied PyCBC
`run/run_fir_search.sh` on the five remote benchmark trees; on dev2 it
uses `work/smoke/run_fir_search.sh` and puts the PyCBC source `bin` before
the virtualenv `bin`. All clean runs set `PYCBC_RATIO_DEVICE=cpu`,
`PYCBC_RATIO_UPPER_TIMING=1`, and OpenMP/BLAS thread counts to 1.
The search uses FFTW, SNR threshold 5.5, FDR 0.001, five segments, and
the wider 5,883-template bank. On sugwg-login2 and Haswell, set
`LD_LIBRARY_PATH=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/lib:${LD_LIBRARY_PATH:-}`
before invoking the launcher, because their FFTW libraries live there.
Omitting this path fails at startup with "Backend fftw is not available."

The primary `paired-A*.log` files compare alpha6 (A) with new `hdev` (B).
The `old-v-new/paired-A*.log` files compare old `hdev` (A) with new `hdev`
(B). A/B runs were interleaved on each host, two pairs except four on
dev2 and the primary Haswell comparison. Only two direct old/new Haswell
pairs were needed to confirm its result. Each complete log must contain
all 68 lower groups in all five segments and five upper totals; the
adjacent alpha6 analyzer enforces this. The rate uses segments 1–4:
`4 * 5883 * 376 = 8,848,032` template-seconds divided by lower plus
upper seconds. The reported speedup is mean A loop time / mean B loop
time. The per-pair ratios show variability.

The representative A1/B1 HDF outputs were checked by sorting
`template_hash,end_time` and comparing identities and SNRs. The
Haswell fixture is the saved `hosts/og-node-169/capture/hier-00.npz`;
`tools/compare_captured_series.py` ran 31 interleaved rounds on CPU3.
Its JSON includes both `_core` hashes, exact output comparisons,
per-round wall and thread CPU times, and the fixture SHA256.

To regenerate the analysis from the archive:

```bash
mkdir -p /tmp/hdev-5e56728-logs
tar -xzf docs/measurements/pycbc-hdev-5e56728-fleet-20260927/logs.tar.gz -C /tmp/hdev-5e56728-logs
python docs/measurements/pycbc-hdev-5e56728-fleet-20260927/analyze.py /tmp/hdev-5e56728-logs
```

This regeneration requires only Python's standard library. The trigger
parity check requires NumPy and h5py and is recorded in `validation.json`.
