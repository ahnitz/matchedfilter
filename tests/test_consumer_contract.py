"""The calls pycbc_inspiral_fir makes, as it makes them (pycbc-work/apogee, b4a5fa24d).

No pycbc dependency: each call below copies the consumer's names, keyword arguments and
shapes, citing where it makes them, so a rename or a changed field fails here and not in
a production search. The numbers each call returns are tested elsewhere (the search
against filters composed by hand in test_hierarchical_search, the bank against the flat
filter); this file pins only the interface.
"""
import numpy as np
import pytest

# pycbc/filter/matched_filter_ratio.py:12-14 and pycbc/vetoes/chisq_fir.py:17
import matchedfilter as _mf
from matchedfilter import search as mf_search
from matchedfilter.time_domain import reference_profile

from conftest import bank_subset
from test_hierarchical_search import BAND, N, VALID, _spec

RATE = 2048
IFOS = ("H1", "L1")


def _search(engine, rng, profile_band=None):
    """A search built as matched_filter_ratio.py:446-534 builds one, on real FIR taps."""
    b = bank_subset()
    taps, counts = b["fine_taps"][:24].astype(np.complex64), b["fine_counts"][:24]
    upper, upper_counts = b["upper_taps"][:2], b["upper_counts"][:2]
    inner = []
    for row in range(2):
        leaf = mf_search.Leaf(taps, counts, lags=np.arange(len(counts)) % 7, node_id=row)
        inner.append(mf_search.Inner(upper[row], count=int(upper_counts[row]), children=[leaf],
                                     node_id=row))
    top = _spec(rng)
    psd = np.ones(len(top))
    if profile_band is not None:                         # a degenerate PSD: a band of zeros
        psd[profile_band[0]:profile_band[1]] = 0.0
    delta_f = RATE / N
    profile = reference_profile(top, psd, 20.0, 900.0, delta_f)       # :495-501
    root = mf_search.Root(top, BAND, children=inner, profile=(profile, delta_f), node_id=11)
    search = mf_search.HierarchicalSearch(                            # :520-534
        [root], threshold=5.5,
        leaf_options=dict(tap_sample_rate=RATE, data_sample_rate=RATE, engine=engine,
                          false_dismissal=1e-3, first_stage_snr=4.0, coarse_band_hz=256.0,
                          device=None, binsize=512),
        context=300, min_pad=4096)
    return search, root


def _inputs(rng):
    """matched_filter_ratio.py:1021-1028: spectra, (start, stop) analysis ranges, a root
    scale callable(root, segment) and one tag per segment."""
    return {ifo: mf_search.BlockInput([_spec(rng) for _ in range(2)], [VALID] * 2,
                                      lambda _root, s: 1.0 / N,
                                      tags=["%s-%d" % (ifo, s) for s in range(2)])
            for ifo in IFOS}


@pytest.mark.parametrize("engine", ["hier", "flat"])
def test_the_search_pycbc_runs(engine):
    rng = np.random.default_rng(3)
    search, root = _search(engine, rng)
    assert isinstance(search.pad(root), int) and search.pad(root) >= 4096     # :539
    seen = {"series": [], "peaks": [], "chunks": []}

    def on_series(ctx):                                  # :641-660: an envelope per channel
        assert list(ctx.channels) == list(IFOS)
        for ifo in ctx.channels:
            assert ctx.tags[ifo].startswith(ifo)
            assert isinstance(ctx.series[ifo], np.ndarray) and ctx.series[ifo].ndim == 1
        seen["series"].append(ctx.chunk)
        return {ifo: (lambda t: np.ones(np.shape(t))) for ifo in ctx.channels}

    def on_peaks(ctx):                                   # :662-700 and :904-905
        for ifo, res in ctx.peaks.items():
            assert res.template_indices.dtype.kind in "iu" and res.sample_indices.dtype.kind in "iu"
            assert len(res.template_indices) == len(res.sample_indices) == len(res.snr)
            assert np.iscomplexobj(res.snr)
            e = ctx.envelope(ifo)                        # :670-671: values at the peaks
            assert e is not None and len(e) == len(res.snr)
            np.testing.assert_array_equal(e, 1.0)        # on_series' envelope, evaluated
            again = ctx.refilter(ifo, windows=slice(10000, 11000), binsize=64, threshold=0.0,
                                 template_index=0)
            assert len(again.snr) > 0
            seen["peaks"].append((ctx.leaf.node_id, ctx.chunk, ifo, ctx.tags[ifo], len(res.snr)))

    def on_chunk(ctx):                                   # :964-990
        seen["chunks"].append((ctx.chunk, list(ctx.channels), ctx.tags[ctx.channels[0]]))

    search.run(_inputs(rng), windows=lambda leaf, s_num, ifo, extra: None,     # :614-638
               on_series=on_series, on_peaks=on_peaks, on_chunk=on_chunk)
    assert seen["series"] == [0, 1]
    assert seen["chunks"] == [(0, list(IFOS), "H1-0"), (1, list(IFOS), "H1-1")]
    assert {(leaf, chunk, ifo) for leaf, chunk, ifo, _, _ in seen["peaks"]} == {
        (leaf, chunk, ifo) for leaf in (0, 1) for chunk in (0, 1) for ifo in IFOS}
    assert all(n > 0 for *_, n in seen["peaks"])
    assert {"root", "inner", "leaf", "setup"} <= set(search.timings)           # :1036-1040


def test_a_degenerate_reference_still_runs():
    """A segment whose PSD is zero over a band (a notched line) gives a reference profile
    with a band of zeros; the search must run on it."""
    rng = np.random.default_rng(4)
    search, root = _search("hier", rng, profile_band=(4000, 6000))
    got = []
    search.run(_inputs(rng), on_peaks=lambda ctx: got.extend(
        np.abs(r.snr).max() for r in ctx.peaks.values() if len(r.snr)))
    assert got and np.all(np.isfinite(got))


def test_the_chisq_bank_calls():
    """pycbc/vetoes/chisq_fir.py:61-141: valid ranges and block spectra of real taps."""
    b = bank_subset()
    taps, counts = b["fine_taps"][:8], b["fine_counts"][:8]
    rates = dict(tap_sample_rate=RATE, data_sample_rate=RATE)
    n = 4096
    valid = _mf.template_valid(np.asarray(counts, dtype=np.int64), n, **rates)
    assert valid.shape == (8, 2) and np.all(valid[:, 0] < valid[:, 1])
    spectra, _ = _mf.template_spectra(taps, counts, n, **rates)
    assert spectra.shape[0] == 8 and np.iscomplexobj(spectra)
    m = int(counts.max())
    spec, _ = _mf.template_spectra(taps[:3, :m], counts[:3], int(n))          # :141
    np.testing.assert_array_equal(spec, spectra[:3])
