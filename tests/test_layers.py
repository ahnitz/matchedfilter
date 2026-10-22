"""The package's modules import one way: down the layers below (robustness-plan E).

A module may import from its own layer or any below it. An upward import -- at module
level or inside a function, including ``from . import name`` for a name the package root
defines -- is allowed only while it is in UPWARD, which was seeded on 2026-10-22 from the
imports of the day and only shrinks: the test fails on a new upward import and on an
entry that is no longer needed, so each move that removes one also removes its entry.
"""
import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "python" / "matchedfilter"

#: Compiled extension modules: below every Python module.
EXTENSIONS = {"_core"}

#: Lowest first. A module not listed fails the test (place it when adding it).
LAYERS = (
    ("foundation", {"_config", "_errors", "_kernel_dirs", "_kernel_id", "_series", "_gpu_cache",
                    "_gputime", "_coarse", "_shared", "_execution_policy", "_choice",
                    "_costfile", "_results"}),
    ("platform", {"_cuda", "_metal", "_vulkan", "device", "_vksubgroup"}),
    ("models", {"gatemodel", "gatechain", "_chains", "_prices"}),
    ("gpu host", {"_gpuhost", "_gpuhier", "_gpuexec"}),
    ("backends", {"_vkcompute", "_cudacompute", "_mtlcompute"}),
    ("workloads", {"time_domain", "search", "_roofline", "__init__", "_layout", "_filter",
                   "_hierarchical"}),
    ("applications", {"benchmark", "tutorial", "demo", "precision"}),
)
LEVEL = {m: i for i, (_, mods) in enumerate(LAYERS) for m in mods}
LEVEL.update({m: -1 for m in EXTENSIONS})

#: (importer, imported) upward edges still allowed. Remove an entry when its import goes.
UPWARD = {
    ('_cudacompute', '_roofline'),
    ('_gpuhost', 'time_domain'),
    ('_mtlcompute', '_roofline'), ('_vkcompute', '_roofline'),
    ('_vksubgroup', 'gatechain'), ('device', '__init__'),
    ('gatechain', '__init__'),
}


def _edges():
    """{(importer, imported)} of the package's own modules, at any depth."""
    mods = {p.stem for p in PKG.glob("*.py")} | EXTENSIONS
    out = set()
    for path in PKG.glob("*.py"):
        me = path.stem
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ImportFrom) or node.level != 1:
                continue
            if node.module:
                targets = [node.module.split(".")[0]]
            else:                             # from . import a, b: modules, or the root's names
                targets = [a.name if a.name in mods else "__init__" for a in node.names]
            out.update((me, t) for t in targets if t != me and t in mods)
    return out


def test_every_module_has_a_layer():
    missing = sorted({p.stem for p in PKG.glob("*.py")} - set(LEVEL))
    assert not missing, "place these modules in LAYERS: %s" % missing


def test_imports_go_down_the_layers():
    upward = {(a, b) for a, b in _edges() if a in LEVEL and b in LEVEL and LEVEL[b] > LEVEL[a]}
    new = sorted(upward - UPWARD)
    assert not new, "upward imports (import down, or move the code): %s" % new


def test_the_allowlist_only_shrinks():
    upward = {(a, b) for a, b in _edges() if a in LEVEL and b in LEVEL and LEVEL[b] > LEVEL[a]}
    stale = sorted(UPWARD - upward)
    assert not stale, "these upward imports are gone: remove them from UPWARD: %s" % stale
