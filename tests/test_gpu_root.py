"""The root stage of a hierarchical search on a GPU (_gpuroot): the device's transform
against the host's, what it keeps across runs and searches, and where a search computes its
roots."""
import gc

import numpy as np
import pytest

from matchedfilter import _core, _gpuroot
from matchedfilter.search import BlockInput, HierarchicalSearch, Inner, Leaf, Root
from matchedfilter.time_domain import _settle_device_writes

#: The shortest series the device root takes (its half-length transform is two-stage).
N = 1 << 18


def _has_gpu():
    import matchedfilter as mf
    try:
        return any(str(d) == "gpu:0" for d in mf.devices())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _has_gpu(), reason="needs a GPU")


def _spec(rng, n=N):
    h = n // 2 + 1
    return (rng.standard_normal(h) + 1j * rng.standard_normal(h)).astype(np.complex64)


def _device_root():
    from matchedfilter.device import parse
    dev = _gpuroot.device_root(parse("gpu:0"))
    if dev is None or dev.kernels(N) is None:
        pytest.skip("this GPU's backend runs no device root")
    return dev


def _host(D, T, band, scale, n=N):
    out = np.empty(n, np.float32)
    _core.Root(n).real(np.ascontiguousarray(D), T, band[0], band[1], scale, out)
    return out


def test_the_device_root_gives_the_host_root():
    """Every band edge the host's merge treats specially -- DC and Nyquist inside the band
    (their products taken real), a band from bin 1, a few bins -- and two channels of one
    chunk at their own scales, to float rounding of the host's series."""
    rng = np.random.default_rng(5)
    dev = _device_root()
    h = N // 2
    T = _spec(rng)
    dev.set_template(N, T)
    blocks = [_spec(rng), _spec(rng)]
    outs = [dev.take_output(N, c, 0) for c in range(2)]
    for band in ((0, h + 1), (1, h), (h // 3, h // 3 + 7), (17, h + 1)):
        scales = [0.37, 1.9]
        dev.run(N, 0, blocks, outs, band, scales)
        _settle_device_writes()
        for D, out, s in zip(blocks, outs, scales):
            ref = _host(D, T, band, s)
            np.testing.assert_allclose(out, ref, rtol=0, atol=2e-5 * np.abs(ref).max(),
                                       err_msg="band %s" % (band,))
    for c, out in enumerate(outs):
        dev.give_output(N, c, 0, out)


def test_a_block_is_uploaded_once_and_freed_with_its_array():
    """A chunk's second run uploads and records nothing; a new array (equal contents, a
    new object) is uploaded; a block whose array died is freed at the next run, with its
    recording."""
    rng = np.random.default_rng(6)
    dev = _device_root()
    h = N // 2
    dev.set_template(N, _spec(rng))
    a, b = _spec(rng), _spec(rng)
    out = [dev.take_output(N, c, 1) for c in range(2)]
    first = dev.run(N, 1, [a, b], out, (10, h - 10), [1.0, 1.0])
    assert first >= 1                       # a recording, and uploads of blocks it had not seen
    assert dev.run(N, 1, [a, b], out, (11, h - 11), [2.0, 0.5]) == 0
    blocks, records = len(dev._blocks), len(dev._records)
    c = a.copy()
    assert dev.run(N, 1, [c, b], out, (10, h - 10), [1.0, 1.0]) == 2   # c, and its recording
    assert (len(dev._blocks), len(dev._records)) == (blocks + 1, records + 1)
    del c
    gc.collect()
    dev.run(N, 1, [a, b], out, (10, h - 10), [1.0, 1.0])
    assert (len(dev._blocks), len(dev._records)) == (blocks, records)
    _settle_device_writes()
    for i, o in enumerate(out):
        dev.give_output(N, i, 1, o)


def test_a_block_rewritten_in_place_is_uploaded_again():
    """A caller that writes new data into an array a search already read gets the root of
    the new data, not of the device's old copy (the block is checked before each use)."""
    rng = np.random.default_rng(8)
    dev = _device_root()
    h = N // 2
    T = _spec(rng)
    dev.set_template(N, T)
    a = _spec(rng)
    out = dev.take_output(N, 0, 0)
    band = (5, h - 5)
    dev.run(N, 0, [a], [out], band, [1.0])
    _settle_device_writes()
    built = dev.built
    a[:] = _spec(rng)                         # the same array object, new contents
    assert dev.run(N, 0, [a], [out], band, [1.0]) == 1
    _settle_device_writes()
    ref = _host(a, T, band, 1.0)
    np.testing.assert_allclose(out, ref, rtol=0, atol=2e-5 * np.abs(ref).max())
    a[h // 2] += 1.0                          # one bin
    dev.run(N, 0, [a], [out], band, [1.0])
    _settle_device_writes()
    ref = _host(a, T, band, 1.0)
    np.testing.assert_allclose(out, ref, rtol=0, atol=2e-5 * np.abs(ref).max())
    a[:] = a[::-1].copy()                     # the same values, permuted
    dev.run(N, 0, [a], [out], band, [1.0])
    _settle_device_writes()
    ref = _host(a, T, band, 1.0)
    np.testing.assert_allclose(out, ref, rtol=0, atol=2e-5 * np.abs(ref).max())
    w = a.view(np.uint64)                     # two changes that cancel in a sum of words
    w[10] += np.uint64(12345)
    w[20] -= np.uint64(12345)
    dev.run(N, 0, [a], [out], band, [1.0])
    _settle_device_writes()
    ref = _host(a, T, band, 1.0)
    np.testing.assert_allclose(out, ref, rtol=0, atol=2e-5 * np.abs(ref).max())
    assert dev.built == built + 4
    dev.give_output(N, 0, 0, out)


def test_steady_device_roots_leave_no_cyclic_garbage():
    """The device root's steady calls -- outputs taken and given back, recorded runs --
    are freed by reference counting alone (no ctypes types made per call)."""
    import gc
    rng = np.random.default_rng(9)
    dev = _device_root()
    dev.set_template(N, _spec(rng))
    blocks = [_spec(rng), _spec(rng)]
    band = (3, N // 2 - 3)

    def chunk(parity):
        outs = [dev.take_output(N, c, parity) for c in range(2)]
        dev.run(N, parity, blocks, outs, band, [1.0, 2.0])
        _settle_device_writes()
        for c, o in enumerate(outs):
            dev.give_output(N, c, parity, o)
    chunk(0)
    chunk(1)
    gc.collect()
    gc.disable()
    try:
        gc.set_debug(gc.DEBUG_SAVEALL)
        for k in range(6):
            chunk(k % 2)
        gc.collect()
        kinds = {type(o).__name__ for o in gc.garbage}
    finally:
        gc.garbage.clear()
        gc.set_debug(0)
        gc.enable()
    assert "PyCArrayType" not in kinds, kinds


def _taps(rng, c):
    t = rng.standard_normal(c).astype(np.float32)
    return t / np.linalg.norm(t)


def _tree(rng):
    counts = (101, 151)
    leaves = []
    groups = []
    for i, c in enumerate((301, 451)):
        taps = np.zeros((len(counts), max(counts)), np.complex64)
        for j, k in enumerate(counts):
            t = rng.standard_normal(k) + 1j * rng.standard_normal(k)
            taps[j, :k] = t / np.linalg.norm(t)
        lf = Leaf(taps, counts, lags=rng.integers(0, 40, len(counts)), node_id=("leaf", i))
        leaves.append(lf)
        groups.append(Inner(_taps(rng, c), children=[lf], node_id=("inner", i)))
    return Root(_spec(rng), (60, N // 2 - 200), children=groups, node_id="root")


def _run(root, inputs, device, thr):
    search = HierarchicalSearch([root], threshold=thr,
                                leaf_options=dict(engine="flat", binsize=512, device=device,
                                                  fft_lengths=(4096, 8192)))
    series, peaks = {}, {}

    def on_series(ctx):
        for ch in ctx.channels:
            series[(ctx.chunk, ch)] = np.array(ctx.series[ch])

    def on_peaks(ctx):
        for ch in ctx.channels:
            peaks[(ctx.leaf.node_id, ctx.chunk, ch)] = ctx.peaks[ch]
    search.run(inputs, on_series=on_series, on_peaks=on_peaks)
    return search, series, peaks


@pytest.mark.parametrize("place", _gpuroot.PLACES)
def test_a_gpu_search_computes_its_root_where_placed_and_gives_the_cpu_search(monkeypatch, place):
    """The root on the device (or the host) of a GPU search: the root series a hook reads
    and every leaf's peaks are the CPU search's; a second search over the same blocks (as a
    caller builds one per root) writes the first one's output buffers, and builds and
    uploads nothing on the device."""
    monkeypatch.setattr(_gpuroot.Placement, "winner", lambda self: place)
    rng = np.random.default_rng(7)
    root = _tree(rng)
    valid = (8192, N - 8192)
    inputs = {ch: BlockInput([_spec(rng) for _ in range(3)], [valid] * 3,
                             root_scale=lambda r, b, s=1.0 + 0.5 * j: s / N)
              for j, ch in enumerate(("A", "B"))}
    _, cpu_series, cpu_peaks = _run(root, inputs, "cpu", 0.0)
    thr = float(np.median(np.concatenate([np.abs(p.snr) for p in cpu_peaks.values()])))
    _, cpu_series, cpu_peaks = _run(root, inputs, "cpu", thr)
    dev = _device_root()
    taken = []
    take = dev.take_output

    def remember(n, pos, parity):
        out = take(n, pos, parity)
        taken[-1].add(out.ctypes.data)
        return out
    monkeypatch.setattr(dev, "take_output", remember)
    built = []
    for _ in range(2):
        taken.append(set())
        built.append(dev.built)
        search, gpu_series, gpu_peaks = _run(root, inputs, "gpu:0", thr)
        assert set(search._root_placed.values()) == {place}
        assert gpu_series.keys() == cpu_series.keys()
        for key, s in cpu_series.items():
            np.testing.assert_allclose(gpu_series[key], s, rtol=0, atol=2e-5 * np.abs(s).max())
        assert gpu_peaks.keys() == cpu_peaks.keys()
        for key, p in cpu_peaks.items():
            g = gpu_peaks[key]
            assert sorted(zip(g.template_indices.tolist(), g.sample_indices.tolist())) == \
                sorted(zip(p.template_indices.tolist(), p.sample_indices.tolist())), key
            np.testing.assert_allclose(np.sort(np.abs(g.snr)), np.sort(np.abs(p.snr)),
                                       rtol=1e-4)
    assert len(taken[0]) == 4 and taken[1] == taken[0]   # 2 channels x 2 chunk parities
    assert dev.built == built[1]                         # the second search built nothing
    # the caller rewrites its blocks in place: a new search gives the CPU's root of the new data
    for inp in inputs.values():
        for spec in inp.spectra:
            spec[:] = _spec(rng)
    _, cpu_series, _ = _run(root, inputs, "cpu", thr)
    _, gpu_series, _ = _run(root, inputs, "gpu:0", thr)
    for key, s in cpu_series.items():
        np.testing.assert_allclose(gpu_series[key], s, rtol=0, atol=2e-5 * np.abs(s).max())


def test_the_placement_trial_keeps_the_device_unless_the_host_is_clearly_faster(monkeypatch):
    """A run's halves go to the two arms, the first arm alternating from run to run; a run's
    halves (wall time per unit of work) are a round; the device stands on a tie and the
    host is chosen where it is faster by more than the tie in most rounds."""
    from matchedfilter import _choice
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    p = _gpuroot.Placement(("test", 1), None)
    orders = []
    for _ in range(2):
        p.new_run(10)
        orders.append([p.next(k) for k in range(10)])
        p.end_run()
    assert orders[0] == ["host"] * 5 + ["device"] * 5
    assert orders[1] == ["device"] * 5 + ["host"] * 5
    for host_cost, want in ((0.7, "host"), (0.98, "device"), (1.0, "device"), (1.3, "device")):
        _choice.reset("root-place")
        p = _gpuroot.Placement(("test", host_cost), None)
        rounds = 0
        while p.winner() is None:
            p.new_run(10)
            p.sample("host", 3 * host_cost, 3)
            p.sample("device", 4.0, 4)
            p.end_run()
            rounds += 1
            assert rounds <= p.choice.cap
        assert p.winner() == want, host_cost
    # a run with one arm only (too short to split, or setup in a half) is no round
    _choice.reset("root-place")
    p = _gpuroot.Placement(("test", 2), None)
    p.new_run(10)
    p.sample("host", 0.5, 1)
    p.end_run()
    assert not p.choice.samples["host"]


def test_a_backend_with_unverified_root_kernels_keeps_the_host_root(monkeypatch):
    """device_root gives no DeviceRoot for a backend outside VERIFIED_BACKENDS, whatever
    the host: its searches compute their roots on the host."""
    class Other:
        backend, index = "not-verified", 0

        def __str__(self):
            return "gpu:0 (not verified)"
    monkeypatch.setattr(_gpuroot, "_ROOTS", {})
    assert _gpuroot.device_root(Other()) is None
