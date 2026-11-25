"""Every GPU driver's Context provides every primitive the shared executor calls (the list in
the _gpuexec module docstring). Read from the sources, so the check runs on every platform:
the Metal driver's _x_peaks once sat in its _Buffer class, and `ladder --roofline` failed on
an M2 only, with an AttributeError."""
import ast
import os
import re

import pytest

import matchedfilter

PKG = os.path.dirname(matchedfilter.__file__)
DRIVERS = ("_vkcompute.py", "_cudacompute.py", "_mtlcompute.py")


def _methods(path, cls):
    """Names of the functions defined directly in class `cls` of the module at path."""
    tree = ast.parse(open(os.path.join(PKG, path)).read())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    raise AssertionError("no class %s in %s" % (cls, path))


def _primitives():
    """The _x_ names the _gpuexec docstring lists as driver primitives."""
    doc = ast.get_docstring(ast.parse(open(os.path.join(PKG, "_gpuexec.py")).read()))
    listed = doc.split("Driver primitives", 1)[1].split("\nFeatures a driver reports", 1)[0]
    lines = [l for l in listed.splitlines() if re.match(r"\s{2}_x_", l)]
    names = {m for l in lines for m in re.findall(r"(_x_[a-z0-9_]+)\(", l)}
    assert len(names) > 15, names
    return names


@pytest.mark.parametrize("driver", DRIVERS)
def test_every_driver_context_defines_every_primitive(driver):
    shared = _methods("_gpuexec.py", "Executor") | _methods("_gpu_cache.py", "InputUploads")
    missing = sorted(_primitives() - _methods(driver, "Context") - shared)
    assert not missing, "%s Context lacks %s" % (driver, missing)


def test_pow2_scaling_is_ldexp_bit_for_bit():
    """The fp16 tier's template and data scaling (a product with 2^e) gives np.ldexp's value
    bit for bit at every exponent the tier uses, for normal, subnormal, overflowing,
    infinite and NaN components."""
    import numpy as np
    from matchedfilter._gpuhier import pow2_scaled
    rng = np.random.default_rng(5)
    x = rng.standard_normal(4096).astype(np.float32) * np.float32(1e-3)
    edge = np.array([1e-38, 1.4e-45, 6e-39, 1.17549435e-38, 3e38, -3e38, np.inf, -np.inf,
                     np.nan, -0.0, 0.0, 65504.0], np.float32)
    a = np.concatenate([x, edge, edge[::-1]]).view(np.complex64)
    with np.errstate(over="ignore"):
        for e in range(-140, 141):
            want = np.ldexp(a.view(np.float32), e) if e else a.view(np.float32)
            np.testing.assert_array_equal(pow2_scaled(a, e).view(np.uint32),
                                          np.asarray(want, np.float32).view(np.uint32))


def test_half_bits_is_numpys_float16_cast_bit_for_bit():
    """_core.half_bits (the fp16 tiers' template packing) gives NumPy's float32 -> float16
    bits: round to nearest with ties to even, subnormal halves, overflow to infinity, a NaN
    kept a NaN of its sign, both signs. A strided sweep over every float32
    bit pattern and each edge class (all 2^32 patterns were checked once, 2026-11-25)."""
    import numpy as np
    from matchedfilter import _core
    from matchedfilter._shared import pack_half2
    sweep = np.arange(0, 1 << 32, 4099, dtype=np.uint64).astype(np.uint32)
    exps = np.arange(256, dtype=np.uint32) << 23
    mants = np.array([0, 1, 0x1000, 0x1001, 0xfff, 0x2000, 0x3000, 0x7ff, 0x800, 0x3fff,
                      0x7fe000, 0x7ff000, 0x7fffff, 0x400000, 0x400001], np.uint32)
    edges = (exps[:, None] | mants[None, :]).ravel()
    bits = np.concatenate([sweep, edges, edges | np.uint32(0x80000000)])
    f = bits.view(np.float32)
    with np.errstate(all="ignore"):
        want = f.astype(np.float16).view(np.uint16)
    got = np.empty(f.size, np.uint16)
    _core.half_bits(f, got)
    # A NaN stays a NaN of its sign; which payload bits survive is the platform's choice
    # (NumPy's cast quiets a signalling NaN on ARM and keeps it one on x86).
    nan = np.isnan(f)
    bad = np.flatnonzero((got != want) & ~nan)
    assert bad.size == 0, [(hex(int(bits[i])), hex(int(got[i])), hex(int(want[i])))
                           for i in bad[:5]]
    assert np.all(np.isnan(got.view(np.float16)[nan]))
    assert np.array_equal(got[nan] >> 15, (bits[nan] >> 31).astype(np.uint16))
    c = f[: (f.size // 2) * 2].view(np.complex64).reshape(-1, 2)
    with np.errstate(all="ignore"):
        ref = c.view(np.float32).astype(np.float16)
    packed = np.asarray(pack_half2(c)).view(np.uint16).reshape(ref.shape)
    keep = ~np.isnan(ref)
    np.testing.assert_array_equal(packed[keep], ref.view(np.uint16)[keep])
    assert np.all(np.isnan(packed.view(np.float16)[~keep]))
