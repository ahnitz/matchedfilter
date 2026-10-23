"""Print a GitHub Actions error annotation for a failed sanitizer run's log.

    python3 tools/sanitize_report.py LOG RC
    python3 tools/sanitize_report.py --crashing-test LOG    # the test running at a crash

With pytest -v the log names each test as it starts, so a crash is placed even when no
stack names it. The annotation leads with what matters when a shard fails: the crashing
test; the failed tests (pytest -rfE) and their messages (the "E" lines); the sanitizer report (the AddressSanitizer ERROR
block, or UndefinedBehaviorSanitizer's "runtime error" lines with the stack that follows),
interpreter frames dropped, or, for another abort, the lines before faulthandler's "Fatal
Python error"; the test frames faulthandler shows; the gdb re-run's stack and registers and
the re-run without the fake stack; then the end of the log.
The public API shows annotations; the job log needs a token.
"""
import re
import sys


#: The outcomes pytest -v prints after a test's node id.
OUTCOMES = ("PASSED", "FAILED", "SKIPPED", "XFAIL", "XPASS", "ERROR")


def crashing_test(text):
    """The pytest node (tests/test_x.py::test_y) running at a crash, or None: the one
    faulthandler shows, else the last node id pytest -v printed with no outcome after it
    (under ASan, ASan's abort handler runs instead of faulthandler's)."""
    m = re.findall(r'File "[^"]*/(tests/test_\w+\.py)", line \d+ in (test_\w+)', text)
    if m:
        return "%s::%s" % m[0]
    started = re.findall(r"^(tests/test_\w+\.py::\S+)(.*)$", text, re.M)
    if started and not any(o in started[-1][1] for o in OUTCOMES):
        return started[-1][0]
    return None


#: Stack frames inside the Python interpreter: they fill an annotation and name nothing of ours.
INTERPRETER = re.compile(r"^\s*#\d+ .*(Objects/|Python/|Include/|Modules/|libpython)")


def summary(text, limit=3800):
    lines = text.splitlines()
    parts = []
    node = crashing_test(text)
    if node:
        parts.append("crashing test: " + node)
    failed = [l for l in lines if l.startswith(("FAILED ", "ERROR "))]
    if failed:
        parts.append("\n".join(failed[:12]))
        # pytest's "E   " lines: the failures' messages, which the one-line summary cuts
        # (a CI-only failure is diagnosed from what its assertion reports).
        errs = [l for l in lines if l.startswith("E   ")]
        if errs:
            parts.append("failure messages:\n" + "\n".join(errs[:40]))
    for i, line in enumerate(lines):
        if "ERROR: AddressSanitizer" in line or "runtime error:" in line:
            block = [l for l in lines[max(0, i - 2): i + 60] if not INTERPRETER.search(l)]
            parts.append("\n".join(block[:24]))
            break
    else:
        # No sanitizer report: an abort() of another kind (an assert, a library check)
        # prints its message just before faulthandler's stack, whose first line ends
        # "(most recent call first):" (its "Fatal Python error" line can land after it).
        for i, line in enumerate(lines):
            if "most recent call first" in line:
                parts.append("before the abort:\n" + "\n".join(lines[max(0, i - 30): i + 1]))
                break
    test = [l for l in lines if re.search(r"File .*/tests/test_\w+\.py", l)]
    if test:
        parts.append("test frames:\n" + "\n".join(test[:6]))
    parts += [l for l in lines if l.startswith("=== without use-after-return detection")]
    gdb = [i for i, l in enumerate(lines) if l.startswith("=== gdb: ")]
    if gdb:
        g = [l for l in lines[gdb[-1]:] if not INTERPRETER.search(l)]
        parts.append("\n".join(g[:40]))
    head = "\n--\n".join(parts)
    tail = text[-max(0, limit - len(head) - 20):] if len(head) < limit else ""
    return (head + "\n-- end of log --\n" + tail)[:limit]


if __name__ == "__main__":
    if sys.argv[1] == "--crashing-test":
        node = crashing_test(open(sys.argv[2], errors="replace").read())
        print(node or "")
        sys.exit(0 if node else 1)
    log, rc = sys.argv[1], sys.argv[2]
    body = summary(open(log, errors="replace").read())
    esc = body.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print("::error::rc=%s%%0A%s" % (rc, esc))
