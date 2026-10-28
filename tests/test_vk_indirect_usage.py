"""Every buffer a Vulkan indirect dispatch reads its group count from was created with
VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT, as the valid usage of vkCmdDispatchIndirect requires.

RADV and ANV dispatch from a buffer without that usage, so a missing flag passes every result
check, and no validation layer is installed to report it. From 8fd9f471 and 4a148370
(2026-10-19) the executor's buffers had none, and the listed ops read their counts from them:
a hierarchical call's counts (args0, args1, bargs), a follow-up group's table, the gate-way
timing's count. These tests watch the Vulkan calls themselves -- the usage each vkCreateBuffer
was given and the buffer each vkCmdDispatchIndirect names -- over every path that records a
listed op, so they do not depend on how the driver chooses a buffer's usage.
"""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank

#: The specification's value, not the driver's constant: a wrong constant is a failure too.
VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT = 0x100


def _vulkan_gpu():
    """The usable GPU's device string, if it is a Vulkan one; else skip."""
    from conftest import usable_gpu
    import matchedfilter as mf
    device = usable_gpu()
    if device is None or next(d for d in mf.devices() if str(d) == device).backend != "vulkan":
        pytest.skip("requires a Vulkan GPU")
    return device


class _Watch:
    """The device's Vulkan function table, wrapped: `reads` gets (pipeline kind, buffer
    usage) for each indirect dispatch recorded, the usage None for a buffer created before
    the watch began."""

    def __init__(self, monkeypatch, ctx):
        vk = ctx.vk                           # the device's table, which every context shares
        self.ctx, self.reads, self._usage, self._bound = ctx, [], {}, {}
        create, bind, indirect = (vk.vkCreateBuffer, vk.vkCmdBindPipeline,
                                  vk.vkCmdDispatchIndirect)

        def vk_create_buffer(device, info, allocator, handle):
            rc = create(device, info, allocator, handle)
            if rc == 0:
                self._usage[handle._obj.value] = info._obj.usage
            return rc

        def vk_cmd_bind_pipeline(cmd, point, pipeline):
            self._bound[getattr(cmd, "value", cmd)] = getattr(pipeline, "value", pipeline)
            return bind(cmd, point, pipeline)

        def vk_cmd_dispatch_indirect(cmd, buf, offset):
            pipe = self._bound.get(getattr(cmd, "value", cmd))
            self.reads.append((self._kind(pipe), self._usage.get(getattr(buf, "value", buf))))
            return indirect(cmd, buf, offset)

        monkeypatch.setattr(vk, "vkCreateBuffer", vk_create_buffer)
        monkeypatch.setattr(vk, "vkCmdBindPipeline", vk_cmd_bind_pipeline)
        monkeypatch.setattr(vk, "vkCmdDispatchIndirect", vk_cmd_dispatch_indirect)

    def _kind(self, pipe):
        """The kernel a pipeline was built as (its cache key's first name: refine, items,
        fwd_listed, ...), or None."""
        for key, entry in self.ctx._pipelines.items():
            if getattr(entry[0], "value", entry[0]) == pipe:
                while isinstance(key[0], tuple):
                    key = key[0]
                return key[0]
        return None

    def check(self, what, kinds):
        """Assert the indirect dispatches recorded since the last check include each of
        `kinds` and read only buffers created with INDIRECT_BUFFER usage; return them."""
        reads, self.reads = self.reads, []
        seen = {k for k, _ in reads}
        assert set(kinds) <= seen, "%s: no indirect dispatch of %s (saw %s)" % (
            what, sorted(set(kinds) - seen), sorted(seen, key=str))
        unknown = sum(u is None for _, u in reads)
        assert not unknown, ("%s: %d of %d indirect dispatches read a buffer created before "
                             "the watch began" % (what, unknown, len(reads)))
        bad = sorted({(k, hex(u)) for k, u in reads
                      if not u & VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT}, key=str)
        assert not bad, ("%s: %d of %d indirect dispatches read a buffer created without "
                         "VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT, as (kernel, usage): %s" % (
                             what, sum(not u & VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT
                                       for _, u in reads), len(reads), bad))
        return reads


@pytest.fixture
def watch(monkeypatch):
    """A _Watch on the Vulkan GPU, with a context made under it (watch.ctx)."""
    from matchedfilter import _vkcompute
    index = int(_vulkan_gpu().split(":")[1])
    table = _vkcompute.Context(index)        # reaches the device's function table
    w = _Watch(monkeypatch, table)
    w.ctx = _vkcompute.Context(index)
    try:
        yield w
    finally:
        monkeypatch.undo()
        w.ctx.destroy()
        table.destroy()


def _spectra(rng, rows, n):
    return (rng.standard_normal((rows, n)) + 1j * rng.standard_normal((rows, n))
            ).astype(np.complex64)


def test_hierarchical_tiers_and_refine_dispatch_from_indirect_buffers(watch):
    """A cascade's second tier (args0) and refine (args1), and a one-tier call's refine
    (args0), on a context made under the watch."""
    ctx = watch.ctx
    n, b0, b1, nd, nt = 4096, 128, 512, 4, 8
    rng = np.random.default_rng(42)
    d, h = _spectra(rng, nd, n), _spectra(rng, nt, n)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    lag = 500
    d[1] += 50.0 * h[2] * np.exp(-2j * np.pi * np.arange(n) * lag / n).astype(np.complex64)
    idx, _ = ctx.hier_peaks(n, b1, d, h, h[:, :b0], 0.9, cascade_band=b0, ct1=h[:, :b1],
                            raw_thr1=2.0, threshold=30.0)
    assert idx[1, 2, 0] == lag
    assert len(watch.check("cascade", ["refine"])) >= 2
    idx, _ = ctx.hier_peaks(n, b1, d, h, h[:, :b1], 2.0, threshold=30.0)
    assert idx[1, 2, 0] == lag
    watch.check("one tier", ["refine"])


def test_gate_way_timing_dispatches_from_an_indirect_buffer(watch):
    """The gate-way timing's own count buffer (_time_gate_ways)."""
    ctx = watch.ctx
    band = next((b for b in (256, 512, 128, 1024)
                 if ctx._shipped("tier1", b) and ctx._shipped("tier1gate", b)), None)
    if band is None:
        pytest.skip("no one-bin tier with a gate build is shipped for this device")
    times = ctx._time_gate_ways(band, ("gate", "tier"))
    assert set(times) == {"gate", "tier"}
    watch.check("gate-way timing", ["refine"])


def test_band_feed_recompute_dispatches_from_indirect_buffers(watch, monkeypatch):
    """A search whose hierarchical calls claim their forward (the band feed): the listed
    recompute of the refine blocks (bargs), with the cascade's tiers and refine."""
    from matchedfilter import _gpuhier
    from test_time_domain import _whitened_inspiral_bank
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    monkeypatch.setenv("MF_CHAIN_FORCE", "256,512")
    monkeypatch.setenv("MF_BAND_FORWARD", "1")
    rng = np.random.default_rng(5)
    counts = sorted(rng.integers(200, 1800, 24))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=4.0,
                                false_dismissal=1e-3, device=_vulkan_gpu(),
                                fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    S = 1 << 17
    X = np.fft.fft(rng.standard_normal(S))
    X[S // 2:] = 0
    x = (np.fft.ifft(X) * 2).astype(np.complex64)
    x[S // 3] += 40.0                        # a loud sample: refine survivors in many blocks
    before = _gpuhier.CLAIMS[0]
    out = TimeDomainFilterBank.filter_series_many(
        [(bank, x, dict(windows=slice(4096, S - 4096)))] * 2)
    assert _gpuhier.CLAIMS[0] > before, "no call claimed its forward"
    assert all(len(r.snr) for r in out)
    watch.check("band feed", ["fwd_listed", "refine"])


def test_device_followups_dispatch_from_indirect_buffers(watch, monkeypatch):
    """A batch of threshold-0 single-template calls run as device follow-ups: the listed
    forward and refineItems read their count from the group's table."""
    from matchedfilter import _gpuhost
    from test_time_domain import _whitened_inspiral_bank
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    rng = np.random.default_rng(95)
    counts = list(rng.integers(200, 400, 33))
    taps, w, df = _whitened_inspiral_bank(rng, counts)
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine="hier", threshold=4.5,
                                false_dismissal=1e-3, device=_vulkan_gpu(),
                                fft_lengths=[2048], binsize=2048)
    bank.set_reference(w, delta_f=df)
    S = 1 << 17
    rows = bank.empty_shared((2, S))
    for r in rows:
        r[:] = (rng.standard_normal(S) + 1j * rng.standard_normal(S)).astype(np.complex64)
    taken = []
    submit = _gpuhost.submit_followups
    monkeypatch.setattr(_gpuhost, "submit_followups",
                        lambda jobs: (lambda c: taken.append(c is not None) or c)(submit(jobs)))
    jobs = []
    for k in range(6):
        c0 = int(rng.integers(20000, S - 20000))
        jobs.append((bank, rows[k % 2], dict(windows=slice(c0 - 3000, c0 + 3100), binsize=61,
                                             threshold=0.0, template_index=(7 * k) % 33)))
    got = TimeDomainFilterBank.filter_series_many(jobs)
    assert taken == [True], "the device follow-up path was not taken"
    assert len(got) == len(jobs)
    watch.check("follow-ups", ["fwd_listed", "items"])
