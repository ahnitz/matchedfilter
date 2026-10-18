# Hierarchical search: design

Status: phase 1 implemented (python/matchedfilter/search.py, root stage in C:
ap_root_real), 2026-10-17. Phases 2 and 3 are proposals.

## Why

Today matchedfilter is entered in the middle of the hierarchy. pycbc owns
the top (root) filter, the segment loop, the middle stage's packing and
buffer reuse, and calls the library once per middle group per segment per
detector. Measured on the 100k complex bank (dev2, one core) the top and
middle stages are 3% and 10% of steady time, and the code that drives them
in pycbc is where the last two correctness bugs were (the FFTW
input-destroying c2r, a buffer-reuse assumption; the reference-plan
wrapper costing 0.7 ms per call). The segments themselves are overlap-save
done by hand: each is one 2^20-sample transform block of which 376 s of
512 s is valid.

The proposal is one library object that runs the whole hierarchy over the
input: pycbc describes the hierarchy and the data and supplies hooks; the
library chooses blocks, chunks, order, batching and device placement. The
library stays unit-agnostic: samples, bins, scales and spectra on the
caller's grid; never Hz, PSDs or detectors.

## The model

**Hierarchy.** A forest of trees. Each node is a filter whose output is a
series; a node's children filter that series. Any depth L >= 1.

- A **root** filter is a spectrum on the input blocks' frequency grid, with
  a band [k0, k1). Its output is real: the complex-to-real transform of the
  one-sided product, i.e. twice the real part.
- An **inner** node is an FIR filter (taps, count). Real taps on a real
  series give a real series; complex taps give a complex one.
- A **leaf group** is a bank of FIR templates (taps, counts, per-template
  lag) that is searched: the gated peak search, one peak per template per
  bin above the threshold. Each leaf group has one parent node.

Real-real-complex is one configuration (real root output, real inner taps,
complex leaf taps). Inner nodes that are siblings with real taps on a real
series are run as packed complex pairs (two real filters per complex
filter), which is the library's choice, not the caller's.

**Channels.** Independent input streams (detectors) filtered by the same
hierarchy. A node's results for one chunk are delivered for all channels
together, so a hook can relate them (the asym follow-up does).

**Input.** Per channel, either

- *blocks*: transformed input blocks, each a one-sided spectrum of length
  N/2 + 1 with its global start sample and its valid span (the caller did
  the forward transform and any per-block whitening; today's segments), or
- *a series*: one continuous, already conditioned series with its global
  start sample.

Each block carries an opaque caller tag (pycbc: the segment object), handed
back to hooks, and the root scale for each root node (or a callable giving
it), since the scale depends on the block's normalisation.

**Chunks.** The library walks the input in chunks. A chunk is the unit for
which every node's series are held in memory and the hooks run. Phase 1
uses one input block per chunk (today's behaviour); later phases size
chunks from the memory budget (see Phases).

**Threshold.** A scalar T, or a threshold envelope: T * e(t), where e is a
caller callable giving e at sample indices. The search is constructed with
`envelope_floor` = e_min > 0, the least value any envelope may take (default
1: envelopes only raise the threshold), and builds its leaf banks at
T * e_min; an envelope seen below its floor at a peak is an error. Envelopes
come from `on_series` on the root, per (chunk, channel); see Exactness.

**Windows.** Where leaf peaks are searched, per (leaf group, chunk,
channel): `windows(leaf, chunk, channel, extra)` returns None (the block's
valid span), a list of spans, or empty (the group is skipped in that chunk
and channel), widened by `extra` samples and clipped to the valid span. The
library asks with extra = 0 for the search and extra = `context` (samples
hooks may read or re-filter beyond the windows) for what the parent series
must hold; asking the caller to widen keeps windows that lie just outside
the valid span but within reach. A leaf's parent series is exact over those
widened windows plus the longest leaf block (`pad`); an inner series over its
children's spans plus their filters' tap reach. A node any channel needs in
a chunk is produced in every channel (zero where that channel's own windows
are empty), so a hook can read it in another channel.

**Hooks.** Three, all optional:

- `on_series(ctx)` when a node's output for a chunk is ready, for all
  channels. May return a threshold envelope per channel, applying to every
  leaf below that node in this chunk. pycbc uses it on the root to build
  the SNR renormalisation envelope from the root series.
- `on_peaks(ctx)` per leaf group per chunk, after the peak search, while
  the group's ancestors' series for the chunk are still held. pycbc runs
  its renormalisation, chisq, auto-chisq, asym follow-up and trigger
  recording here, unchanged.
- `on_chunk(ctx)` after every leaf of a chunk (pycbc logs the segment).

`ctx` gives: node id, chunk id, the channels' block tags, the peaks per
channel (template index, sample, complex SNR, block start, block length),
and an accessor:

- `ctx.series(channel, node=None)`: an ancestor's series (default: the
  leaf's parent) for this chunk (read only, valid over the required span),
  for chisq and auto-chisq.
- `ctx.envelope(channel)`: the threshold envelope's values at the peaks, as the
  search evaluated them (None without an envelope), so a hook renormalises with
  them rather than evaluating its envelope again.
- `ctx.refilter(channel, windows, binsize, threshold, template=None)`: run
  this leaf group's bank over its parent's series in other windows, bin
  size and threshold (the asym follow-up's threshold-0 scan of the other
  detector). An explicit threshold here ignores any envelope.

Phase 3 (device residency): a hook declares what it reads (`peaks`,
`series`, `refilter`), so a device backend copies back only that.

## API sketch

```python
from matchedfilter import search as mfs

tree = mfs.Root(top_spec, band=(k0, k1), profile=(w, delta_f), node_id=top_id,
                children=[mfs.Inner(mid_taps[i], count=mid_counts[i], node_id=mid_ids[i],
                                    children=[mfs.Leaf(fine_taps[i], fine_counts[i],
                                                       lags=fine_shifts[i], node_id=mid_ids[i])])
                          for i in range(n_mid)])

search = mfs.HierarchicalSearch(
    [tree], threshold=6.0, envelope_floor=1.0, context=margin,
    leaf_options=dict(engine="hier", false_dismissal=1e-3, binsize=2048, device="cpu"))

inputs = {ifo: mfs.BlockInput(spectra, valid_spans, root_scale=lambda root, b: ...,
                              tags=segments)
          for ifo in ifos}

search.run(inputs, windows=group_windows, on_series=..., on_peaks=..., on_chunk=...)
```

`profile` is the gate calibration's expected signal spectrum, as given to
`set_reference` today, per root node (pycbc: |h_top|^2 / S of the first
segment, which is what it passes now).

## Exactness of the threshold envelope

The leaf search reports, per template per bin, the bin's maximum |z| when
it reaches the threshold. Under an envelope a bin's peak is kept iff
|z(t_p)| >= T * e(t_p - lag), where t_p is the bin's raw peak sample and
lag the template's lag (pycbc evaluates its renormalisation at
t_p - shift). The library therefore:

1. runs the gated search, gates included, at the scalar T * e_min; and
2. keeps each reported peak iff |z(t_p)| >= T * e(t_p - lag).

Step 1 cannot dismiss a peak step 2 would keep: every kept peak has
|z| >= T * e_min, and the gates are calibrated for T * e_min. A bin's
maximum does not depend on the threshold, so step 2 decides exactly what a
per-sample threshold test at the raw peak decides. No kernel changes; every
backend is exact the same way. With e >= 1 everywhere (renormalisation that
only lowers SNRs, pycbc's default) e_min = 1 and the gates are today's.
When an envelope can boost (e < 1 somewhere), the gates are recalibrated at
the lower threshold: more work, never a missed peak.

What this does not define: the renormalised peak (the maximum of
|z|/e over a bin) can sit at a different sample than the raw peak. Today's
pycbc tests the raw peak; so does this. Since e varies over seconds and a
bin is short, the two agree except at the edge of a fast envelope change.

## Determinism

Results must not depend on the chunking or the memory budget. Two things
make that hold:

- Every block grid is anchored to global sample 0 of the channel, not to a
  chunk: the leaf bank already lays blocks at multiples of its step from
  the series start (`_window_layout`), so chunk starts are placed on that
  grid. Gating is statistical per block, so a moved block would move
  dismissals.
- Peak bins are anchored the same way.

Tests run the same input at several budgets and require identical output.

## How pycbc's current code maps

| pycbc today | new |
|---|---|
| `StrainSegments`, per-segment `stilde / psd` | unchanged; segments become `BlockInput` blocks |
| `make_reference_series`, `_reference_snr`, ref plans | library root node |
| `ref_template.sigmasq(psd)`, scale | `root_scale(root, block)` from pycbc |
| `DynamicSNRRenormFactor` | built in `on_series(root)`, returned as the envelope (lower bound from `variance_floor` / `max_boost`) |
| `UpperReferenceBatch` (packing, buffers, dirty regions) | library inner nodes |
| `mid_windows`, `group_windows`, `kept` | `windows(group, chunk, channel)` and `context` |
| `group_engine.process_segment` | library leaf search |
| renorm at peaks, `select_primary_asym_candidates`, `process_and_record_triggers`, chisq, auto-chisq | `on_peaks`, unchanged code |
| `followup_asym_candidates` / `sample_asym_bins` | `on_peaks` with `ctx.refilter` and `ctx.series` |
| `set_reference_from_template(... profile ...)` | root `profile` |
| per-top task distribution (worker pool) | unchanged: one tree per task |

pycbc keeps conditioning, PSDs, normalisation, windows, vetoes, clustering
and output. The segment loop, the top FFT plans, `UpperReferenceBatch` and
the buffer bookkeeping are removed.

## Phases

1. **Same results, new owner.** One chunk per input block, each block's
   pads as today, root computed on the host for every backend (as today),
   leaf groups searched one after another. pycbc's per-top segment loop
   becomes one `run` per top. Gate: triggers identical to today's to float
   rounding on the 100k complex bank (dev1, dev2) and in an injection run;
   GPU runs with a forced chain against the flat engine; the stage table
   shows no regression.
2. **Stitching.** Inner and leaf series run continuously across block
   boundaries (each block's valid part of the root series, with its own
   scale), so pads are paid once per chunk rather than per block. Chunks
   sized from the memory budget. Changes results only near block edges,
   where an inner filter spans two blocks' normalisations: validated
   against the exact flat filter and injection recovery before adoption.
3. **Scheduling.** Leaf groups of a chunk batched (`filter_series_many`),
   several roots in flight within the budget, the root stage on the device
   so the whole chain stays resident.

## Next (planned 2026-10-17)

**Per-call leaf threshold from the envelope.** Today every leaf call gates at
T * envelope_floor, a bound for the whole run (pycbc: 1 / rf_max from the variance
floor and max boost). Instead, each leaf call runs at T * e_w, where e_w is the least
envelope value over the samples its peaks can be tested at: its windows shifted by its
templates' lag range (t - lag for every searched t and every lag), clipped to the
series. The banks stay calibrated at T * envelope_floor; a call's threshold is never
below it.

- Exact: a kept peak has |z| >= T * e(t - lag) >= T * e_w, so the call's gates and
  threshold cannot dismiss it; the per-peak test of the exactness section is unchanged.
- Cost: one minimum of the envelope per (leaf, chunk, channel) over the lag-widened
  windows; the envelope callable gains a range minimum (pycbc's block sums give it
  cheaply), or the search samples the envelope on the windows.
- Effect: with boosting envelopes (floor < 1) most windows gate far above the run's
  floor; with pycbc's default (floor 1, e >= 1) only loud stretches gain.
- Validation: identical peaks with and without, at floors 1 and 0.5, and the
  envelope tests; fine-stage time with a boosting envelope.

**Open from the 2026-10-17 comparison** (phase 1 against the pre-search code; the
cleanups changed none of them):
- fine stage about 1% slower on dev1 and dev2; cause not yet measured;
- chisq + follow-up about 10% slower (about 0.6% of steady time); cause not measured;
- cold start: a bank whose 4096 price lands within TIE of 2048 also prices 8192, an
  ~11 s calibration on dev1 for a size that does not win (gatechain.price_block_sizes).
- GPU (dev2, chain pinned): steady fine about 10-15% slower than the pre-search code
  (GPU rates vary about 15% run to run); cause not measured.

## Open questions

- Envelope callback cost: pycbc's envelope is cheap to build (about 1 ms
  per root chunk) and is read only at peaks; the library calls it once per
  kept-candidate batch, not per sample.
- Decimation between levels (tap rate != data rate) exists in pycbc's
  ratio engine but is 1 in every bank in use; phase 1 requires equal rates.
- The memory budget belongs to phase 2 (chunks of several blocks) and is not
  a parameter yet.
- Whether a GPU should compute the root (phase 3) or keep it on the host
  and stream the series; measured, not assumed.
