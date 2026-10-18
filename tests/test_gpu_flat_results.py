"""Flat peak results on every GPU, through the shared executor (_gpuexec).

An asynchronous result keeps its own values when its record is evicted, cleared or reused
by a later call. A sparse result, gathered on the device, holds exactly the dense result's
peaks, including grouped windows packed at an alignment and more peaks than the first read
brings back."""
import numpy as np
import pytest

import matchedfilter as mf
from conftest import usable_gpu

N = 1024


@pytest.fixture
def ctx():
    device = usable_gpu()
    if device is None:
        pytest.skip('no usable GPU')
    plan = mf.MatchedFilter(N, device=device)
    return plan._gpu


def _spectra(seed, rows):
    rng = np.random.default_rng(seed)
    return (rng.standard_normal((rows, N)) + 1j * rng.standard_normal((rows, N))).astype(
        np.complex64)


def _submit(ctx, data, tmpl, slot, grouped):
    if grouped:
        return ctx.peaks_grouped(N, data, tmpl, [(0, N, 0, data.shape[0])], 128, 0.0,
                                 slot=slot, async_submit=True)
    return ctx.peaks(N, data, tmpl, binsize=128, slot=slot, async_submit=True)


@pytest.mark.parametrize('grouped', [False, True])
@pytest.mark.parametrize('release', ['evict', 'clear'])
def test_async_result_survives_release_of_its_record(ctx, grouped, release):
    d1, d2, h = _spectra(1, 2), _spectra(2, 2), _spectra(3, 3)
    want1 = ctx.peaks(N, d1, h, binsize=128)
    want2 = ctx.peaks(N, d2, h, binsize=128)
    old = ctx.cache_limit_bytes
    ctx.cache_limit_bytes = 1                    # the next record evicts this one
    try:
        first = _submit(ctx, d1, h, 0, grouped)
        if release == 'evict':
            second = _submit(ctx, d2, h, 1, grouped)
            np.testing.assert_array_equal(second()[0], want2[0])
        else:
            ctx.clear_cache()
        idx, val = first()
        np.testing.assert_array_equal(idx, want1[0])
        np.testing.assert_array_equal(val, want1[1])
        assert first()[0] is idx                 # materialized once, early or not
    finally:
        ctx.cache_limit_bytes = old


def test_a_call_reusing_a_record_keeps_the_pending_result(ctx):
    d1, d2, h = _spectra(4, 2), _spectra(5, 2), _spectra(6, 3)
    want1 = ctx.peaks(N, d1, h, binsize=128)
    first = ctx.peaks(N, d1, h, binsize=128, slot=0, async_submit=True)
    second = ctx.peaks(N, d2, h, binsize=128, slot=0, async_submit=True)   # same buffers
    np.testing.assert_array_equal(first()[0], want1[0])
    np.testing.assert_array_equal(second()[0], ctx.peaks(N, d2, h, binsize=128)[0])


@pytest.mark.parametrize('packed', [False, True])
def test_sparse_holds_exactly_the_dense_peaks(ctx, monkeypatch, packed):
    if packed:
        # Every group's result then starts at a 64-byte boundary, which none of these row
        # offsets is: the groups are packed and the host maps them back.
        monkeypatch.setattr(ctx, 'storage_offset_alignment', 64, raising=False)
    data, h = _spectra(7, 7), _spectra(8, 3)
    groups = [(0, 700, 0, 3), (100, 1000, 3, 5), (5, 900, 5, 7)]
    dense = ctx.peaks_grouped(N, data, h, groups, 64, 0.0)
    sparse = ctx.peaks_grouped(N, data, h, groups, 64, 0.0, sparse=True)
    idx, val = sparse.dense()
    np.testing.assert_array_equal(idx, dense[0])
    np.testing.assert_array_equal(val, dense[1])
    # More peaks than the first read holds (every bin clears a zero threshold).
    many = ctx.peaks(N, _spectra(9, 16), _spectra(10, 8), binsize=16, sparse=True)
    assert len(many.flat) > ctx._SPARSE_FIRST
    ref = ctx.peaks(N, _spectra(9, 16), _spectra(10, 8), binsize=16)
    np.testing.assert_array_equal(many.dense()[0], ref[0])
    np.testing.assert_array_equal(many.dense()[1], ref[1])


def _count_uploads(ctx, monkeypatch):
    """Upload counts per input name, from the executor's one upload path."""
    counts = {'data': 0, 'tmpl': 0}
    upload = ctx._x_upload

    def counted(buf, array, slot):
        for rec in ctx._exec_records.values():
            for name in counts:
                if rec.buffers.get(name) is buf:
                    counts[name] += 1
        return upload(buf, array, slot)
    monkeypatch.setattr(ctx, '_x_upload', counted)
    return counts


@pytest.mark.parametrize('changed', ['data', 'tmpl'])
def test_a_revisited_window_sees_updated_inputs_and_unchanged_ones_stay(ctx, monkeypatch,
                                                                       changed):
    counts = _count_uploads(ctx, monkeypatch)
    d, h = _spectra(11, 1), _spectra(12, 1)
    a, b = (0, N), (100, N // 2)
    ctx.peaks(N, d, h, binsize=N // 2, window=a)
    ctx.peaks(N, d, h, binsize=N // 2, window=b, upload_data=False, upload_tmpl=False)
    (d if changed == 'data' else h)[:] = 7 + 2j
    got = ctx.peaks(N, d, h, binsize=N // 2, window=a, upload_data=changed == 'data',
                    upload_tmpl=changed == 'tmpl')
    # Window b (a record of another bin count) was not told: it must still see the change.
    got_b = ctx.peaks(N, d, h, binsize=N // 2, window=b, upload_data=False, upload_tmpl=False)
    before = dict(counts)
    ctx.peaks(N, d, h, binsize=N // 2, window=b, upload_data=False, upload_tmpl=False)
    assert counts == before                     # unchanged inputs: no transfer
    # The changed input reached both records (checked last: the reference uploads copies).
    for window, result in ((a, got), (b, got_b)):
        np.testing.assert_array_equal(result[0], ctx.peaks(N, d.copy(), h.copy(),
                                                           binsize=N // 2, window=window)[0])


def test_a_split_call_keeps_its_inputs_resident(ctx, monkeypatch):
    """More bins than one dispatch takes: the pieces share the uploaded inputs."""
    counts = _count_uploads(ctx, monkeypatch)
    d, h = _spectra(13, 1), _spectra(14, 1)
    ctx.peaks(N, d, h, binsize=1, window=(17, N))
    warm = dict(counts)
    ctx.peaks(N, d, h, binsize=1, window=(17, N), upload_data=False, upload_tmpl=False)
    assert counts == warm


def test_changing_data_keeps_templates_resident(ctx, monkeypatch):
    counts = _count_uploads(ctx, monkeypatch)
    d, h = _spectra(15, 1), _spectra(16, 1)
    ctx.peaks(N, d, h)
    for _ in range(3):
        d *= 2
        ctx.peaks(N, d, h, upload_data=True, upload_tmpl=False)
    assert counts == {'data': 4, 'tmpl': 1}
