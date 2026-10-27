"""The library is pyflakes-clean: no unused import, unused local, redefinition or undefined
name anywhere in python/matchedfilter.

Until 2026-10-27 pyflakes reported 143 warnings there: imports left behind when code moved
between modules, re-exports of private names that callers could reach in their own
modules, and locals computed and dropped. None was a live bug, but 143 lines of noise hide
the one that is. A name a module keeps for its callers is bound where pyflakes sees it
(gatechain assigns its cost-file names, as it does _SIG); pyflakes ignores ``# noqa``, so
a comment does not make an import clean. Skipped where pyflakes is not installed; CI
installs it with the test extra.
"""
import io
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "python" / "matchedfilter"


def test_the_library_is_pyflakes_clean():
    pytest.importorskip("pyflakes")
    from pyflakes import api, reporter
    if not PKG.is_dir():
        pytest.skip("the library's source tree is not next to the tests")
    files = sorted(PKG.rglob("*.py"))
    assert files, PKG
    out, err = io.StringIO(), io.StringIO()
    rep = reporter.Reporter(out, err)
    count = sum(api.checkPath(str(path), rep) for path in files)
    found = (out.getvalue() + err.getvalue()).strip()
    assert count == 0 and not found, "%d pyflakes warnings:\n%s" % (count, found)
