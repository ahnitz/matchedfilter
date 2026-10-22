"""Every tool and example imports and names only what exists.

Until 2026-10-22 tools/audit_threshold.py imported hmf_tune, folded into tests/_gatelib.py
months before; score_fdr.py, bench_stages.py and bench_coarse_quality.py (since removed) found tests/ only
from the checkout root; verify_cuda.py and bench_pack_indexing.py ran their whole body on
import. Nothing ran them, so nothing said.

Each file is imported by path in one separate interpreter started outside the checkout
(so a tool that finds tests/ only from the root fails), with its own directory on the
path; sys.path, sys.argv and the helpers it loaded from tools/ or tests/ are restored
between files, so each must find its own. No tool imports a third-party
module but numpy at module level, so any failure to import is a broken tool.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import matchedfilter as mf

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "examples").glob("*.py"))
if not (ROOT / "tools").is_dir():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)

DRIVER = r"""
import importlib.util, io, json, sys, traceback, contextlib
files, local = json.loads(sys.argv[1]), tuple(json.loads(sys.argv[2]))
out = {}
for path in files:
    saved_path, saved_argv = list(sys.path), list(sys.argv)
    before = set(sys.modules)
    sys.path[:0] = [path.rsplit("/", 1)[0]]
    sys.argv = [path]
    name = "_repo_tool_" + path.rsplit("/", 1)[1][:-3]
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
        out[path] = ["ok", ""]
    except BaseException:
        out[path] = ["fail", traceback.format_exc(limit=4)[-1500:]]
    finally:
        sys.path[:], sys.argv = saved_path, saved_argv
        # Forget helpers this file loaded from tools/ or tests/: the next file must find
        # them itself, not through this one's import.
        for m in set(sys.modules) - before:
            if (getattr(sys.modules[m], "__file__", None) or "").startswith(local):
                del sys.modules[m]
print(json.dumps(out))
"""


@pytest.fixture(scope="module")
def imported(tmp_path_factory):
    parent = os.path.dirname(os.path.dirname(os.path.abspath(mf.__file__)))
    env = dict(os.environ, PYTHONPATH=parent, OMP_NUM_THREADS="1")
    local = [str(ROOT / d) + os.sep for d in ("tools", "tests", "examples")]
    p = subprocess.run([sys.executable, "-c", DRIVER, json.dumps([str(f) for f in FILES]),
                        json.dumps(local)],
                       capture_output=True, text=True, timeout=600, env=env,
                       stdin=subprocess.DEVNULL, cwd=str(tmp_path_factory.mktemp("cwd")))
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("path", FILES, ids=lambda p: "%s/%s" % (p.parent.name, p.name))
def test_imports(path, imported):
    verdict, detail = imported[str(path)]
    assert verdict == "ok", detail


def test_names_resolve():
    """No undefined name in any tool or example (pyflakes, where it is installed)."""
    pytest.importorskip("pyflakes")
    from pyflakes import api, messages, reporter
    found = []

    class Collect(reporter.Reporter):
        def __init__(self):
            super().__init__(sys.stdout, sys.stderr)

        def flake(self, message):
            if isinstance(message, (messages.UndefinedName, messages.UndefinedLocal,
                                    messages.UndefinedExport)):
                found.append(str(message))

        def syntaxError(self, filename, msg, lineno, offset, text):
            found.append("%s:%s: %s" % (filename, lineno, msg))

    rep = Collect()
    for path in FILES:
        api.checkPath(str(path), rep)
    assert not found, "\n".join(found)
