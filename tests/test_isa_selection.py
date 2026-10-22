"""MF_ISA restricts the process, set_target changes only what it says, and a plan keeps its
kernel for every call (docs/robustness-plan.md, B3).

Until 2026-10-21: an invalid MF_ISA printed an error and the next kernel call segfaulted;
set_target(None) dropped MF_ISA (under MF_ISA=SSE4 it switched back to the widest target,
so CI's forced-target re-runs tested their target only until the first test that
restored the default); a failed set_target left the default selected; and sub-plans a
plan builds lazily (its real-series half transform, the direct refine's correlation) used
whatever target was selected then, not the plan's own."""
import os
import subprocess
import sys

import numpy as np
import pytest

import matchedfilter as mf
from conftest import scaled

#: Where the matchedfilter under test was imported from (the source tree, or an installed
#: wheel in CI): the subprocesses import the same one.
PACKAGE_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(mf.__file__)))


def _python(code, **env):
    e = dict(os.environ, PYTHONPATH=PACKAGE_PARENT, **env)
    return subprocess.run([sys.executable, "-c", code], env=e, capture_output=True, text=True,
                          timeout=scaled(120))


def test_an_invalid_mf_isa_is_refused_at_import():
    p = _python("import matchedfilter", MF_ISA="bogus")
    assert p.returncode == 1, p.stderr[-500:]          # an exception, not a crash
    assert "ValueError: MF_ISA=bogus is not one of this build's targets" in p.stderr
    for t in mf.targets():
        assert t in p.stderr


def test_mf_isa_restricts_the_process():
    narrow = mf.targets()[-1]
    code = ("import matchedfilter as mf\n"
            "assert mf.backend() == %r and mf.targets() == (%r,), (mf.backend(), mf.targets())\n"
            "mf.set_target(None)\n"
            "assert mf.backend() == %r, mf.backend()\n"
            "for t in %r:\n"
            "    if t != %r:\n"
            "        try:\n"
            "            mf.set_target(t)\n"
            "            raise SystemExit('selected %%s outside MF_ISA' %% t)\n"
            "        except ValueError:\n"
            "            assert mf.backend() == %r\n"
            "print('ok')\n") % (narrow, narrow, narrow, tuple(mf.targets()), narrow, narrow)
    p = _python(code, MF_ISA=narrow)
    assert p.returncode == 0 and p.stdout.strip() == "ok", p.stderr[-800:]


def test_a_failed_set_target_changes_nothing():
    if len(mf.targets()) < 2:
        pytest.skip("one target in this build or session")
    narrow = mf.targets()[-1]
    try:
        mf.set_target(narrow)
        with pytest.raises(ValueError):
            mf.set_target("NOT_A_TARGET")
        assert mf.backend() == narrow
    finally:
        mf.set_target(None)


def _keeps_kernel(build):
    """build() makes a plan and returns its first call. A plan made on the widest target and
    called after set_target(narrow) must equal one made and called on the widest, bit for
    bit; a plan made on the narrow target differs (or the case cannot tell, and skips)."""
    if len(mf.targets()) < 2:
        pytest.skip("one target in this build or session")
    narrow = mf.targets()[-1]
    try:
        ref = build()()
        mf.set_target(narrow)
        other = build()()
        mf.set_target(None)
        call = build()
        mf.set_target(narrow)
        switched = call()
    finally:
        mf.set_target(None)
    same = lambda a, b: all(np.array_equal(x, y) for x, y in zip(a, b))   # noqa: E731
    if same(other, ref):
        pytest.skip("the %s and %s kernels agree bit for bit here" % (mf.backend(), narrow))
    assert same(switched, ref), "a lazily built sub-plan used the selected target"


def test_a_hierarchical_plan_keeps_its_kernel_for_real_series():
    rng = np.random.default_rng(1)
    from matchedfilter.time_domain import template_spectra
    n, T = 2048, 16
    taps = (rng.standard_normal((T, 201)) / 15).astype(np.float32)
    filt, valid = template_spectra(taps, np.full(T, 201), n)
    lo, hi = int(valid[:, 0].max()), int(valid[:, 1].min())
    real = rng.standard_normal(8 * (hi - lo) + n).astype(np.float32)
    layout = (np.arange(8) * (hi - lo), np.full(8, lo), np.full(8, hi))

    def build():
        f = mf.HierarchicalFilter(n, 1, T, snr=5.0, fd=1e-3, chain=(256, 512))
        f.set_reference(np.ones(n))
        f.set_templates(np.conj(filt))
        f._execution_plan()
        return lambda: tuple(a.copy() for a in f.run_series(real, *layout, binsize=256,
                                                              threshold=0.0, raw=True))
    _keeps_kernel(build)


def test_the_direct_refine_keeps_the_plans_kernel(monkeypatch):
    from test_direct_refine import _bank
    monkeypatch.setenv("MF_DIRECT_REFINE", "1")
    n, taps, counts, spec, series, layout, ref, window = _bank()

    def build():
        f = mf.HierarchicalFilter(n, 1, spec.shape[0], snr=6.0, fd=1e-3, chain=(256, 512),
                                  search_window=window)
        f.set_reference(ref)
        f.set_templates(spec)
        f.set_taps(taps, counts)
        f._execution_plan()
        return lambda: tuple(a.copy() for a in f.run_series(series, *layout, binsize=n,
                                                              threshold=6.0, raw=True))
    _keeps_kernel(build)
