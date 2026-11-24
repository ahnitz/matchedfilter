# The hierarchical search

`matchedfilter.search.HierarchicalSearch` (`python/matchedfilter/search.py`) runs a tree
of filters over transformed input blocks and delivers peaks through hooks. The caller
describes the hierarchy and the data; the library chooses blocks, order, batching and
device placement. PyCBC's `pycbc_inspiral_fir` is its user.

The library stays unit-agnostic: samples, bins, scales and spectra on the caller's grid,
never Hz, noise spectra or detectors.

What is implemented is described first. [Not implemented](#not-implemented) lists the
parts of the design that are proposals.

## The model

**Hierarchy.** A forest of trees. Each node is a filter whose output is a series, and a
node's children filter that series.

- A **root** (`search.Root`) is a spectrum on the input blocks' frequency grid, with a band
  `[k0, k1)`. Its output is real: the complex-to-real transform of the one-sided product,
  which is twice the real part. The root stage runs in C on the host (`ap_root_real`).
- An **inner** node (`search.Inner`) is an FIR filter given as taps and a count. Real taps
  on a real series give a real series; complex taps give a complex one.
- A **leaf** (`search.Leaf`) is a bank of FIR templates (taps, counts and a lag per
  template) that is searched: one peak per template per bin above the threshold, through
  a `TimeDomainFilterBank`. Each leaf has one parent node.

A real root output with real inner taps and complex (quadrature) leaf taps is one
configuration. Sibling inner nodes with real taps on a real series run as packed complex
pairs, two real filters per complex filter. That is the library's choice, not the caller's.

**Channels.** Independent input streams (detectors) filtered by the same hierarchy. A
node's results for one chunk are delivered for all channels together, so a hook can relate
them.

**Input.** Per channel, a `search.BlockInput`: transformed blocks, each a one-sided
spectrum of n/2 + 1 bins with the span of its output that is searched, an opaque tag
handed back to hooks, and `root_scale(root, block)`, the root output's scale for that
block. The caller does the forward transform and any per-block whitening.

**Chunks.** The search walks the input in chunks, the unit for which every node's series
are held in memory and the hooks run. A chunk is one input block, filtered on its own with
its valid span padded by the filters' reach.

**Threshold.** A scalar T, or a threshold envelope T · e(t), where e is a callable giving
the scale at sample indices. The search is built with `envelope_floor`, the least value
any envelope may take (default 1: envelopes only raise the threshold), and calibrates its
leaf banks at T · `envelope_floor`. An envelope seen below its floor at a peak is an error.
Envelopes come from `on_series`, per chunk and channel.

**Windows.** `windows(leaf, chunk, channel, extra)` says where a leaf's peaks are searched:
`None` (the block's valid span), a list of spans, or empty (the leaf is skipped in that
chunk and channel), widened by `extra` samples and clipped to the valid span. The search
asks with `extra=0` for the peak search and with `extra=context` for what the parent
series must hold, where `context` is the number of samples hooks may read or refilter
beyond the windows. A leaf's parent series is exact over those widened windows plus the
leaf bank's longest block, and an inner series over its children's spans plus their
filters' reach. A node any channel needs in a chunk is produced in every channel, so a
hook can read it in another channel.

**Hooks.** Three, all optional:

- `on_series(SeriesContext)` runs when a root's output for a chunk is ready, for all
  channels. It may return a threshold envelope per channel, applied to every leaf below
  the root in this chunk.
- `on_peaks(PeaksContext)` runs per leaf per chunk, after the peak search, while the
  leaf's ancestors' series for the chunk are still held.
- `on_chunk(ChunkContext)` runs after every leaf of a chunk.

A `PeaksContext` gives the node, the chunk, the channels' block tags and the peaks per
channel (template index, sample, complex SNR, block start and block length), and:

- `series(channel, node=None, span=None)`: an ancestor's series for this chunk (default:
  the leaf's parent), read only and valid over the span the search holds;
  `support(channel, node=None)` lists the intervals that were computed.
- `envelope(channel)`: the threshold envelope's values at the peaks, as the search
  evaluated them (`None` without an envelope), so a hook does not evaluate its envelope
  again.
- `refilter(channel, windows, binsize, threshold, template_index=None)`: this leaf's bank
  over its parent's series with other windows, bin size and threshold, for example a
  threshold-0 scan of another channel. An explicit threshold here ignores any envelope.

## Building and running a search

```python
from matchedfilter import search as mfs

tree = mfs.Root(top_spec, (k0, k1), profile=(w, delta_f), node_id=top_id,
                children=[mfs.Inner(mid_taps[i], count=mid_counts[i], node_id=mid_ids[i],
                                    children=[mfs.Leaf(fine_taps[i], fine_counts[i],
                                                       lags=fine_shifts[i], node_id=mid_ids[i])])
                          for i in range(n_mid)])

search = mfs.HierarchicalSearch(
    [tree], threshold=6.0, envelope_floor=1.0, context=margin,
    leaf_options=dict(engine="hier", false_dismissal=1e-3, binsize=2048, device="cpu"))

inputs = {channel: mfs.BlockInput(spectra, valid_spans, root_scale=scale_of, tags=segments)
          for channel in channels}

search.run(inputs, windows=leaf_windows, on_series=..., on_peaks=..., on_chunk=...)
```

`profile` is the expected output-power spectrum the leaf gates are calibrated on, as
`TimeDomainFilterBank.set_reference` takes it, per root. Where the channels' noise spectra
differ, give one per channel, `profile={channel: (w[channel], delta_f)}`: every leaf's
bank then holds a calibration for each channel's profile over one copy of its templates.
`HierarchicalSearch.leaf_bank(root, leaf, channel)` returns a channel's bank.

A chunk's leaf searches run as one batch (`TimeDomainFilterBank.filter_series_many`), and
together with the inner correlations they read (`correlate_and_filter_many`).

## Exactness of the threshold envelope

The leaf search reports, per template per bin, the bin's largest |z| when it reaches the
threshold. Under an envelope a bin's peak is kept if and only if
|z(t_p)| ≥ T · e(t_p − lag), where t_p is the bin's raw peak sample and lag the template's
lag. The search therefore:

1. runs the gated search, gates included, at the scalar T · `envelope_floor`; and
2. keeps each reported peak if and only if |z(t_p)| ≥ T · e(t_p − lag).

Step 1 cannot dismiss a peak that step 2 would keep: every kept peak has
|z| ≥ T · `envelope_floor`, and the gates are calibrated for that threshold. A bin's
maximum does not depend on the threshold, so step 2 decides exactly what a per-sample
threshold test at the raw peak decides. No kernel is involved, so every backend is exact
in the same way. With e ≥ 1 everywhere the floor is 1 and the gates are those of a search
without an envelope. Where an envelope can lower the threshold (e < 1 somewhere), the
gates are calibrated at the lower threshold: more work, never a missed peak.

One thing this does not define: the largest |z|/e over a bin can sit at a different sample
than the raw peak. The search tests the raw peak. An envelope that varies over seconds is
nearly constant over a bin, so the two agree except at the edge of a fast change.

## Not implemented

These parts of the design are proposals.

- **Continuous series input.** A channel given as one conditioned series in place of
  transformed blocks.
- **Stitching.** Inner and leaf series run continuously across block boundaries, so the
  filters' pads are paid once per chunk and not once per block, with chunks sized from a
  memory budget. It would change results near block edges, where an inner filter spans
  two blocks' normalisations, so it needs validating against the flat filter and by
  injection recovery. Results must then not depend on the chunking: every block grid and
  every peak bin would be anchored to the channel's sample 0, since gating is statistical
  per block and a moved block moves dismissals.
- **Scheduling.** Several roots in flight within the budget, and the root stage on the
  device so that a whole chain stays resident there. Whether a GPU should compute the
  root or have the series streamed to it is to be measured.
- **Hooks that declare what they read** (`peaks`, `series`, `refilter`), so that a device
  backend copies back only that.
- **A per-call leaf threshold from the envelope.** Every leaf call gates at
  T · `envelope_floor`, a bound for the whole run. Each call could instead run at T · e_w,
  where e_w is the least envelope value over the samples its peaks can be tested at (its
  windows shifted by its templates' lag range). A kept peak has
  |z| ≥ T · e(t − lag) ≥ T · e_w, so the call's gates cannot dismiss it. The cost is one
  minimum of the envelope per leaf, chunk and channel. With envelopes that can lower the
  threshold most windows would gate far above the run's floor; with a floor of 1 only loud
  stretches gain.
- **Different rates between levels.** Tap and data rates are equal at every level.
