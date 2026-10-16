#!/usr/bin/env python
"""Production coverage: which library code the production ladder runs.

    tools/ladder_coverage.py [--modes batched,pipeline] [--out DIR] -- <ladder.py arguments>

Runs tools/ladder.py once per mode under coverage (the `coverage` package, importable from
this interpreter), measuring the matchedfilter package only, then prints each module's
covered fraction and every function or method no mode executed. Those functions are the
deletion candidates of docs/convergence-plan.md: code no backend's production run reaches is
either removed or kept with a test that says why.

Run it on each backend's machine (the ladder's --device chooses the backend); the CPU is
--device cpu. A function listed here may still be reached by a production consumer the
ladder does not imitate (pycbc's calls), so read the list as candidates, not verdicts.
"""
import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def functions(path):
    """[(qualified name, first body line, last line)] of every function in a module."""
    tree = ast.parse(Path(path).read_text())
    out = []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                body = child.body
                # Skip the docstring: a function whose only executed line is its docstring
                # was never called.
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(getattr(body[0], "value", None), ast.Constant)
                        and isinstance(body[0].value.value, str) and len(body) > 1):
                    body = body[1:]
                out.append((name, body[0].lineno, child.end_lineno))
                walk(child, name + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, prefix + child.name + ".")
    walk(tree, "")
    return out


def main():
    argv = sys.argv[1:]
    if "--" not in argv:
        sys.exit(__doc__)
    i = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="batched,pipeline",
                    help="comma-separated: batched (no flag) and/or pipeline (--pipeline)")
    ap.add_argument("--out", default="ladder_coverage",
                    help="directory for the coverage data files")
    args = ap.parse_args(argv[:i])
    ladder_args = argv[i + 1:]
    try:
        import coverage
    except ImportError:
        sys.exit("ladder_coverage: the coverage package is not importable here")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pkg = ROOT / "python" / "matchedfilter"
    files = []
    for mode in args.modes.split(","):
        data = out / (".coverage." + mode)
        cmd = [sys.executable, "-m", "coverage", "run", "--data-file", str(data),
               "--source", str(pkg), str(ROOT / "tools" / "ladder.py")] + ladder_args
        if mode == "pipeline":
            cmd.append("--pipeline")
        elif mode != "batched":
            sys.exit("ladder_coverage: unknown mode %r" % mode)
        print("== %s" % mode, flush=True)
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "python"),
                                                          env.get("PYTHONPATH")]))
        rc = subprocess.call(cmd, env=env)
        if rc:
            sys.exit("ladder_coverage: the %s ladder failed (rc %d)" % (mode, rc))
        files.append(str(data))
    cov = coverage.Coverage(data_file=str(out / ".coverage"))
    cov.combine(files, keep=True)
    cov.save()
    data = cov.get_data()
    print("\n%-34s %7s %7s" % ("module", "lines", "run"))
    never = []
    for path in sorted(pkg.glob("*.py")):
        try:
            _, statements, _, missing, _ = cov.analysis2(str(path))
        except coverage.CoverageException:
            continue
        run = set(data.lines(str(path)) or ())
        if statements:
            print("%-34s %7d %6.0f%%" % (path.name, len(statements),
                                         100.0 * (len(statements) - len(missing)) / len(statements)))
        stmts = set(statements)
        for name, first, last in functions(path):
            body = [ln for ln in range(first, last + 1) if ln in stmts]
            if body and not run.intersection(body):
                never.append((path.name, name, len(body)))
    print("\nfunctions no mode ran (%d): module, function, statements" % len(never))
    for mod, name, n in sorted(never, key=lambda t: (-t[2], t[0], t[1])):
        print("  %-26s %-56s %5d" % (mod, name, n))


if __name__ == "__main__":
    main()
