"""The register -> output index map, pinned against the GPU that produced it."""
import numpy as np
import pytest

import sys
_TOOLS = None

def _tools_dir():
    """Locate tools/ from the TEST file, not from the installed package.

    These tests used matchedfilter.__file__ to find it, which works only in
    a source checkout -- against an installed wheel the package lives in
    site-packages and tools/ is nowhere near it, so collection failed and
    the suite could not be used to verify an install at all.
    """
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    for base in (here.parent, here.parent.parent):
        cand = base / "tools"
        if (cand / "gpu_output_order.py").is_file():
            return cand
    return None
_TOOLS = _tools_dir()
if _TOOLS is None:
    pytest.skip("tools/ is not beside the tests (installed package?)",
                allow_module_level=True)
sys.path.insert(0, str(_TOOLS))
import gpu_output_order as output_order


@pytest.mark.parametrize("n", sorted(output_order.RADICES))
def test_permutation_is_a_permutation(n):
    p = output_order.permutation(n)
    assert sorted(p) == list(range(n))


@pytest.mark.parametrize("n,radices", sorted(output_order.RADICES.items()))
def test_radices_multiply_to_the_transform_length(n, radices):
    prod = 1
    for r in radices:
        prod *= r
    assert prod == n


def test_high_bits_of_the_index_come_from_the_register():
    """index = q*WG + reverse(tid) -- the property the fast path rests on."""
    n = 4096
    wg = n // 16
    for q in range(16):
        for tid in (0, 1, 7, 255):
            assert output_order.slot_to_index(tid * 16 + q,
                                              output_order.RADICES[n]) // wg == q


def test_register_bins_degrade_gracefully_with_an_unaligned_start():
    """An arbitrary start does not disable the fast path, it shrinks it."""
    n = 4096
    assert len(output_order.bin_is_fixed_by_register(n, 0, 4096)) == 16
    assert len(output_order.bin_is_fixed_by_register(n, 0, 256)) == 16
    partial = output_order.bin_is_fixed_by_register(n, 37, 1000)
    assert 0 < len(partial) < 16


def _natural_store(n, cap):
    """tierb.slang storeNatural, address by address: per round, the staging slot each register
    of each thread is written to and the lag each reader thread stores from each slot.
    Returns (lags stored, cache lines per wave store, worst lanes per LDS bank on a write)."""
    import gpu_regmodel as rm
    import kernel_variants as kv
    R = kv.radix(n)
    WG, levels, inner = rm.geom(n, R)
    lgR = R.bit_length() - 1
    CH = min(max(min(R * WG, cap) // WG, 1), R)

    def s2i(slot):
        return rm.slot_to_index(slot, levels, inner, lgR)
    fixed = s2i(R - CH)
    free = [b for b in range(n.bit_length() - 1) if not (fixed >> b) & 1]

    def squeeze(x):
        return sum(((x >> b) & 1) << k for k, b in enumerate(free))

    def expand(x):
        return sum(((x >> k) & 1) << b for k, b in enumerate(free))

    def swizzle(x):
        return x ^ ((x >> 5) & 31)
    stored, lines, bank = [], 0, 0
    for c in range(R // CH):
        stage = {}
        for j in range(CH):
            i = c * CH + j
            addrs = [swizzle(squeeze(s2i(tid << lgR))) ^ swizzle(squeeze(s2i(i)))
                     for tid in range(WG)]
            for tid, a in enumerate(addrs):
                assert 0 <= a < CH * WG and a not in stage
                stage[a] = s2i(tid * R + i)       # the lag register i of thread tid holds
            for w in range(0, WG, 32):
                bank = max(bank, max(np.bincount(np.array(addrs[w:w + 32]) % 16)))
        for j in range(CH):
            lags = []
            for t in range(WG):
                lag = expand(t) | expand(j * WG) | s2i(c * CH)
                assert stage[swizzle(t) ^ swizzle(j * WG)] == lag
                lags.append(lag)
            stored.extend(lags)
            for w in range(0, WG, 32):
                lines = max(lines, len({lag // 16 for lag in lags[w:w + 32]}))
    return stored, lines, bank


@pytest.mark.parametrize("n", [1024, 2048, 4096, 8192, 16384, 32768, 65536])
def test_correlation_output_is_stored_in_natural_order_by_whole_lines(n):
    """The full-correlation kernels store each lag once, and every wave's store covers two
    128-byte lines (32 lanes x 8 bytes): the transform's digit-reversed order, stored
    directly, put each lane in its own line (half the middle stage's device time). Every
    staging cap a build uses."""
    import kernel_variants as kv
    for cap in sorted({kv.LDS_CAP[n], kv.PORTABLE_CAP}):
        stored, lines, bank = _natural_store(n, cap)
        assert sorted(stored) == list(range(n))
        assert lines == 2
        assert bank <= 8                     # 2 is conflict-free for 8-byte elements


def test_the_correlation_kernels_store_through_the_natural_order():
    """Both full-correlation entries end in storeNatural, not a per-register store."""
    src = (_TOOLS.parent / "src" / "gpu" / "tierb.slang").read_text()
    for entry in ("void fullCorrelation(", "void fullCorrelationSeries("):
        body = src[src.index(entry):]
        body = body[:body.index("\n}\n")]
        assert "storeNatural(r, tid, output" in body
        assert "slotToIndex" not in body
