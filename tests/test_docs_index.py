"""docs/README.md lists every document in docs/, and every link it has resolves. Until
2026-10-22 it listed half of them: the environment reference, the active plans and the
search design were reachable only by knowing their names."""
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[1] / "docs"
if not (DOCS / "README.md").exists():
    pytest.skip("docs/ is not shipped here", allow_module_level=True)
INDEX = (DOCS / "README.md").read_text()
LINKS = re.findall(r"\]\(([^)#\s]+)", INDEX)


def test_every_document_is_listed():
    listed = {Path(l).name for l in LINKS if "/" not in l}
    missing = sorted(p.name for p in DOCS.glob("*.md") if p.name != "README.md"
                     and p.name not in listed)
    assert not missing, "not in docs/README.md: %s" % ", ".join(missing)


def test_every_link_resolves():
    broken = [l for l in LINKS if not l.startswith("http") and not (DOCS / l).exists()]
    assert not broken, broken


def test_every_tool_is_listed_in_the_tools_map():
    tools = DOCS.parent / "tools"
    readme = (tools / "README.md").read_text()
    missing = sorted(p.name for p in list(tools.glob("*.py")) + list(tools.glob("*.sh"))
                     if "`%s`" % p.name not in readme)
    assert not missing, "not in tools/README.md: %s" % ", ".join(missing)
