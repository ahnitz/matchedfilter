"""A loud injection must never be dismissed by an fp16 coarse gate (fail open).

Above SNR ~2500 the half-width coarse transform overflows to inf and then NaN. Under the
default Metal fast-math, and with `x >= thr` comparisons, that NaN lost every comparison and
the loudest pair was dismissed (tools/gate_margin.py --loud on review/unify: 0 peaks against
the CPU's 62). The Metal coarse and compaction kernels now compile with IEEE math and compare
as !(x < thr), so an overflowing pair is refined exactly."""
import sys

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter.benchmark import _inspiral_power

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Metal only")


@pytest.mark.parametrize("chain", [(256,), (128, 512), (64,)])
@pytest.mark.parametrize("tile", ["0", "1"])
def test_loud_injection_peaks_match_cpu(monkeypatch, chain, tile):
    monkeypatch.setenv("MF_METAL_COARSE_TILE", tile)
    n, nd, nt = 4096, 4, 16
    power = _inspiral_power(n)
    h = np.sqrt(power).astype(np.complex64)
    rng = np.random.default_rng(2026)
    tm = (h * np.exp(2j * np.pi * rng.random((nt, n)) * 0.05)).astype(np.complex64)
    noise = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    for snr in (2000, 2500, 10000, 100000):
        data = noise.copy()
        data[1] += snr * np.conj(tm[3]) / np.linalg.norm(tm[3]) * np.sqrt(n)
        got = []
        for dev in (None, "gpu:0"):
            try:
                hf = mf.HierarchicalFilter(n, nd, nt, chain=chain, snr=5.5, fd=1e-3, device=dev)
            except Exception as e:                  # pragma: no cover - no device
                pytest.skip("no Metal device: %s" % e)
            hf.set_reference(power)
            hf.set_templates(np.conj(tm))
            hf.set_data(data)
            r = hf.run(binsize=n // 4, threshold=6.0 * np.sqrt(n))
            got.append(r["index"])
        np.testing.assert_array_equal(got[1] >= 0, got[0] >= 0, err_msg="snr %g" % snr)
