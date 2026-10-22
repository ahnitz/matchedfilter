"""Write docs/environment.md from the registry in python/matchedfilter/_config.py.

    python3 tools/gen_environment_doc.py           # rewrite the document
    python3 tools/gen_environment_doc.py --check   # exit 1 if it is stale

tests/test_config_registry.py runs the check.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "environment.md"


def registry():
    """_config loaded by path: it imports nothing, so neither the package nor its
    extension need to be built."""
    spec = importlib.util.spec_from_file_location(
        "_mf_config", ROOT / "python" / "matchedfilter" / "_config.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses resolves annotations through it
    spec.loader.exec_module(mod)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    text = registry().markdown()
    if args.check:
        if not DOC.exists() or DOC.read_text() != text:
            print("%s is stale: run python3 tools/gen_environment_doc.py" % DOC.relative_to(ROOT))
            return 1
        return 0
    DOC.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
