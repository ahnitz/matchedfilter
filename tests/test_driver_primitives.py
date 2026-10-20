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
