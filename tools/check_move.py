#!/usr/bin/env python3
"""A move is behaviour-neutral: every definition at a base revision is still in the package,
unchanged, wherever it now lives (robustness-plan E1; delete this tool after E3).

    python3 tools/check_move.py [--base REV] [--allow NAME ...]

Every top-level function and class of python/matchedfilter/*.py at REV (default HEAD), and
every method of those classes, must exist in the working tree's package with the same
syntax tree (docstrings included; the module it lives in may differ). Prints what is
missing or changed and exits 1 if anything is; NAME (a "module:qualname" or "qualname")
excuses one deliberate change.
"""
import argparse
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "python/matchedfilter"


def definitions(sources):
    """{qualname: [(module, ast dump), ...]} of top-level functions and classes and the
    methods of those classes, from {module: source}."""
    out = {}
    for module, src in sources.items():
        for node in ast.parse(src).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.setdefault(node.name, []).append((module, ast.dump(node)))
                if isinstance(node, ast.ClassDef):
                    for sub in node.body:
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            out.setdefault(node.name + "." + sub.name, []).append(
                                (module, ast.dump(sub)))
    return out


def at_revision(rev):
    names = subprocess.run(["git", "ls-tree", "--name-only", rev, PKG + "/"], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.split()
    return {Path(n).stem: subprocess.run(["git", "show", "%s:%s" % (rev, n)], cwd=ROOT,
                                         capture_output=True, text=True, check=True).stdout
            for n in names if n.endswith(".py")}


def in_tree():
    return {p.stem: p.read_text() for p in (ROOT / PKG).glob("*.py")}


def compare(old, new, allow=()):
    """[(qualname, old module, problem)] for every old definition that is not unchanged in
    the new package."""
    problems = []
    for name, defs in sorted(old.items()):
        for module, dump in defs:
            if name in allow or "%s:%s" % (module, name) in allow:
                continue
            here = new.get(name, [])
            if any(d == dump for _, d in here):
                continue
            problems.append((name, module, "changed" if here else "missing"))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--allow", nargs="*", default=())
    a = ap.parse_args(argv)
    problems = compare(definitions(at_revision(a.base)), definitions(in_tree()), set(a.allow))
    for name, module, what in problems:
        print("%-8s %s (was in %s)" % (what, name, module))
    print("check_move: %d definitions %s" % (len(problems), "differ" if problems else
                                             "differ; every one is where a move put it"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
