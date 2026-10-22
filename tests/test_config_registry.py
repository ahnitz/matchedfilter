"""The environment-variable registry (_config.VARS), the code and docs/environment.md agree:
every MF_* name the package or its C reads is registered, everything registered is read
by the side it says, and the document is the one the registry renders."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec_path = ROOT / "tools" / "gen_environment_doc.py"
if not spec_path.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)

import importlib.util                                                      # noqa: E402
_spec = importlib.util.spec_from_file_location("gen_environment_doc", spec_path)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)
config = gen.registry()

LITERAL = re.compile(r"""["'](MF_[A-Z0-9_]+)["']""")


def _names(paths):
    """{name: [file, ...]} of the MF_* string literals in these files."""
    out = {}
    for p in paths:
        for name in LITERAL.findall(p.read_text(errors="replace")):
            out.setdefault(name, []).append(p.name)
    return out


def _python():
    return [p for p in (ROOT / "python" / "matchedfilter").glob("*.py") if p.name != "_config.py"]


def _c():
    return (sorted((ROOT / "src").glob("*.c")) + sorted((ROOT / "src").glob("*.cc"))
            + sorted((ROOT / "src").glob("*.h"))
            + [ROOT / "python" / "matchedfilter" / "_core.c"])


def test_every_name_the_code_reads_is_registered():
    seen = {**_names(_python()), **_names(_c())}
    unknown = {k: v for k, v in seen.items()
               if k not in config.BY_NAME and k not in config.SHADER_MACROS}
    assert not unknown, "unregistered MF_* names (add them to _config.VARS): %r" % unknown


def test_everything_registered_is_read_where_it_says():
    py, c = _names(_python()), _names(_c())
    wrong = []
    for v in config.VARS:
        want = {"py": [py], "c": [c], "both": [py, c]}[v.side]
        if not all(v.name in names for names in want):
            wrong.append((v.name, v.side, v.name in py, v.name in c))
    assert not wrong, "(name, side, read by Python, read by C): %r" % wrong


def test_the_registry_is_well_formed():
    names = [v.name for v in config.VARS]
    assert len(names) == len(set(names))
    assert not set(names) & config.SHADER_MACROS
    removed = {n for _, _, group in config.REMOVED for n in group}
    assert not set(names) & removed, "a removed name is still registered"
    for v in config.VARS:
        assert v.section in dict(config.SECTIONS) and v.side in ("py", "c", "both")
        if v.row is None:
            assert v.doc, "%s has no description" % v.name
        else:
            owner = config.BY_NAME[v.row]
            assert owner.row is None and owner.section == v.section, v.name


def test_the_document_is_generated_from_the_registry():
    assert gen.main(["--check"]) == 0, "docs/environment.md is stale"
