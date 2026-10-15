"""Packed Q15 tails must preserve each original broadcast lane exactly.

The screen oracle runs one data row at a time over complete template tiles.
The command-line mode also emits exact screen and hierarchical-output digests
for comparison between separate baseline/candidate PYTHONPATH processes:

  PYTHONPATH=<build>/python python tests/test_q15_tail_packing.py \
      --target AVX3 --output <results.json>

No timing is taken here. Screens cover every head/tail length with a rotating
offset, rather than the unnecessary Cartesian product of those two lengths.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import _core


BANDS = (64, 128, 256, 512, 1024)
DATA_COUNTS = (1, 2, 3, 4, 5, 31, 32, 33)


class _Screen:
    """Use the public C API to cover balanced and pair-batch input layouts."""
    def __init__(self, n, data, templates, pairbatch):
        self.lib = C.CDLL(_core.__file__)
        ptr, integer, size = C.c_void_p, C.c_int, C.c_size_t
        signatures = {
            "ap_mf_create": ([size, integer, integer], ptr),
            "ap_mf_create_pairbatch": ([size, integer, integer], ptr),
            "ap_mf_destroy": ([ptr], None),
            "ap_mf_set_data": ([ptr, integer, ptr], integer),
            "ap_mf_set_template": ([ptr, integer, ptr], integer),
            "ap_mf_q15_screen": ([ptr, integer, integer, integer, integer,
                                   C.c_float, size, size, ptr, ptr], integer),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.lib, name)
            fn.argtypes, fn.restype = args, result
        create = self.lib.ap_mf_create_pairbatch if pairbatch else self.lib.ap_mf_create
        self.ptr = create(n, len(data), len(templates))
        assert self.ptr
        self.set_inputs(data, templates)

    def set_inputs(self, data, templates):
        for d, row in enumerate(data):
            assert self.lib.ap_mf_set_data(self.ptr, d, row.ctypes.data) == 0
        for t, row in enumerate(templates):
            assert self.lib.ap_mf_set_template(self.ptr, t, row.ctypes.data) == 0

    def run(self, d0, nd, t0, nt, threshold, start, end, with_stat=True):
        # Guard both ends; a partial packed tile must not write padding lanes.
        mask = np.full(nd * nt + 2, 197, np.uint8)
        stat = np.full(nd * nt + 2, -12345.0, np.float32)
        total = self.lib.ap_mf_q15_screen(
            self.ptr, d0, nd, t0, nt, threshold, start, end,
            mask[1:-1].ctypes.data, stat[1:-1].ctypes.data if with_stat else None)
        assert total >= 0
        assert mask[0] == mask[-1] == 197
        assert stat[0] == stat[-1] == -12345.0
        assert total == int(mask[1:-1].sum())
        if not with_stat:
            assert np.all(stat == -12345.0)
        return total, mask[1:-1].reshape(nd, nt), stat[1:-1].reshape(nd, nt)

    def close(self):
        if self.ptr:
            self.lib.ap_mf_destroy(self.ptr)
            self.ptr = None


def _noise(rng, shape):
    return (rng.normal(size=shape) + 1j * rng.normal(size=shape)).astype(np.complex64)


def _digest_update(digest, metadata, arrays):
    digest.update(json.dumps(metadata, separators=(",", ":")).encode())
    for array in arrays:
        digest.update(np.ascontiguousarray(array).tobytes())


def _screen_sweep(n, pairbatch):
    width = _core.MF(n, 1, 1).q15_lanes()
    if not width:
        pytest.skip("Q15 unavailable for this band/target")
    rng = np.random.default_rng(713 + n)
    nd_all, nt_all = 35, 4 * width
    data, templates = _noise(rng, (nd_all, n)), _noise(rng, (nt_all, n))
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    data *= np.geomspace(.05, 20, nd_all, dtype=np.float32)[:, None]
    templates *= np.geomspace(.05, 20, nt_all, dtype=np.float32)[:, None]
    data[4] = 0
    templates[width + 2] = 0
    actual = _Screen(n, data, templates, pairbatch)
    reference = _Screen(n, data, templates, pairbatch)
    digest, calls = hashlib.sha256(), 0
    windows = ((0, n + 7), (3, n - 5), (n // 2 + 1, n // 2 + 2), (20, n - 20))
    thresholds = (0.0, 4.0, 1e8)
    try:
        # Each update invalidates quantized inputs that were used by earlier tails.
        for update in range(2):
            if update:
                data[2:5] = _noise(rng, (3, n)) * np.float32(.3)
                templates[width - 1:width + 3] = _noise(rng, (4, n)) / np.sqrt(n)
                actual.set_inputs(data, templates)
                reference.set_inputs(data, templates)
            oracle = {}
            for wi, (lo, hi) in enumerate(windows):
                for threshold in thresholds:
                    rows = [reference.run(d, 1, 0, nt_all, threshold, lo, hi)
                            for d in range(nd_all)]
                    oracle[wi, threshold] = (np.concatenate([r[1] for r in rows]),
                                              np.concatenate([r[2] for r in rows]))
            # Multiplication by an odd number permutes every offset of a SIMD tile.
            for tail in range(1, width + 1):
                offset = (7 * tail) % width
                ranges = ((width + offset, 2 * width + tail - offset), (width, tail))
                for t0, nt in ranges:
                    for di, nd in enumerate(DATA_COUNTS):
                        d0 = (tail + di) % (nd_all - nd + 1)
                        for wi, (lo, hi) in enumerate(windows):
                            threshold = thresholds[(tail + di + wi + update) % len(thresholds)]
                            expected_mask, expected_stat = oracle[wi, threshold]
                            expected_mask = expected_mask[d0:d0 + nd, t0:t0 + nt]
                            expected_stat = expected_stat[d0:d0 + nd, t0:t0 + nt]
                            for with_stat in (False, True):
                                count, mask, stat = actual.run(d0, nd, t0, nt, threshold,
                                                              lo, hi, with_stat)
                                np.testing.assert_array_equal(mask, expected_mask)
                                if with_stat:
                                    # Integer views require identical floating-point bits.
                                    np.testing.assert_array_equal(stat.view(np.uint32),
                                                                  expected_stat.view(np.uint32))
                                _digest_update(digest, (update, d0, nd, t0, nt, lo, hi,
                                                        threshold, with_stat, count),
                                               (mask, stat) if with_stat else (mask,))
                                calls += 1
    finally:
        actual.close()
        reference.close()
    return dict(n=n, pairbatch=pairbatch, lanes=width, calls=calls,
                sha256=digest.hexdigest())


@pytest.mark.parametrize("n", BANDS)
@pytest.mark.parametrize("pairbatch", [False, True])
def test_q15_tail_statistics_and_masks(n, pairbatch):
    mf.backend()
    _screen_sweep(n, pairbatch)


def _assert_same_screen(actual, expected):
    assert actual[0] == expected[0]
    np.testing.assert_array_equal(actual[1], expected[1])
    np.testing.assert_array_equal(actual[2].view(np.uint32), expected[2].view(np.uint32))


def _single_row_screen(plan, nd, nt, threshold, lo, hi):
    rows = [plan.run(d, 1, 0, nt, threshold, lo, hi) for d in range(nd)]
    return (sum(row[0] for row in rows), np.concatenate([row[1] for row in rows]),
            np.concatenate([row[2] for row in rows]))


@pytest.mark.parametrize("pairbatch", [False, True])
def test_q15_tail_at_end_of_allocated_template_group(pairbatch):
    mf.backend()
    if not _core.MF(256, 1, 1).q15_lanes():
        pytest.skip("Q15 unavailable for this target")
    rng = np.random.default_rng(1901)
    data, templates = _noise(rng, (5, 256)), _noise(rng, (56, 256))
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    data *= np.array([.01, .5, 1, 2, 4], np.float32)[:, None]
    for tail in range(1, 25):
        nt = 32 + tail
        # The allocated plan itself ends here, so all remaining template lanes
        # in its last quantized group are padding, not initialized real rows.
        actual = _Screen(256, data, templates[:nt], pairbatch)
        reference = _Screen(256, data, templates[:nt], pairbatch)
        try:
            for lo, hi in ((20, 236), (0, 256), (127, 128)):
                expected = _single_row_screen(reference, 5, nt, 4.0, lo, hi)
                _assert_same_screen(actual.run(0, 5, 0, nt, 4.0, lo, hi), expected)
                count, mask, _ = actual.run(0, 5, 0, nt, 4.0, lo, hi, False)
                assert count == expected[0]
                np.testing.assert_array_equal(mask, expected[1])
        finally:
            actual.close()
            reference.close()


def _retained_backend_case(created_target, other_target, pairbatch):
    restore = mf.backend()  # Consume MF_ISA before selecting either test target.
    actual = reference = None
    try:
        mf.set_target(created_target)
        if not _core.MF(256, 1, 1).q15_lanes():
            return False
        rng = np.random.default_rng(1902)
        data, templates = _noise(rng, (5, 256)), _noise(rng, (49, 256))
        templates /= np.linalg.norm(templates, axis=1, keepdims=True)
        data *= np.array([.01, .5, 1, 2, 4], np.float32)[:, None]
        actual = _Screen(256, data, templates, pairbatch)
        reference = _Screen(256, data, templates, pairbatch)
        cases = ((4.0, 20, 236), (0.0, 127, 128), (1e8, 0, 256))
        expected = [_single_row_screen(reference, 5, 49, *case) for case in cases]
        # actual has not called q15_prepare yet. Changing the process target
        # must not change its Q15 width, scratch requirements or tile dispatch.
        for target in (other_target, created_target, other_target):
            mf.set_target(target)
            for case, wanted in zip(cases, expected):
                _assert_same_screen(actual.run(0, 5, 0, 49, *case), wanted)
    finally:
        if actual is not None:
            actual.close()
        if reference is not None:
            reference.close()
        mf.set_target(restore)


@pytest.mark.parametrize("created_target,other_target", [
    ("AVX3", "AVX2"), ("AVX3", "SSE4"),
    ("AVX2", "AVX3"), ("SSE4", "AVX3"),
])
@pytest.mark.parametrize("pairbatch", [False, True])
def test_q15_tail_keeps_plan_backend(created_target, other_target, pairbatch):
    # targets() reflects the dispatch override too. A forced-ISA regression
    # run must still discover every backend this machine can actually execute.
    restore = mf.backend()
    try:
        mf.set_target(None)
        available = set(mf.targets())
    finally:
        mf.set_target(restore)
    if not {created_target, other_target}.issubset(available):
        pytest.skip("requires AVX3 and the selected narrower SIMD target")
    # Isolate a dispatch regression: selecting a wider kernel for an existing
    # narrow plan can overwrite its scratch allocation, not merely fail an assert.
    script = """
import runpy
import sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
except ImportError:
    pass
namespace = runpy.run_path(sys.argv[1])
if namespace['_retained_backend_case'](sys.argv[2], sys.argv[3], sys.argv[4] == '1') is False:
    raise SystemExit(77)
"""
    result = subprocess.run([sys.executable, "-c", script, str(Path(__file__).resolve()),
                            created_target, other_target, str(int(pairbatch))],
                            capture_output=True, text=True)
    if result.returncode == 77:
        pytest.skip("Q15 unavailable for the retained plan target")
    assert result.returncode == 0, result.stdout + result.stderr


def _hierarchical_digest():
    """Final results and non-timing counters for cross-build exact comparison."""
    n, band = 2048, 256
    width = _core.MF(band, 1, 1).q15_lanes()
    if not width:
        pytest.skip("Q15 unavailable for this band/target")
    rng = np.random.default_rng(8193)
    nd_all, nt_all = 35, 3 * width
    data = _noise(rng, (nd_all, n))
    templates = _noise(rng, (nt_all, n))
    templates /= np.linalg.norm(templates, axis=1, keepdims=True)
    data[::4] *= np.float32(.05)
    data[1::4] *= np.float32(3)
    plan = _core.HMF(n, nd_all, nt_all, [band, 512], 3)
    plan.set_reference(np.ones(n, np.float32))
    plan.set_data_batch(0, data)
    plan.set_template_batch(0, templates)
    assert plan.set_q15(True)
    digest, calls = hashlib.sha256(), 0
    for tail in (1, width // 2 - 1, width - 1, width):
        t0, nt = width - 1, width + tail
        for nd in DATA_COUNTS:
            for lo, hi, binsize in ((0, n, n), (17, n - 13, 173), (311, 312, n)):
                rows = nd * nt
                nb = (hi - lo + binsize - 1) // binsize
                idx = np.empty(rows * nb, np.int64)
                val = np.empty(rows * nb, np.complex64)
                mag = np.empty(rows * nb, np.float32)
                counts = np.empty(rows, np.int32)
                plan.set_thresholds([2.5, 3.0])
                before = np.asarray([*plan.stats(), *(p for _, p, _ in plan.tier_stats()),
                                     plan.q15_stats()[1]], np.int64)
                count = plan.run(1, nd, t0, nt, binsize, 0.5, lo, hi,
                                 idx, val, mag, counts)
                after = np.asarray([*plan.stats(), *(p for _, p, _ in plan.tier_stats()),
                                    plan.q15_stats()[1]], np.int64)
                assert count == int(counts.sum())
                _digest_update(digest, (tail, nd, lo, hi, binsize, count),
                               (idx, val, mag, counts, after - before))
                calls += 1
    return dict(n=n, chain=[band, 512], lanes=width, calls=calls,
                sha256=digest.hexdigest())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(MF_AUTOTUNE="0", MF_GATE16="0")
    mf.backend()
    mf.set_target(args.target)
    results = [_screen_sweep(n, pairbatch) for n in BANDS for pairbatch in (False, True)]
    report = dict(target=mf.backend(), core_sha256=hashlib.sha256(Path(_core.__file__).read_bytes()).hexdigest(),
                  screens=results, hierarchical=_hierarchical_digest())
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
