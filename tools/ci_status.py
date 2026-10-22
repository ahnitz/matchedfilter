#!/usr/bin/env python
"""What GitHub Actions says about a commit, a branch or main, through the public API.

    python tools/ci_status.py                      # main's latest run of each workflow
    python tools/ci_status.py --sha 8a33d64a       # every workflow's run for one commit
    python tools/ci_status.py --branch ci/a1       # the latest runs on a proof branch
    python tools/ci_status.py --schedules          # also each scheduled workflow's last run
    python tools/ci_status.py --sha SHA --workflow CI --wait 3600   # the release's check

One verdict line per workflow run, and for a failed run one line per failed job naming
its failed steps and the first lines of its error annotations (the logs need a signed-in
download; annotations do not). A scheduled workflow is red when its latest scheduled run
did not succeed, or when that run is older than two periods plus 6 h (a schedule that
stopped running is as bad as one that fails). A red schedule is cleared by a newer
successful run of the same workflow pushed to a ci/** proof branch: the fix, proven.

Exit status: 0 when everything judged is green, 1 when anything is red, 2 when the answer
is unknown (a run still in progress, no run at all, the API unreachable or rate-limited).
An unknown is never reported as green.

A token raises the API's rate limit from 60 to 5000 requests an hour: GH_TOKEN or
GITHUB_TOKEN from the environment, else the file ~/.config/mf-ci/token. A read-only token
(Actions: read) is enough. Without one the public limit applies.
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "ahnitz/matchedfilter"
API = "https://api.github.com/repos/" + REPO
GREEN = "success"


class Unknown(Exception):
    """The API could not answer (network, rate limit, permissions)."""


def _token():
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok.strip()
    path = Path.home() / ".config" / "mf-ci" / "token"
    try:
        return path.read_text().strip() or None
    except OSError:
        return None


def get(path, token=None):
    """GET API + path as JSON; raises Unknown on any failure to answer."""
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise Unknown("HTTP %d for %s%s" % (e.code, path,
                      " (rate limit reached)" if e.code in (403, 429) else ""))
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Unknown("%s for %s" % (e, path))


def latest_per_workflow(runs):
    """The newest run (and newest attempt) of each workflow name, in name order."""
    best = {}
    for r in runs:
        key = r["name"]
        rank = (r.get("created_at", ""), r.get("run_attempt", 1))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    return [best[k][1] for k in sorted(best)]


def verdict(run):
    """'green', 'red' or 'unknown' for one run."""
    if run.get("status") != "completed":
        return "unknown"
    return "green" if run.get("conclusion") == GREEN else (
        "green" if run.get("conclusion") == "skipped" else "red")


def _parse_time(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def schedule_period(cron):
    """Seconds between runs of a five-field cron line: weekly when it names weekdays,
    monthly when it names days of the month, else daily."""
    fields = cron.split()
    if len(fields) != 5:
        raise ValueError("not a five-field cron line: %r" % cron)
    if fields[4] != "*":
        return 7 * 86400
    if fields[2] != "*":
        return 31 * 86400
    return 86400


def schedule_verdict(run, period, now):
    """('green'|'red'|'unknown', detail) for a workflow's latest scheduled run."""
    if run is None:
        return "unknown", "no scheduled run yet"
    v = verdict(run)
    age = (now - _parse_time(run["created_at"])).total_seconds()
    if v == "green" and age > 2 * period + 6 * 3600:
        return "red", "last scheduled run is %.1f days old (period %.0f days)" % (
            age / 86400, period / 86400)
    return v, "%s, %.1f days ago" % (run.get("conclusion") or run.get("status"), age / 86400)


def cleared_by(sched_run, proofs):
    """The newest successful proof run (ci/** push) of the same workflow created after the
    red scheduled run, or None."""
    after = [r for r in proofs if r["name"] == sched_run["name"]
             and r.get("head_branch", "").startswith("ci/") and verdict(r) == "green"
             and r["created_at"] > sched_run["created_at"]]
    return max(after, key=lambda r: r["created_at"]) if after else None


def failed_jobs(run, token):
    """[(job name, [failed step names], [annotation lines])] of a red run."""
    out = []
    jobs = get("/actions/runs/%d/jobs?per_page=100" % run["id"], token).get("jobs", [])
    for j in jobs:
        if j.get("conclusion") not in ("failure", "timed_out", "cancelled"):
            continue
        steps = [s["name"] for s in j.get("steps", []) if s.get("conclusion") == "failure"]
        notes = []
        try:
            for a in get("/check-runs/%d/annotations" % j["id"], token):
                if a.get("annotation_level") == "failure":
                    msg = (a.get("title") or "") + ": " + (a.get("message") or "").splitlines()[0]
                    notes.append(msg[:200])
        except Unknown:
            pass
        out.append((j["name"], j.get("conclusion"), steps, notes[:5]))
    return out


def report(runs, token, out=sys.stdout):
    """Print one line per run (and its failed jobs); returns the worst verdict."""
    worst = "green"
    for r in runs:
        v = verdict(r)
        print("%-7s %-12s %-24s %s %s" % (v, r.get("head_branch", "")[:12], r["name"][:24],
                                          r["head_sha"][:8], r.get("html_url", "")), file=out)
        if v == "red":
            for name, concl, steps, notes in failed_jobs(r, token):
                print("          %s: %s in %s" % (name, concl, ", ".join(steps) or "(no step)"),
                      file=out)
                for n in notes:
                    print("            %s" % n, file=out)
        worst = _worse(worst, v)
    return worst


def _worse(a, b):
    order = {"green": 0, "unknown": 1, "red": 2}
    return a if order[a] >= order[b] else b


def scheduled_workflows(root):
    """{workflow name: cron line} of the workflows in .github/workflows that have one."""
    import re
    out = {}
    for p in sorted((Path(root) / ".github" / "workflows").glob("*.yml")):
        text = p.read_text()
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        cron = re.search(r"cron:\s*[\"']([^\"']+)[\"']", text)
        if name and cron:
            out[name.group(1).strip()] = cron.group(1)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sel = ap.add_mutually_exclusive_group()
    sel.add_argument("--sha", help="judge every workflow's run for this commit")
    sel.add_argument("--branch", help="judge the latest runs on this branch")
    ap.add_argument("--workflow", help="only this workflow (its name, e.g. CI)")
    ap.add_argument("--schedules", action="store_true",
                    help="also judge each scheduled workflow's latest scheduled run")
    ap.add_argument("--wait", type=float, default=0,
                    help="poll up to this many seconds while a judged run is in progress")
    args = ap.parse_args(argv)
    token = _token()
    root = Path(__file__).resolve().parent.parent
    deadline = time.time() + args.wait
    while True:
        try:
            if args.sha:
                sha = args.sha
                if len(sha) < 40:
                    sha = get("/commits/" + sha, token)["sha"]
                runs = get("/actions/runs?head_sha=%s&per_page=100" % sha, token)["workflow_runs"]
                runs = [r for r in runs if r.get("event") in ("push", "workflow_dispatch")]
            else:
                branch = args.branch or "main"
                runs = get("/actions/runs?branch=%s&event=push&per_page=50" % branch,
                           token)["workflow_runs"]
            runs = latest_per_workflow(runs)
            if args.workflow:
                runs = [r for r in runs if r["name"] == args.workflow]
            if any(verdict(r) == "unknown" for r in runs) and time.time() < deadline:
                time.sleep(60)
                continue
            worst = report(runs, token) if runs else "unknown"
            if not runs:
                print("unknown no %s run found" % (args.workflow or "workflow"))
            if args.schedules:
                now = datetime.datetime.now(datetime.timezone.utc)
                sruns = get("/actions/runs?event=schedule&per_page=50", token)["workflow_runs"]
                proofs = None
                for name, cron in scheduled_workflows(root).items():
                    mine = latest_per_workflow([r for r in sruns if r["name"] == name])
                    v, detail = schedule_verdict(mine[0] if mine else None,
                                                 schedule_period(cron), now)
                    if v == "red" and mine:
                        if proofs is None:
                            proofs = get("/actions/runs?event=push&per_page=100",
                                         token)["workflow_runs"]
                        fix = cleared_by(mine[0], proofs)
                        if fix is not None:
                            v, detail = "green", "%s; cleared by %s on %s (%s)" % (
                                detail, fix["head_sha"][:8], fix["head_branch"], fix["html_url"])
                    print("%-7s schedule     %-24s %s" % (v, name[:24], detail))
                    worst = _worse(worst, v)
        except Unknown as e:
            print("unknown %s" % e)
            return 2
        break
    if not token:
        print("(no token: public rate limit)")
    return {"green": 0, "red": 1, "unknown": 2}[worst]


if __name__ == "__main__":
    sys.exit(main())
