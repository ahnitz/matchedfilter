"""The calls a consumer's hooks make back into the library, per trigger: a follow-up
(PeaksContext.refilter, a bank's single-template filter_series), series reads, leaf-bank
lookups and filter spectra (get_filter_f). Each runs thousands of times a job, so each does
no work a repeat already did; the results are the same, to the bit, as the general path's."""
import numpy as np
import pytest

from conftest import usable_gpu, usable_gpu_reason
from matchedfilter import TimeDomainFilterBank, _batches
from matchedfilter import search as S
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
from matchedfilter.time_domain import _TemplateGroup

N = 1 << 15
VALID = (4096, N - 4096)
BAND = (60, N // 2 - 200)
LEAF = dict(engine="flat", binsize=512)


def _taps(rng, counts, cplx=False):
    taps = np.zeros((len(counts), max(counts)), np.complex64 if cplx else np.float32)
    for i, c in enumerate(counts):
        t = rng.standard_normal(c) + (1j * rng.standard_normal(c) if cplx else 0)
        taps[i, :c] = t / np.linalg.norm(t)
    return taps


def _search(rng):
    spec = lambda: (rng.standard_normal(N // 2 + 1)
                    + 1j * rng.standard_normal(N // 2 + 1)).astype(np.complex64)
    kids = [Inner(_taps(rng, [c])[0], children=[
        Leaf(_taps(rng, [101, 151, 201], cplx=True), [101, 151, 201], node_id=("leaf", i))],
        node_id=("inner", i)) for i, c in enumerate((301, 351))]
    root = Root(spec(), BAND, children=kids, node_id="root")
    inputs = {ch: BlockInput([spec()], [VALID], root_scale=lambda root, b: 1.0 / N, tags=[ch])
              for ch in ("A", "B")}
    return root, inputs, HierarchicalSearch([root], threshold=0.0, leaf_options=LEAF)


def _same(a, b):
    for f in a._fields:
        np.testing.assert_array_equal(getattr(a, f), getattr(b, f))


def test_a_filter_asked_for_twice_in_a_row_is_made_once(monkeypatch):
    """pycbc's power chisq asks for a trigger's filter (its correlation), then again (its
    template): the second is the first's spectrum, as a fresh array of its own."""
    rng = np.random.default_rng(3)
    bank = TimeDomainFilterBank(_taps(rng, [120, 200, 260]), tap_counts=[120, 200, 260])
    want = [np.conj(g.full_spectra(slice(t, t + 1))[0])
            for g, t in (bank._template_map[i] for i in range(3))]
    made = []
    full = _TemplateGroup.full_spectra
    monkeypatch.setattr(_TemplateGroup, "full_spectra",
                        lambda self, rows=None: made.append(rows) or full(self, rows))
    a = bank.get_filter_f(1)
    b = bank.get_filter_f(1)
    assert len(made) == 1
    assert a is not b
    np.testing.assert_array_equal(a, want[1])
    np.testing.assert_array_equal(b, want[1])
    a[:] = 0                                    # the caller's array is its own
    np.testing.assert_array_equal(bank.get_filter_f(1), want[1])
    np.testing.assert_array_equal(bank.get_filter_f(2), want[2])
    np.testing.assert_array_equal(bank.get_filter_f(0), want[0])
    assert len(made) == 3
    other = TimeDomainFilterBank(_taps(rng, [90, 300]), tap_counts=[90, 300])
    np.testing.assert_array_equal(other.get_filter_f(0),
                                  np.conj(other._template_map[0][0].full_spectra(slice(0, 1))[0]))


def test_a_follow_up_call_runs_as_a_batch_of_one_without_building_a_batch(monkeypatch):
    """A single-template call takes the batched follow-up path for its one job directly:
    the peaks of the batch with that one job, to the bit."""
    rng = np.random.default_rng(4)
    bank = TimeDomainFilterBank(_taps(rng, [150, 220, 300], cplx=True), tap_counts=[150, 220, 300],
                                engine="flat")
    x = rng.standard_normal(1 << 16).astype(np.float32)
    calls = [dict(windows=slice(9000, 60000), binsize=51, threshold=0.0, template_index=1),
             dict(windows=slice(0, 3000), binsize=64, threshold=2.0, template_index=2),
             dict(windows=slice(50000, None), binsize=None, threshold=None, template_index=0),
             dict(windows=slice(70000, 80000), binsize=51, threshold=0.0, template_index=1)]
    want = []
    for kw in calls:
        out = [None]
        assert _batches._cpu_single_td_batch([(bank, x, kw)], out) == {0}
        want.append(out[0])

    def no_batch(*a, **k):
        raise AssertionError("a single call built a batch")
    monkeypatch.setattr(_batches, "_cpu_single_td_batch", no_batch)
    for kw, w in zip(calls, want):
        _same(bank.filter_series(x, **kw), w)


def test_a_hook_settles_once_and_reads_a_slice_window_without_the_parser(monkeypatch):
    """A hook's series reads settle the search's inner rows at the first read only, and a
    follow-up's lone slice window is clipped as the parser would clip it: the same peaks as
    the same window given as a pair."""
    root, inputs, search = _search(np.random.default_rng(5))
    settles, hooks = [], []
    settle = HierarchicalSearch._settle
    monkeypatch.setattr(HierarchicalSearch, "_settle",
                        lambda self: settles.append(1) or settle(self))
    parse = S._normalize_windows

    def pairs_only(windows, n):
        assert not isinstance(windows, slice), "a slice window went through the parser"
        return parse(windows, n)
    monkeypatch.setattr(S, "_normalize_windows", pairs_only)

    def on_peaks(ctx):
        hooks.append(1)
        ctx.series("A")
        ctx.series("B", node=root)
        r = ctx.refilter("B", windows=slice(10000, 11000), binsize=64, threshold=0.0,
                         template_index=1)
        _same(r, ctx.refilter("B", windows=[(10000, 11000)], binsize=64, threshold=0.0,
                              template_index=1))
        assert len(ctx.refilter("B", windows=slice(11000, 10000), binsize=64, threshold=0.0,
                                template_index=1).snr) == 0
        with pytest.raises(ValueError, match="outside computed"):
            ctx.refilter("B", windows=slice(0, 1000), binsize=64, threshold=0.0,
                         template_index=1)
    search.run(inputs, on_peaks=on_peaks)
    assert len(hooks) == 2 and len(settles) == len(hooks)


def test_a_leaf_bank_handed_out_is_looked_up_once(monkeypatch):
    """Asked again for a leaf's bank in a channel (every hook call asks), the search hands
    back the bank it built, without resolving the channel's profile again."""
    root, inputs, search = _search(np.random.default_rng(6))
    leaf = root.children[0].children[0]
    bank = search.leaf_bank(root, leaf, "A")
    resolved = []
    which = HierarchicalSearch._channel_profile
    monkeypatch.setattr(HierarchicalSearch, "_channel_profile",
                        lambda self, r, c: resolved.append(c) or which(self, r, c))
    assert search.leaf_bank(root, leaf, "A") is bank
    assert search.leaf_bank(root, leaf, "A") is bank
    assert resolved == []
    assert search.leaf_bank(root, leaf, "B") is bank      # one bank, another channel: resolved
    assert resolved and set(resolved) == {"B"}


@pytest.mark.parametrize("window", [(0, 51000), (100, 900), (20000, 71000), (1, 1 << 17),
                                    (130000, 1 << 17), (60000, 60001)])
def test_a_gpu_banks_locked_cpu_follow_up_lays_out_no_window(monkeypatch, tmp_path, window):
    """A GPU bank's single-template call whose call shape is locked to the CPU runs there
    without laying its window out (for the play, then the device): the lock found from the
    window's bounds is the one for _window_layout's block count, and the peaks are the
    batched follow-up path's, to the bit."""
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    from matchedfilter import _choice, _settings
    from matchedfilter import time_domain as td
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.delenv("MF_SINGLE_DEVICE", raising=False)
    monkeypatch.delenv("MF_AUTOTUNE", raising=False)
    monkeypatch.setattr(_choice, "_CHOICES", {})
    rng = np.random.default_rng(8)
    counts = [300, 420, 515]
    df = 1.0 / 16
    f = np.arange(int(1024 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    bank = TimeDomainFilterBank(_taps(rng, counts, cplx=True), tap_counts=counts, engine="hier",
                                threshold=5.0, false_dismissal=1e-3, device=dev,
                                fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S_ = 1 << 17
    x = rng.standard_normal(S_).astype(np.float32)
    kw = dict(windows=slice(*window), binsize=51, threshold=0.0, template_index=2)
    g, _ = bank._template_map[2]
    W = np.array([window], np.int64)
    nblocks = TimeDomainFilterBank._window_layout(g, W, S_)[0].size
    td._single_choice(bank.device, g.n, nblocks).lock(_settings.arm("side", "cpu"))
    out = [None]
    assert _batches._cpu_single_td_batch([(bank, x, kw)], out, force_cpu=True) == {0}
    laid = []
    layout = TimeDomainFilterBank._window_layout
    monkeypatch.setattr(TimeDomainFilterBank, "_window_layout",
                        staticmethod(lambda g, W, S: laid.append(1) or layout(g, W, S)))
    _same(bank.filter_series(x, **kw), out[0])
    assert laid == []


def test_filter_spectra_keep_their_transform_per_block_length():
    """taps_to_spectra keeps a transform per block length: one-row calls (get_filter_f's,
    one per call) make none once their sizes have one, and give the rows of a call with
    every row, to the bit."""
    from matchedfilter import _core
    rng = np.random.default_rng(9)
    counts = np.array([90, 300, 517, 700], np.int64)
    m = int(counts.max())
    for cplx in (False, True):
        taps = _taps(rng, counts, cplx=cplx)
        full = {n: np.zeros((len(counts), n), np.complex64) for n in (1024, 2048)}
        for n, out in full.items():
            _core.taps_to_spectra(taps, counts, n, m, out, cplx)
        made = _core._t2s_plans()
        for _ in range(3):
            for t in range(len(counts)):
                for n in (1024, 2048):
                    one = np.zeros((1, n), np.complex64)
                    _core.taps_to_spectra(taps[t:t + 1], counts[t:t + 1], n, m, one, cplx)
                    np.testing.assert_array_equal(one[0], full[n][t])
        assert _core._t2s_plans() == made
