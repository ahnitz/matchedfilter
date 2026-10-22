"""Print a GitHub Actions error annotation for a failed sanitizer run's log.

    python3 tools/sanitize_report.py LOG RC

The annotation leads with what matters when a shard fails: the sanitizer report (the
AddressSanitizer ERROR block, or UndefinedBehaviorSanitizer's "runtime error" lines with
the stack that follows) or, for another abort, the lines before faulthandler's "Fatal
Python error"; then the test faulthandler shows running, then the end of the log.
The public API shows annotations; the job log needs a token.
"""
import re
import sys


def summary(text, limit=3800):
    lines = text.splitlines()
    parts = []
    for i, line in enumerate(lines):
        if "ERROR: AddressSanitizer" in line or "runtime error:" in line:
            parts.append("\n".join(lines[max(0, i - 2): i + 40]))
            break
    else:
        # No sanitizer report: an abort() of another kind (an assert, a library check)
        # prints its message just before faulthandler's "Fatal Python error".
        for i, line in enumerate(lines):
            if line.startswith("Fatal Python error"):
                parts.append("before the abort:\n" + "\n".join(lines[max(0, i - 30): i + 2]))
                break
    test = [l for l in lines if re.search(r"File .*/tests/test_\w+\.py", l)]
    if test:
        parts.append("test frames:\n" + "\n".join(test[:6]))
    head = "\n--\n".join(parts)
    tail = text[-max(0, limit - len(head) - 20):] if len(head) < limit else ""
    return (head + "\n-- end of log --\n" + tail)[:limit]


if __name__ == "__main__":
    log, rc = sys.argv[1], sys.argv[2]
    body = summary(open(log, errors="replace").read())
    esc = body.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print("::error::rc=%s%%0A%s" % (rc, esc))
