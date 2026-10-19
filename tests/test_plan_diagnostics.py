"""The engine's diagnostic dump (MF_HMF_DUMP, hmf.c) describes the caller's plan only: plans the
library makes for itself, such as the cost calibration a pinned chain's late-recheck choice asks
for, neither truncate the file nor write their own pairs into it."""
import numpy as np

import matchedfilter as mf


def test_the_dump_holds_only_the_callers_pairs(monkeypatch, tmp_path):
    n, chain, nd, nt = 2048, (256, 512), 6, 21
    rng = np.random.default_rng(7)
    f = np.fft.fftfreq(n)
    power = np.zeros(n)
    power[f > 0] = f[f > 0] ** (-7 / 3)
    h = (np.sqrt(power) * np.exp(2j * np.pi * rng.random((nt, n)))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    d = (rng.standard_normal((nd, n)) + 1j * rng.standard_normal((nd, n))).astype(np.complex64)
    path = tmp_path / "dump.bin"
    monkeypatch.setenv("MF_HMF_DUMP", str(path))
    hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, chain=chain)
    hf.set_reference(power)
    hf.set_coarse_threshold(tuple(0.0 for _ in chain))
    hf.set_data(d)
    hf.set_templates(h)
    hf.run(binsize=n // 4, threshold=4.0)
    del hf
    rec = np.fromfile(path, np.float32).reshape(-1, 8)
    pairs = sorted(map(tuple, rec[:, 6:8].astype(int)))
    # A zero first threshold passes every pair: each is recorded exactly once.
    assert pairs == [(i, j) for i in range(nd) for j in range(nt)]
