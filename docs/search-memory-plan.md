# Hierarchical search: memory and interface plan

Status (2026-10-17): B done (7ceff4e2). A built, measured and dropped (below). C open.
Originally: plan, 2026-10-17, for review before any code. Three library changes, each
measured first, each validated against the code it replaces before the next.

Baseline (100k complex bank, 2048 s, two detectors, dev2, one core, branch
`hier-search` 09e5dcb3): steady 12.7 M templates in real time; peak RSS 1.71 GB.
Per top: fine banks ~95 KB a template (~430 MB at 4.5k templates), middle
buffers 2 x 160 MB, the top series 2 x 4 MB.

Rules for all three:
- **Exactness.** Each change keeps every computed value: triggers compared as sets
  with SNR to float rounding (and bit-identical peaks where the arithmetic is
  unchanged, which is stated per item), on dev2 and dev1, with and without
  injections.
- **No performance loss.** Paired, interleaved runs against the previous commit,
  reported as the standard stage table (notes/stage_breakdown.py).
- **One path.** No switch keeps the old behaviour; each backend either takes the
  new path or the change says why it does not apply there.

## A. Middle rows streamed from held block spectra

**Measured basis.** A search holds, per detector, every middle row of the top for
the whole segment: 20 packed rows x 2^20 samples x 8 B = 160 MB. The fine stage
reads one group's middle series at a time. The middle stage's forward transform
of each top-series block is shared by all rows in a call: ~13.5 us of a
~27.8 us single-row block at n = 16384, so computing rows in separate calls
would cost ~+19% in the middle stage. A cache-warm middle series does not speed
the fine search (140 vs 148 ms, noise), so this is a memory change, not a speed
change.

**Design.**
- C: split `ap_mf_correlate_series_continuous(_real)` into its two halves:
  `ap_mf_ingest_series(p, series, nseries, starts, nblocks, real)`, the block
  forward transforms into the plan's data slots (as `series_spectra` does now, for
  up to `p->nd` blocks), and `ap_mf_correlate_ingested(p, starts, nblocks, lo, hi,
  t0, nt, out)`, the per-row product, inverse and copy-out over those slots. The
  existing call becomes ingest + correlate per slot group: one code path.
- Python: `CorrelationFilter.ingest_series(series, starts)` and
  `correlate_ingested(starts, t0, nt, out)`. The search builds each inner batch's
  plans with as many data slots as the segment has blocks (74 at n = 16384, 39 at
  32768: ~10 MB a plan a detector, the held spectra).
- Search: per chunk and channel, ingest once per plan; then run the inner rows in
  batches of k packed rows, and the leaf groups below each batch, before the next
  batch reuses the row buffers. k comes from a new `memory_budget` (bytes) on
  `HierarchicalSearch`, the first thing that parameter controls. Nested inner
  levels stream the same way, level by level.

**Exactness.** Every output sample is the same arithmetic on the same spectra
and templates: bit-identical middle series and peaks expected. The order of
`on_peaks` calls follows row batches; leaf groups below one batch keep tree
order, and rows are already in tree order for pycbc's banks (both sorted by tap
count), so the call order should not change for them.

**Backends.** CPU engine path: as above. The macOS platform-FFT path is not taken
for real series (the middle stage's case), so it is unaffected. A GPU inner plan
(not used by pycbc today) keeps today's call per batch: correct, with the forward
repeated per batch, until the device path has its own held spectra (phase 3).

**Risks.** The zero-fill guarantee (a row reads as if fresh outside what it
computes) must hold for row slots that now hold different filters in turn; the
existing buffer tests cover reuse across chunks, and get a reuse-across-batches
case. Data slots grow with segment length: 2^20 samples is ~10 MB per plan;
longer blocks bound k instead.

**Validation.** Unit: ingest + correlate equals the existing call bit for bit at
several k, block sizes, windows; streamed search equals unstreamed (identical
peaks and series over every span hooks read). End to end: identical triggers
(dev2, dev1, injections), stage table, peak RSS. **Expected:** about -280 MB peak
RSS on this job, no throughput change.

## B. No unscaled tier copies (`ct0`) in the hierarchical plan

**Measured basis.** Each tier keeps an unscaled copy of every template's band
(`tr->ct0`), 8 B x (sum of tier bands) a template: 14 KB at chain
(256, 512, 1024), ~60 MB a top. It exists for one event: a reference change after
templates are loaded, which rescales every tier template (`refresh_template`).
The Python plan already ignores a reference equal to the current one, so the
event is a genuine change of profile: rare.

**Design.** C: `ap_hmf_set_reference` records the new tier fractions and marks
loaded templates stale instead of rescaling them; running with stale templates is
an error. Python: `HierarchicalFilter.set_reference`, on a genuine change with
templates loaded, reloads them from the template source (or the held copy for a
plan without one). `ct0` and its allocation go; the per-template band fraction
(`fpow`, 4 B) stays.

**Exactness.** A reloaded template is scaled from the same spectrum by the same
factor as `refresh_template` computed: bit-identical tier templates. Peaks
unchanged.

**Backends.** GPU plans keep templates on the device and already re-upload on a
reference change (`_tdirty`); they do not use `ct0`. CPU only.

**Risks.** Any path that sets a reference on a loaded plan without going through
the Python wrapper would now fail loudly rather than rescale; the reference tests
(`tests/test_hier_reference.py`) get a case that checks the error and the reload.

**Validation.** Unit: reference change after load gives the same peaks as loading
after the reference; chain trials and block-size trials (which re-plan and
re-reference) unchanged; full suite and gate. **Expected:** ~-14 KB a fine
template (~-60 MB a top), no throughput change.

## C. Peaks with their envelope values; batched refilter (measured: low value)

**Envelope values.** The search evaluates the threshold envelope at every peak
(`e(t - lag)`) and drops those below `T e`; pycbc's hook then evaluates its
renormalisation at the same samples again for selection and records. Design:
`PeaksContext.envelope(channel)` gives the values the search used, aligned with
the peaks (None without an envelope), so a caller renormalises with them instead
of re-evaluating. Exactness: pycbc's SNR becomes `z / e` with `e = 1 / rf`
instead of `z * rf`: float rounding (~1e-7), stated and checked. Library-only
change; pycbc adopts it when we return to the pycbc side.

**Batched refilter.** Measured on the job: 1,780 single-template refilters (~10 s
windows) cost 0.58 s of the follow-up's 1.23 s, out of 52.5 s; the rest is
pycbc's own selection and records. A list-of-(template, window) primitive could
remove some of the per-call overhead on the CPU (well under 1% of the run) and
already exists on GPUs as `filter_series_many` of single-template calls. Not
planned now; revisit if a production configuration (30 s windows, 1000 bins)
shows the follow-up larger.

## Order

1. B (smallest surface, C only, independent).
2. A (C split, Python API, search streaming, `memory_budget`).
3. C, envelope values only.

Each lands on `hier-search` as its own commit, gated (suite, ladder checks)
before the next starts. Not covered here, next: the ~0.7 GB not returned between
tops (allocator or cache: diagnose first), and the audit of `MF_*` switches.

## Outcome of A (measured, dropped)

Built as planned (C ingest/correlate split, held spectra, row batches from a budget) and
bit-identical, but the "same work" did not hold for memory traffic: the held spectra (about
10 MB a block size a detector) are written once and read back per row batch, where the fused
path uses each block's spectrum for every row while it is in cache. Paired on dev2, identical
triggers throughout:

| middle rows held | steady | peak RSS |
|---|---|---|
| all (fused) | 12.68 / 12.70 M (baseline 12.66 / 12.69) | ~1.6 GB |
| 8 (128 MB) | 12.49 M (-1.5%) | 1.48 GB |
| 4 (64 MB) | 12.10 M (-4.5%) | 1.38 GB |
| 2 (32 MB) | 11.98 M (-5.5%) | 1.36 GB |

The budget also bounded only the middle rows, not the fine banks (the largest item), so it
was not a memory budget in the sense a user would read it. Dropped for its complexity. Kept
from the rewrite: the search's middle stage as a tree walk with exact slot clearing (a reused
slot clears what its last row wrote outside its new coverage), on the fused path.
