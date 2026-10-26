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


def _outside():
    """Text of the tools, builds and tests (their names may sit in prose or a shell line)."""
    paths = (sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "tools").glob("*.sh"))
             + sorted((ROOT / "tests").glob("*.py")) + [ROOT / "setup.py"])
    return "\n".join(p.read_text(errors="replace") for p in paths if p.exists())


def test_everything_registered_is_read_where_it_says():
    py, c = _names(_python()), _names(_c())
    outside = _outside()
    wrong = []
    for v in config.VARS:
        if v.side == "tools":
            if v.name in py or v.name in c or not re.search(r"\b%s\b" % v.name, outside):
                wrong.append((v.name, v.side, v.name in py, v.name in c))
            continue
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
        assert v.section in dict(config.SECTIONS) and v.side in ("py", "c", "both", "tools")
        assert (v.section == "tools") == (v.side == "tools"), v.name
        if v.row is None:
            assert v.doc, "%s has no description" % v.name
        else:
            owner = config.BY_NAME[v.row]
            assert owner.row is None and owner.section == v.section, v.name


def test_the_document_is_generated_from_the_registry():
    assert gen.main(["--check"]) == 0, "docs/environment.md is stale"


@pytest.mark.parametrize("raw,want", [("", True), ("  ", True), ("1", True), ("yes", True),
                                      ("On", True), (" TRUE ", True), ("0", False),
                                      ("false", False), ("no", False), ("OFF", False)])
def test_a_flag_follows_the_one_rule(raw, want):
    assert config.parse(config.BY_NAME["MF_AUTOTUNE"], raw) is want


#: A float variable for the parsing rule (the registry has none at present).
_FLOAT = config.Var("MF_TEST_FLOAT", "override", "py", kind="float")


@pytest.mark.parametrize("name,raw", [("MF_AUTOTUNE", "2"), ("MF_AUTOTUNE", "enabled"),
                                      ("MF_GPU_QUEUE_AHEAD", "8.5"), ("MF_TEST_FLOAT", "x"),
                                      ("MF_METAL_IEEE", "fast")])
def test_anything_else_is_refused_by_name(name, raw):
    with pytest.raises(ValueError, match="%s=%s" % (name, re.escape(raw))):
        config.parse(_FLOAT if name == "MF_TEST_FLOAT" else config.BY_NAME[name], raw)


def test_values_and_defaults_by_kind():
    v = config.BY_NAME
    assert config.parse(v["MF_GPU_QUEUE_AHEAD"], "") == 8
    assert config.parse(v["MF_GPU_QUEUE_AHEAD"], " 3 ") == 3
    assert config.parse(_FLOAT, "") is None
    assert config.parse(_FLOAT, "1.25") == 1.25
    assert config.parse(v["MF_BAND_FORWARD"], "") is None      # unset: measured
    assert config.parse(v["MF_METAL_IEEE"], "ALL") == "all"
    assert config.parse(v["MF_CHAIN_FORCE"], "256,512") == "256,512"


def test_removed_and_misspelled_names_warn_and_invalid_values_raise():
    with pytest.warns(RuntimeWarning, match="MF_BBLK was removed on 2026-10-22"):
        config.check_environment({"MF_BBLK": "2"})
    with pytest.warns(RuntimeWarning, match="did you mean MF_AUTOTUNE"):
        config.check_environment({"MF_AUTOTUNES": "0"})
    with pytest.raises(ValueError, match="MF_GPU_ITEMS=maybe"):
        config.check_environment({"MF_GPU_ITEMS": "maybe"})
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config.check_environment({"MF_AUTOTUNE": "off", "PATH": "/bin"})


def test_an_invalid_value_fails_the_import():
    import os
    import subprocess
    import sys
    import matchedfilter as mf
    from conftest import scaled
    parent = os.path.dirname(os.path.dirname(os.path.abspath(mf.__file__)))
    p = subprocess.run([sys.executable, "-c", "import matchedfilter"], capture_output=True,
                       text=True, timeout=scaled(120),
                       env=dict(os.environ, PYTHONPATH=parent, MF_DIRECT_REFINE="nope"))
    assert p.returncode == 1 and "ValueError: MF_DIRECT_REFINE=nope" in p.stderr, p.stderr[-500:]
