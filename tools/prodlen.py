#!/usr/bin/env python3
"""Production-length vetting: fresh ladder processes of two trees, interleaved, with every
measured choice's lock and the fine batch it locked at.

    python tools/prodlen.py run --base ../main --new . --processes 4 --out runs/ \\
        --bank BANK.hdf --profiles PROFILES.npz --device gpu:0 --cores 12-15
    python tools/prodlen.py summarise runs/ [--json summary.json]

A production job starts with no MF_COST_FILE, so every measured choice (_choice.Choice: the
GPU device trials, the banks' joint trials, the single-template side, ...) is decided afresh
in each process, on a loaded machine, over the job's own batches. A trial that locks within
a short ladder run can stay open for most of a job, or lock another arm, and a seeded cost
file hides both. This runs the production shape: each tree's own tools/ladder.py with
--tops 27 --segments 28 --pipeline --pure (the defaults), every process fresh, no
MF_COST_FILE, MF_AUTOTUNE_LOG=1.

  * The processes alternate ABBA (base, new, new, base, ...), each pinned to --cores, after
    --warm short unrecorded runs of each tree (a cold shader cache costs minutes in a first
    GPU run; a short run may not reach every kernel the long one uses, and the first
    recorded process's prep shows it if so).
  * Every MF_* and LADDER_* variable of the caller's environment is dropped (--env sets one,
    for both trees, recorded), the BLAS and OpenMP thread counts are 1, PYTHONPATH is the
    tree's python/, and a tree whose extension is older than its C sources is refused.
  * Each process runs its tree's ladder through this file's hook (`prodlen.py hook`), the
    same for both trees: it marks every filter_series_many batch and every measured
    choice's creation, rounds (with their timings) and lock on stderr as JSON lines
    ("[prodlen] {...}"), beside the library's own MF_AUTOTUNE lines, in one log per process.

Per process the summary gives every decision: a measured choice (_choice.Choice), with a
coordinate search counted once. A search's passes are separate choices (the later ones
described as the first plus " around <arm>"); its decision is its last pass's lock, and its
passes are listed under it. For each decision: the lock, the fine batch it locked at (k of
tops x segments, and its top and segment; the ladder's own batches, not the calls a joint
trial's round makes inside one), the fine batches it was open in, the batches it played
(had a round in) and how many of them ran a non-default configuration, the arms it dropped
or picked for confirmation, and the fine batches after a non-default decision. Then the
model-priced chain and block-size picks (made afresh in each process, without rounds), the
steady wall (steady_s) and its per-top series, the process's total, user and system time,
prep and warmup, the load (1-minute average) at start and end and its range over the run,
and the GPU clock the ladder sampled. Pooled: each metric's median per tree and the new/base
ratio (also per ABBA pair); per search how many processes of each tree reached which
decision; each tree's non-default decisions (one per search, however many passes reached
it) and the processes they were in; and the offline kernel screens' and the model-priced
picks (both can differ between processes too). CHECK lines verify what the numbers rest on
(exit status, the hook, the batch counts, every lock seen twice: by the hook and in the
library's log); the exit status is 1 when one fails.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

HOOK = "[prodlen] "
AUTOTUNE = "[MF_AUTOTUNE] "
DEFAULT = "default"          # the arm label of every dimension at its default (_settings.DEFAULT)
#: An offline screen's line (_coarse.shortlist): not a Choice, listed apart.
SCREEN = re.compile(r"^(?P<kind>\S+) (?P<device>.+) band (?P<band>\d+) -> (?P<label>\S+) "
                    r"\(then (?P<alt>\S+)\)")
#: Choice.lock's line: "<what> -> <label>  {<medians>}".
LOCK_LINE = re.compile(r"^(?P<what>.+) -> (?P<label>\S+)  \{.*\}$")
DROP_LINE = re.compile(r"^(?P<what>.+): (?P<label>\S+) cannot win, dropped$")
CONFIRM_LINE = re.compile(r"^(?P<what>.+): (?P<label>\S+) to be confirmed against \S+$")
#: A coordinate search's later pass: the first pass's description, then " around <arm>"
#: (_trial.current_pass: the GPU device trials and the banks' joint trials).
AROUND = re.compile(r"^(?P<root>.+) around (?P<base>\S+)$")
#: The model-priced decisions each process makes afresh, without rounds: a fine bank's
#: chain (_hierarchical) and a bank's block-size partition (time_domain), prices left out.
MODEL_LINES = {"CHAIN": re.compile(r"^CHAIN (?P<pick>n=\d+ model=.+?) ranking="),
               "BLOCK": re.compile(r"^BLOCK (?P<pick>.+? -> n=\d+)(?:  |$)")}
METRICS = ("total", "user", "sys", "prep", "warm", "steady")
SOURCES = (".c", ".cc", ".cpp", ".h", ".hpp")


# ---- the hook: runs inside each ladder process ---------------------------------------------

def hook(argv):
    """`prodlen.py hook LADDER [ladder arguments]`: run LADDER (a tree's tools/ladder.py) in
    this process, with its tree's matchedfilter, emitting the events the summary reads on
    stderr. Returns nothing; exits non-zero if the tree lacks what the hook wraps."""
    import runpy
    ladder = os.path.abspath(argv[0])
    pkg = os.path.join(os.path.dirname(os.path.dirname(ladder)), "python")
    sys.path.insert(0, pkg)
    import matchedfilter
    from matchedfilter import _choice
    if not os.path.abspath(matchedfilter.__file__).startswith(pkg + os.sep):
        sys.exit("prodlen hook: imported %s, not the tree's %s" % (matchedfilter.__file__, pkg))
    C, bank = _choice.Choice, matchedfilter.TimeDomainFilterBank
    missing = [n for n in ("__init__", "round", "lock", "expire") if not callable(getattr(C, n, None))]
    if missing or not callable(getattr(bank, "filter_series_many", None)):
        sys.exit("prodlen hook: this tree has no Choice.%s / filter_series_many to wrap"
                 % "/".join(missing))
    t0 = time.perf_counter()

    def emit(ev, **kw):
        kw = dict(ev=ev, t=round(time.perf_counter() - t0, 4), **kw)
        sys.stderr.write(HOOK + json.dumps(kw, default=str) + "\n")
        sys.stderr.flush()

    def label(ch, c):
        try:
            return str(ch.label(c))
        except Exception:                                   # noqa: BLE001 -- a label never fails a run
            return str(c)

    ids = iter(range(1, 1 << 62))

    def uid(ch):
        if "_prodlen_uid" not in ch.__dict__:
            ch.__dict__["_prodlen_uid"] = next(ids)
        return ch.__dict__["_prodlen_uid"]

    init, rnd, lock, expire = C.__init__, C.round, C.lock, C.expire

    def init_(self, *a, **k):
        init(self, *a, **k)
        held = getattr(self, "held", None)
        emit("choice", id=uid(self), what=str(getattr(self, "what", "?")),
             pref=label(self, self.preference),
             cands=[label(self, c) for c in getattr(self, "candidates", ())],
             held=None if held is None else label(self, held))

    def round_(self, timings, *a, **k):
        if getattr(self, "winner", None) is None:
            arms = list(timings)
            try:                                            # Choice.play shares one timing
                times = [float(timings[c]) for c in arms]   # among arms that run alike
            except (TypeError, ValueError):
                times = None
            emit("round", id=uid(self), arms=[label(self, c) for c in arms], times=times)
        return rnd(self, timings, *a, **k)

    def lock_(self, winner, *a, **k):
        out = lock(self, winner, *a, **k)
        emit("lock", id=uid(self), asked=label(self, winner), label=label(self, self.winner))
        return out

    def expire_(self, *a, **k):
        emit("expire", id=uid(self), attempts=getattr(self, "attempts", None))
        return expire(self, *a, **k)

    C.__init__, C.round, C.lock, C.expire = init_, round_, lock_, expire_
    many = bank.filter_series_many
    count = [0]

    def filter_series_many(jobs, *a, **k):
        if not isinstance(jobs, (list, tuple)):
            jobs = list(jobs)
        i = count[0]
        count[0] += 1
        follow = any(len(j) > 2 and (j[2] or {}).get("template_index") is not None for j in jobs)
        emit("batch", i=i, kind="empty" if not jobs else ("follow" if follow else "fine"),
             n=len(jobs))
        try:
            return many(jobs, *a, **k)
        finally:
            emit("done", i=i)

    bank.filter_series_many = staticmethod(filter_series_many)
    emit("start", matchedfilter=os.path.abspath(matchedfilter.__file__), pid=os.getpid(),
         argv=argv[1:])
    sys.argv = [ladder] + list(argv[1:])
    runpy.run_path(ladder, run_name="__main__")
    emit("exit")


# ---- the log parser ------------------------------------------------------------------------

def parse_log(lines):
    """The events of one process's log, in order. Returns a dict:

      batches   [{i, kind, n, fine, nested}] every outermost filter_series_many call (the
                ladder's: kind fine, follow or empty); fine is a fine batch's 1-based index,
                else None; nested counts the calls made inside it (a joint trial's
                round replays its sub-batches through filter_series_many)
      choices   {id: {what, pref, cands, held, at, rounds: [{at..., arms, times, b}], lock,
                asked, lock_at, expired, drops: [(label, at)], confirms: [(label, at)]}};
                a round's times are its arms' timings (None from an older hook), b the
                index (i) of the outermost batch it was in (None between batches)
      screens   [{kind, device, band, label, alt, at}] offline screens (_coarse.shortlist)
      models    [(kind, pick)] the model-priced CHAIN and BLOCK picks (MODEL_LINES), in order
      lock_lines [(what, label)] Choice.lock's lines in the library's own log
      start     the hook's start record (None if absent); exit: whether the ladder returned

    An `at` is {"fine": k, "in": kind or None, "follow": j}: k fine batches and j follow-up
    batches (kind follow or empty: the ladder makes one per segment, in segment order) had
    begun, and the event happened inside an outermost batch of that kind (None: between
    batches)."""
    out = dict(batches=[], choices={}, screens=[], models=[], lock_lines=[], start=None, exit=False)
    fine, follow, stack, by_what = 0, 0, [], defaultdict(list)

    def at():
        return {"fine": fine, "in": stack[0]["kind"] if stack else None, "follow": follow}

    def latest(what):
        # the most recent choice of that description still open (else the most recent)
        cands = by_what.get(what, [])
        for c in reversed(cands):
            if c["lock"] is None:
                return c
        return cands[-1] if cands else None

    for line in lines:
        line = line.rstrip("\n")
        if line.startswith(HOOK):
            try:
                e = json.loads(line[len(HOOK):])
            except ValueError:
                continue
            ev = e.get("ev")
            if ev == "batch":
                if stack:                                 # a call made inside a batch
                    stack[0]["nested"] += 1
                    stack.append(dict(i=e["i"]))
                    continue
                if e["kind"] == "fine":
                    fine += 1
                else:
                    follow += 1
                b = dict(i=e["i"], kind=e["kind"], n=e["n"], fine=fine if e["kind"] == "fine" else None,
                         nested=0)
                out["batches"].append(b)
                stack.append(b)
            elif ev == "done":
                while stack and stack[-1]["i"] != e["i"]:
                    stack.pop()
                if stack:
                    stack.pop()
            elif ev == "choice":
                c = dict(what=e["what"], pref=e["pref"], cands=e["cands"], held=e.get("held"),
                         at=at(), rounds=[], lock=None, asked=None, lock_at=None, expired=None,
                         drops=[], confirms=[])
                out["choices"][e["id"]] = c
                by_what[e["what"]].append(c)
            elif ev in ("round", "lock", "expire"):
                c = out["choices"].get(e["id"])
                if c is None:
                    continue
                if ev == "round":
                    c["rounds"].append(dict(at(), arms=e["arms"], times=e.get("times"),
                                            b=stack[0]["i"] if stack else None))
                elif ev == "lock":
                    c.update(lock=e["label"], asked=e["asked"], lock_at=at())
                else:
                    c["expired"] = e.get("attempts")
            elif ev == "start":
                out["start"] = e
            elif ev == "exit":
                out["exit"] = True
        elif line.startswith(AUTOTUNE):
            text = line[len(AUTOTUNE):]
            m = SCREEN.match(text)
            if m:
                out["screens"].append(dict(m.groupdict(), band=int(m.group("band")), at=at()))
                continue
            m = LOCK_LINE.match(text)
            if m:
                out["lock_lines"].append((m.group("what"), m.group("label")))
                continue
            kind = text.split(" ", 1)[0]
            m = MODEL_LINES[kind].match(text) if kind in MODEL_LINES else None
            if m:
                out["models"].append((kind, m.group("pick")))
                continue
            for pat, key in ((DROP_LINE, "drops"), (CONFIRM_LINE, "confirms")):
                m = pat.match(text)
                if m:
                    c = latest(m.group("what"))
                    if c is not None:
                        c[key].append((m.group("label"), at()))
                    break
    return out


def nondefault(choice, label):
    """Whether `label` is a non-default arm of `choice` (a parsed choice, or a trials() row):
    any arm but DEFAULT where the choice's arms are labelled against it (a search's first
    pass, and a pass around another arm, all of whose arms are non-default), else any
    candidate but the preference."""
    if label is None:
        return False
    if choice["pref"] == DEFAULT or " around " in choice["what"]:
        return label != DEFAULT
    return label != choice["pref"]


def ran_nondefault(choice, rnd):
    """Whether a round of `choice` ran a non-default configuration: the choice's preference
    is a non-default arm (a pass around another arm), or a non-default arm was timed apart
    from the preference. Choice.play runs the arms that run alike (its config) once and gives
    each of them that one timing, so an arm with the preference's timing ran the
    preference's configuration (two separate runs timed to the same float would be taken
    for one). A round without timings (an older hook's log) counts any non-default arm."""
    pref, arms, times = choice["pref"], rnd["arms"], rnd.get("times")
    if nondefault(choice, pref):
        return True
    if times is None or pref not in arms:
        return any(nondefault(choice, a) for a in arms)
    own = times[arms.index(pref)]
    return any(nondefault(choice, a) and t != own for a, t in zip(arms, times))


def trials(parsed, total_fine):
    """Per measured choice of a parsed log (one Choice: each pass of a coordinate search is
    one), its derived record, in creation order: a list of dicts with its lock and where
    (lock_at), whether that is a non-default arm, the fine batches it was open in (from the
    first fine batch it existed in unlocked to the one that had begun when it locked, or the
    last), its rounds (Choice.round calls), the batches they were in by kind (played) and how
    many of those ran a non-default configuration (ran_nondefault), the fine batches after
    its lock, and its search (the first pass's description) and base (the arm a pass around
    another moves from; None for a first pass)."""
    rows = []
    for cid, c in parsed["choices"].items():
        first = c["at"]["fine"] if c["at"]["in"] == "fine" else c["at"]["fine"] + 1
        if c["held"] is not None and c["lock"] is None:
            first = total_fine + 1                       # held from a cost file: never open
        last = c["lock_at"]["fine"] if c["lock_at"] is not None else total_fine
        batches = {}                                     # the batches its rounds were in
        for j, r in enumerate(c["rounds"]):
            g = batches.setdefault(r["b"] if r.get("b") is not None else ("between", j),
                                   dict(kind=r["in"] or "between", ran=False))
            g["ran"] = g["ran"] or ran_nondefault(c, r)
        m = AROUND.match(c["what"])
        lock = c["lock"] if c["lock"] is not None else c["held"]
        rows.append(dict(
            id=cid, what=c["what"], pref=c["pref"], arms=len(c["cands"]), held=c["held"],
            search=m.group("root") if m else c["what"], base=m.group("base") if m else None,
            lock=lock, lock_at=c["lock_at"], nondefault=nondefault(c, lock),
            open_fine=max(0, last - first + 1), first_open=first, last_open=last,
            rounds=len(c["rounds"]), played=dict(Counter(g["kind"] for g in batches.values())),
            ran_nondefault=sum(g["ran"] for g in batches.values()),
            after_fine=(total_fine - c["lock_at"]["fine"]) if c["lock_at"] is not None else 0,
            expired=c["expired"], drops=c["drops"], confirms=c["confirms"]))
    return rows


def searches(rows):
    """The decisions of a process: its choices (trials() rows) grouped by coordinate search,
    each pass around an arm joining the latest search of its first pass's description. A
    list, in creation order, of dicts with what (the first pass's description), passes (its
    rows), lock (the last pass's lock: the search's decision; None while that pass is open),
    base (what runs between an open search's rounds: its last pass's preference) and
    base_nondefault, lock_at, nondefault (the decision is a non-default arm: counted once,
    however many passes reached it), first_nondefault_at (where a pass first locked a
    non-default arm), open_fine (the fine batches any of its passes was open in), rounds,
    played and ran_nondefault summed over its passes, and after_fine (the fine batches after
    the decision)."""
    out, latest = [], {}
    for r in rows:
        s = latest.get(r["search"]) if r["base"] is not None else None
        if s is None:
            s = latest[r["search"]] = dict(what=r["search"], passes=[])
            out.append(s)
        s["passes"].append(r)
    for s in out:
        ps = s["passes"]
        first, last = ps[0], ps[-1]
        played = Counter()
        for p in ps:
            played.update(p["played"])
        span = set().union(*[range(p["first_open"], p["last_open"] + 1) for p in ps])
        s.update(
            lock=last["lock"], base=last["pref"], base_nondefault=nondefault(first, last["pref"]),
            lock_at=last["lock_at"] if last["lock"] is not None else None,
            nondefault=nondefault(first, last["lock"]),
            first_nondefault_at=next((p["lock_at"] for p in ps if p["lock_at"] is not None
                                      and nondefault(first, p["lock"])), None),
            open_fine=len(span), first_open=min(span, default=None), last_open=max(span, default=None),
            rounds=sum(p["rounds"] for p in ps), played=dict(played),
            ran_nondefault=sum(p["ran_nondefault"] for p in ps),
            after_fine=last["after_fine"] if last["lock"] is not None else 0,
            arms=first["arms"] if len(ps) == 1 else None, held=last["held"], expired=last["expired"],
            drops=first["drops"] if len(ps) == 1 else [], confirms=first["confirms"] if len(ps) == 1 else [])
    return out


def where(at, segments, warmup=None):
    """A location (parse_log's `at`) in words: 'setup' before the first fine batch, else
    'fine k' (k fine batches had begun), then ' follow-ups' inside segment k's follow-up
    batch (', follow-ups of fine j' inside segment j's: with --depth 2 or more the ladder
    collects a segment after later fine batches) or ' +between' outside every batch; then
    '(top t seg s)' of the segment the event belongs to, with ', steady' when that segment
    is past the ladder's warmup segments."""
    if at is None:
        return "-"
    k = j = at["fine"]
    if k == 0:
        return "setup"
    text = " +between"
    if at["in"] == "fine":
        text = ""
    elif at["in"] in ("follow", "empty"):
        j = at.get("follow") or k
        text = " follow-ups" if j == k else ", follow-ups of fine %d" % j
    top, seg = (j - 1) // segments + 1, (j - 1) % segments + 1
    return "fine %d%s (top %d seg %d%s)" % (
        k, text, top, seg, ", steady" if warmup is not None and seg > warmup else "")


def lock_check(parsed):
    """(ok, text): every hook lock has its own Choice.lock line in the library's log, and the
    log has no lock line the hook did not see (each counted once)."""
    hooks = Counter((c["what"], c["lock"]) for c in parsed["choices"].values() if c["lock"] is not None)
    lines = Counter(parsed["lock_lines"])
    missing, extra = hooks - lines, lines - hooks
    ok = not missing and not extra
    return ok, "%d locks by the hook, %d lock lines%s%s" % (
        sum(hooks.values()), sum(lines.values()),
        "; hook only: %s" % dict(missing) if missing else "",
        "; log only: %s" % dict(extra) if extra else "")


# ---- one process's summary -------------------------------------------------------------------

def short(what):
    """A choice's description with a device tuple ('gpu:0 <name>',) shortened to gpu:0."""
    return re.sub(r"\('((?:gpu|cpu):\d+)[^']*',\)", r"\1", what)


def process_summary(run_dir, tag):
    """The summary of one recorded process (tag.meta.json, tag.log, tag.json in run_dir):
    a dict of its metrics, per-top steady series, trials (one row per choice), searches (one
    per decision), screens, model-priced picks ({kind: [pick]}) and checks."""
    d = Path(run_dir)
    meta = json.loads((d / (tag + ".meta.json")).read_text())
    with open(d / (tag + ".log"), errors="replace") as f:
        parsed = parse_log(f)
    rp = d / (tag + ".json")
    report = json.loads(rp.read_text()) if rp.exists() else None
    args = (report or {}).get("meta", {}).get("args", {})
    tops = int(args.get("tops", meta["tops"]))
    segments = int(args.get("segments", meta["segments"]))
    warmup = int(args.get("warmup", 2))
    fine = [b for b in parsed["batches"] if b["kind"] == "fine"]
    follow = [b for b in parsed["batches"] if b["kind"] in ("follow", "empty")]
    first = (report or {}).get("first_segment_s", {})
    steady = (report or {}).get("steady_s", {})
    wall = ((report or {}).get("steady_samples") or {}).get("wall") or []
    per = len(wall) // tops if tops and len(wall) % tops == 0 else 0
    per_top = [sum(wall[j * per:(j + 1) * per]) for j in range(tops)] if per else None
    # the ladder samples the amdgpu clock whatever the device: only a GPU run's is its own
    gs = ((report or {}).get("counts") or {}).get("gpu_sampler") or {} \
        if str((report or {}).get("device", "")).startswith("gpu") else {}
    counts = (report or {}).get("counts") or {}
    rows = trials(parsed, len(fine))
    models = defaultdict(list)
    for kind, pick in parsed["models"]:
        models[kind].append(pick)
    models = dict(models)
    lk_ok, lk_text = lock_check(parsed)
    start = parsed["start"] or {}
    pkg = os.path.join(meta["tree"], "python") + os.sep
    checks = [
        ("exit", meta["rc"] == 0 and report is not None and parsed["exit"],
         "rc=%s%s, report %s, ladder %s" % (meta["rc"], " (timed out)" if meta.get("timed_out") else "",
                                            "written" if report else "missing",
                                            "returned" if parsed["exit"] else "did not return")),
        ("tree", str(start.get("matchedfilter", "")).startswith(pkg),
         "matchedfilter %s" % start.get("matchedfilter")),
        ("fine batches", len(fine) == tops * segments,
         "%d fine batches for %d tops x %d segments" % (len(fine), tops, segments)),
        # where() reads the j-th follow-up batch as segment j's: one per segment
        ("follow-up batches", len(follow) == tops * segments,
         "%d follow-up batches (%d empty) for %d tops x %d segments"
         % (len(follow), sum(b["kind"] == "empty" for b in follow), tops, segments)),
        ("steady series", per_top is not None,
         "%d steady samples over %d tops" % (len(wall), tops)),
        ("locks", lk_ok, lk_text),
    ]
    return dict(
        tag=tag, tree_name=meta["tree_name"], tree=meta["tree"], rev=meta.get("rev"), digest=meta.get("digest"),
        order=meta["order"], start=meta["start"], rc=meta["rc"],
        total=meta["wall"], user=meta["user"], sys=meta["sys"],
        prep=first.get("prep"), warm=first.get("wall"), steady=steady.get("wall"),
        tirt=((report or {}).get("templates_in_real_time") or {}).get("total"),
        load_start=meta["load_start"][0], load_end=meta["load_end"][0],
        load_range=[min(x[1] for x in meta["load_trace"]), max(x[1] for x in meta["load_trace"])]
        if meta["load_trace"] else None,
        sclk=gs.get("sclk_mhz_mean"), busy=gs.get("busy_pct"),
        per_top=per_top, tops=tops, segments=segments, warmup=warmup, fine_batches=len(fine),
        follow_batches=sum(b["kind"] == "follow" for b in parsed["batches"]),
        nested=sum(b["nested"] for b in parsed["batches"]),
        triggers=counts.get("fine_triggers"), asym_calls=counts.get("asym_calls"),
        trials=rows, searches=searches(rows), screens=parsed["screens"], models=models,
        open_any=len(set().union(*[range(r["first_open"], r["last_open"] + 1) for r in rows])) if rows else 0,
        last_open=max([r["last_open"] for r in rows if r["open_fine"]], default=0),
        checks=checks)


def _num(v, fmt="%.1f"):
    return "-" if v is None else fmt % v


def format_process(s):
    """One process's summary as text lines."""
    L = ["%s %-4s rc=%s total %s s user %s s sys %s s | load %s -> %s (range %s) | prep %s s "
         "warm %s s steady %s s | tirt %s | sclk %s MHz | fine batches %d (%d calls inside), follow %d, triggers %s"
         % (s["tag"], s["tree_name"], s["rc"], _num(s["total"]), _num(s["user"]), _num(s["sys"]),
            _num(s["load_start"]), _num(s["load_end"]),
            "-" if s["load_range"] is None else "%.1f-%.1f" % tuple(s["load_range"]),
            _num(s["prep"]), _num(s["warm"]), _num(s["steady"], "%.2f"), _num(s["tirt"], "%.4g"),
            _num(s["sclk"], "%.0f"), s["fine_batches"], s["nested"], s["follow_batches"], s["triggers"])]
    if s["per_top"]:
        L.append("    steady per top (s): " + " ".join("%.3f" % v for v in s["per_top"]))
    L.append("    decisions: %d (%d choices: a search's passes are one decision); a trial open in "
             "%d of %d fine batches (last open: %s)"
             % (len(s["searches"]), len(s["trials"]), s["open_any"], s["fine_batches"],
                where({"fine": s["last_open"], "in": "fine"}, s["segments"], s["warmup"])
                if s["last_open"] else "none"))
    for d in s["searches"]:
        L.append(_decision_line("      %-50s" % short(d["what"])[:50], d, s))
        if len(d["passes"]) > 1:
            for p in d["passes"]:
                L.append(_decision_line("        %-48s" % ("pass around %s" % p["base"] if p["base"]
                                                           else "first pass"), p, s))
    if s["screens"]:
        L.append("    screens (first, then the alternative a kernel trial plays): " + "; ".join(
            "%s %d %s then %s at %s" % (x["kind"], x["band"], x["label"], x["alt"], where(x["at"], s["segments"]))
            for x in s["screens"]))
    for kind, picks in sorted(s["models"].items()):
        L.append("    model-priced %s picks: %d (%s)" % (kind, len(picks), _picks(picks)))
    return L


def _picks(picks):
    """Model-priced picks counted by what they chose (a BLOCK pick's subject left out)."""
    return ", ".join("%s x%d" % kv for kv in sorted(Counter(p.split(" -> ")[-1] for p in picks).items()))


def _decision_line(name, r, s):
    """One text line for a decision (a searches() row) or one of its passes (a trials() row)."""
    if r["lock"] is None:
        lock = "OPEN" + (" at %s" % r["base"] if r.get("base_nondefault") else "")
    else:
        lock = r["lock"] + (" (non-default)" if r["nondefault"] else "")
    extra = []
    if r["held"] is not None:
        extra.append("held from file")
    if r["expired"] is not None:
        extra.append("budget spent (%s attempts)" % r["expired"])
    if r["lock"] is not None and not r["rounds"] and r["held"] is None and r["expired"] is None \
            and r["arms"] is not None:
        extra.append("its arms timed outside Choice.round" if r["arms"] > 1 else "one arm, locked at once")
    if r["confirms"]:
        extra.append("picked for confirmation: " + ", ".join(
            "%s at %s" % (l, where(a, s["segments"])) for l, a in r["confirms"]))
    if r["drops"]:
        names = [l for l, _ in r["drops"]]
        extra.append("dropped %s" % (", ".join(names) if len(names) <= 3 else
                                     "%d arms (%s, ...)" % (len(names), ", ".join(names[:2]))))
    first_nd = r.get("first_nondefault_at")
    if first_nd is not None and first_nd != r["lock_at"]:
        extra.append("a pass first locked a non-default arm at %s" % where(first_nd, s["segments"]))
    if r["nondefault"] and r["after_fine"]:
        extra.append("%d fine batches after the lock" % r["after_fine"])
    played = sum(r["played"].values())
    return "%s -> %-18s at %-38s open %3d fine, played %d batches (%s%s), %d ran a non-default arm%s" % (
        name, lock, where(r["lock_at"], s["segments"], s["warmup"]), r["open_fine"], played,
        "/".join("%s %d" % kv for kv in sorted(r["played"].items())) or "none",
        "; %d rounds" % r["rounds"] if r["rounds"] != played else "", r["ran_nondefault"],
        "; " + "; ".join(extra) if extra else "")


# ---- pooled ----------------------------------------------------------------------------------

def _median(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def _ratio(a, b):
    return None if a is None or b is None or b == 0 else a / b


def pooled(procs):
    """The comparison of the base and new processes: per metric (METRICS, tirt) each tree's
    values and median, the ratio of medians new/base and the ratio within each ABBA pair;
    the per-top steady medians; per decision (a search, by its first pass's description)
    each tree's decisions counted by arm, how many were non-default, the most passes one
    took, and the median fine batch they were made at; each tree's non-default decisions
    (one per search) and the processes they were in, and its searches open at the end; per
    offline screen (kind and band) each tree's picks counted; per model-priced kind each
    process's count of picks and how many distinct sets of picks the processes made; and
    each tree's library digests and revisions."""
    by = {n: [p for p in procs if p["tree_name"] == n] for n in ("base", "new")}
    out = dict(n={k: len(v) for k, v in by.items()}, metrics={}, trials={}, nondefault={}, models={},
               digests={k: sorted({str(p["digest"]) for p in v}) for k, v in by.items()},
               revs={k: sorted({str(p["rev"]) for p in v}) for k, v in by.items()})
    pairs = [procs[i:i + 2] for i in range(0, len(procs) - 1, 2)]
    for m in METRICS + ("tirt",):
        med = {k: _median([p[m] for p in v]) for k, v in by.items()}
        pr = []
        for pair in pairs:
            d = {p["tree_name"]: p[m] for p in pair}
            if set(d) == {"base", "new"}:
                pr.append(_ratio(d["new"], d["base"]))
        out["metrics"][m] = dict(values={k: [p[m] for p in v] for k, v in by.items()}, median=med,
                                 ratio=_ratio(med["new"], med["base"]), pairs=pr)
    tops = {p["tops"] for p in procs if p["per_top"]}
    if len(tops) == 1:
        t = tops.pop()
        med = {k: [_median([p["per_top"][j] for p in v if p["per_top"]]) for j in range(t)]
               for k, v in by.items()}
        out["per_top"] = dict(median=med, ratio=[_ratio(a, b) for a, b in zip(med["new"], med["base"])])
    whats = list(dict.fromkeys(d["what"] for p in procs for d in p["searches"]))
    for w in whats:
        e = {}
        for k, v in by.items():
            ds = [d for p in v for d in p["searches"] if d["what"] == w]
            e[k] = dict(locks=dict(Counter(_decision(d) for d in ds)),
                        nondefault=sum(d["nondefault"] for d in ds),
                        processes=sum(any(d["what"] == w for d in p["searches"]) for p in v),
                        passes=max([len(d["passes"]) for d in ds], default=0),
                        lock_fine=_median([d["lock_at"]["fine"] for d in ds if d["lock_at"]]),
                        open_fine=_median([d["open_fine"] for d in ds]))
        out["trials"][w] = e
    out["screens"] = {}
    for x in sorted({(x["kind"], x["band"]) for p in procs for x in p["screens"]}):
        out["screens"]["%s %d" % x] = {k: dict(Counter("%s then %s" % (y["label"], y["alt"]) for p in v
                                                       for y in p["screens"] if (y["kind"], y["band"]) == x))
                                       for k, v in by.items()}
    for kind in sorted({kind for p in procs for kind in p["models"]}):
        sets = {p["tag"]: tuple(sorted(Counter(p["models"].get(kind, [])).items())) for p in procs}
        out["models"][kind] = dict(
            count={p["tag"]: len(p["models"].get(kind, [])) for p in procs},
            distinct=dict({k: len({sets[p["tag"]] for p in v}) for k, v in by.items()},
                          all=len(set(sets.values()))),
            picks={k: _picks([x for p in v for x in p["models"].get(kind, [])]) for k, v in by.items()})
    for k, v in by.items():
        ds = [d for p in v for d in p["searches"]]
        out["nondefault"][k] = dict(decisions=sum(d["nondefault"] for d in ds),
                                    processes=sum(any(d["nondefault"] for d in p["searches"]) for p in v),
                                    open_at_end=sum(d["lock"] is None for d in ds),
                                    open_nondefault=sum(d["lock"] is None and d["base_nondefault"] for d in ds))
    return out


def _decision(d):
    """A decision's label for counting: its lock, or OPEN (at its base when that is non-default)."""
    if d["lock"] is not None:
        return d["lock"]
    return "OPEN at %s" % d["base"] if d["base_nondefault"] else "OPEN"


def format_pooled(P):
    """The pooled comparison as text lines."""
    L = ["pooled: %d base, %d new processes (ABBA pairs in run order)" % (P["n"]["base"], P["n"]["new"])]
    dg = P["digests"]
    L.append("  library digests: base %s (rev %s), new %s (rev %s)%s" % (
        ",".join(dg["base"]), ",".join(P["revs"]["base"]), ",".join(dg["new"]), ",".join(P["revs"]["new"]),
        ": the same library and ladder" if dg["base"] == dg["new"] and len(dg["base"]) == 1
        and dg["base"] != ["None"] else ""))
    for m, e in P["metrics"].items():
        L.append("  %-6s base median %s [%s]  new median %s [%s]  new/base %s  pairs %s" % (
            m, _num(e["median"]["base"], "%.4g"), " ".join(_num(x, "%.4g") for x in e["values"]["base"]),
            _num(e["median"]["new"], "%.4g"), " ".join(_num(x, "%.4g") for x in e["values"]["new"]),
            _num(e["ratio"], "%.3f"), " ".join(_num(x, "%.3f") for x in e["pairs"]) or "-"))
    L.append("  (tirt is a throughput: above 1 is faster; every other ratio is a time: above 1 is slower)")
    if "per_top" in P:
        L.append("  steady per top, base median (s): " + " ".join(_num(x, "%.3f") for x in P["per_top"]["median"]["base"]))
        L.append("  steady per top, new median (s):  " + " ".join(_num(x, "%.3f") for x in P["per_top"]["median"]["new"]))
        L.append("  steady per top, new/base:        " + " ".join(_num(x, "%.2f") for x in P["per_top"]["ratio"]))
    for k, e in P["nondefault"].items():
        L.append("  %-4s non-default decisions %d (one per search; in %d of %d processes); "
                 "open at the end %d (%d at a non-default base)"
                 % (k, e["decisions"], e["processes"], P["n"][k], e["open_at_end"], e["open_nondefault"]))
    for w, e in P["trials"].items():
        L.append("  %-50s base %-40s new %s" % (short(w)[:50], _trial_cell(e["base"]), _trial_cell(e["new"])))
    for kind, e in P["models"].items():
        L.append("  model-priced %s picks per process %s; %s; base %s; new %s" % (
            kind, " ".join("%d" % n for n in e["count"].values()),
            "the same in every process" if e["distinct"]["all"] == 1 else
            "%d distinct sets (base %d, new %d)" % (e["distinct"]["all"], e["distinct"]["base"],
                                                    e["distinct"]["new"]),
            e["picks"]["base"] or "-", e["picks"]["new"] or "-"))
    for b, e in P["screens"].items():
        picks = set(e["base"]) | set(e["new"])
        firsts = {x.split(" then ")[0] for x in picks}
        L.append("  screen %-12s %-14s base %s  new %s" % (
            b, "first varies" if len(firsts) > 1 else ("alt varies" if len(picks) > 1 else "same"),
            ", ".join("%s x%d" % kv for kv in sorted(e["base"].items())),
            ", ".join("%s x%d" % kv for kv in sorted(e["new"].items()))))
    return L


def _trial_cell(e):
    if not e["processes"]:
        return "-"
    return "%s; lock fine %s; open %s%s" % (", ".join("%s %d" % kv for kv in sorted(e["locks"].items())),
                                            _num(e["lock_fine"], "%.0f"), _num(e["open_fine"], "%.0f"),
                                            "; up to %d passes" % e["passes"] if e["passes"] > 1 else "")


def summarise(run_dir):
    """Every recorded process of run_dir (not the warm runs), in run order, and the pooled
    comparison: a dict {processes, pooled, checks}."""
    d = Path(run_dir)
    tags = [p.name[:-len(".meta.json")] for p in d.glob("*.meta.json")
            if json.loads(p.read_text()).get("order") is not None]
    procs = sorted((process_summary(d, t) for t in tags), key=lambda p: p["order"])
    checks = [(p["tag"] + " " + name, ok, text) for p in procs for name, ok, text in p["checks"]]
    n = Counter(p["tree_name"] for p in procs)
    checks.append(("processes", n["base"] == n["new"] and n["base"] > 0,
                   "%d base, %d new" % (n["base"], n["new"])))
    return dict(processes=procs, pooled=pooled(procs), checks=checks)


def print_summary(S, out=sys.stdout):
    """Print a summarise() result: every process, the pooled comparison, the CHECK lines and a
    verdict. Returns the number of failed checks."""
    for p in S["processes"]:
        for line in format_process(p):
            print(line, file=out)
    for line in format_pooled(S["pooled"]):
        print(line, file=out)
    bad = 0
    for name, ok, text in S["checks"]:
        bad += not ok
        print("CHECK %-28s %s  %s" % (name, "ok  " if ok else "FAIL", text), file=out)
    print("VERDICT: %s" % ("all %d checks passed" % len(S["checks"]) if not bad
                           else "%d of %d checks failed" % (bad, len(S["checks"]))), file=out)
    return bad


# ---- the runner ------------------------------------------------------------------------------

def _rev(tree):
    """The tree's git HEAD (short) with '+dirty' for uncommitted tracked changes, or None."""
    try:
        head = subprocess.run(["git", "-C", tree, "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, timeout=30)
        if head.returncode != 0:
            return None
        dirty = subprocess.run(["git", "-C", tree, "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, timeout=30).stdout.strip()
        return head.stdout.strip() + ("+dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return None


def digest(tree, python):
    """A short sha256 of what a ladder process of `tree` runs: its matchedfilter package (every
    file but bytecode and other Pythons' extensions) and tools/ladder.py. Equal digests are
    the same library and bench, whatever git says."""
    import hashlib
    suffix = subprocess.run([python, "-c", "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"],
                            capture_output=True, text=True).stdout.strip()
    pkg = Path(tree) / "python" / "matchedfilter"
    h = hashlib.sha256()
    files = [p for p in pkg.rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and not (p.name.startswith("_core.") and p.suffix in (".so", ".pyd") and not p.name.endswith(suffix))]
    for p in sorted(files) + [Path(tree) / "tools" / "ladder.py"]:
        h.update(str(p.relative_to(tree)).encode() + b"\0" + p.read_bytes())
    return h.hexdigest()[:12]


def stale_extension(tree, python):
    """Why the tree's extension for `python` cannot be trusted (missing, or older than a C
    source or setup.py), or None when it is newer than all of them."""
    suffix = subprocess.run([python, "-c", "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"],
                            capture_output=True, text=True).stdout.strip()
    so = Path(tree) / "python" / "matchedfilter" / ("_core" + suffix)
    if not so.exists():
        return "no %s" % so
    src = [p for p in (Path(tree) / "src").rglob("*") if p.suffix in SOURCES and "gpu" not in p.parts]
    src += [p for p in (Path(tree) / "python" / "matchedfilter").glob("*") if p.suffix in SOURCES]
    src += [Path(tree) / "setup.py"]
    newer = [p for p in src if p.exists() and p.stat().st_mtime > so.stat().st_mtime]
    if newer:
        return "%s is older than %s%s" % (so.name, newer[0], " and %d more" % (len(newer) - 1) if len(newer) > 1 else "")
    return None


def child_env(tree, extra):
    """(env, dropped): the caller's environment without MF_* and LADDER_* variables, with one
    thread for BLAS/OpenMP, PYTHONPATH the tree's python/, MF_AUTOTUNE_LOG=1 and `extra`
    (KEY=VALUE strings) on top; dropped lists the names removed."""
    dropped = sorted(k for k in os.environ if k.startswith(("MF_", "LADDER_")))
    env = {k: v for k, v in os.environ.items() if k not in dropped}
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
               PYTHONUNBUFFERED="1", PYTHONPATH=os.path.join(tree, "python"), MF_AUTOTUNE_LOG="1")
    for kv in extra:
        k, v = kv.split("=", 1)
        env[k] = v
    return env, dropped


def run_one(out, tag, name, order, tree, ladder_args, a, tops, segments, digest=None):
    """One ladder process of `tree` (through the hook) with its log, report and record
    (tag.log, tag.json, tag.meta.json in out; `digest` is recorded). Returns the record."""
    import resource
    env, dropped = child_env(tree, a.env)
    log, report = out / (tag + ".log"), out / (tag + ".json")
    cmd = ["taskset", "-c", a.cores] + (["nice", "-n", str(a.nice)] if a.nice else [])
    cmd += [a.python, str(Path(__file__).resolve()), "hook", os.path.join(tree, "tools", "ladder.py")]
    cmd += ladder_args + ["--out", str(report)]
    trace, stop = [], threading.Event()
    t0 = time.time()

    def sample():
        while not stop.wait(a.load_interval):
            trace.append((round(time.time() - t0, 1), os.getloadavg()[0]))
    load0 = os.getloadavg()
    ru0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    th = threading.Thread(target=sample, daemon=True)
    th.start()
    timed_out = False
    with open(log, "w") as f:
        p = subprocess.Popen(cmd, cwd=tree, env=env, stdout=f, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL)
        try:
            rc = p.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            rc, timed_out = p.wait(), True
    t1 = time.time()
    stop.set()
    th.join()
    ru1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    meta = dict(tag=tag, tree_name=name, tree=tree, rev=_rev(tree), digest=digest, order=order, cmd=cmd,
                env={k: env[k] for k in sorted(env) if k.startswith(("MF_", "LADDER_", "VK_", "OMP_", "PYTHONPATH"))},
                dropped=dropped, cores=a.cores, tops=tops, segments=segments,
                start=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)),
                wall=t1 - t0, user=ru1.ru_utime - ru0.ru_utime, sys=ru1.ru_stime - ru0.ru_stime,
                rc=rc, timed_out=timed_out, load_start=list(load0), load_end=list(os.getloadavg()),
                load_trace=trace)
    (out / (tag + ".meta.json")).write_text(json.dumps(meta, indent=1))
    return meta


def abba(n):
    """The run order of n processes per tree: base, new, new, base, base, new, ..."""
    seq = []
    for r in range(n):
        seq += ["base", "new"] if r % 2 == 0 else ["new", "base"]
    return seq


def cmd_run(a):
    trees = {"base": os.path.abspath(a.base), "new": os.path.abspath(a.new)}
    for name, t in trees.items():
        if not (Path(t) / "tools" / "ladder.py").exists() or not (Path(t) / "python" / "matchedfilter").is_dir():
            sys.exit("%s tree %s has no tools/ladder.py or python/matchedfilter" % (name, t))
        why = stale_extension(t, a.python)
        if why and not a.allow_stale:
            sys.exit("%s tree %s: %s -- rebuild it (setup.py build_ext --inplace) or pass --allow-stale"
                     % (name, t, why))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if list(out.glob("*.meta.json")):
        sys.exit("%s already holds runs: summarise it, or use a new --out" % out)
    common = ["--bank", os.path.abspath(a.bank), "--device", a.device, "--pipeline", "--pure"]
    if a.profiles:
        common += ["--profiles", os.path.abspath(a.profiles)]
    common += a.ladder
    seq = abba(a.processes)
    plan = dict(trees=trees, revs={k: _rev(t) for k, t in trees.items()},
                digests={k: digest(t, a.python) for k, t in trees.items()}, sequence=seq,
                args=vars(a), host=os.uname().nodename)
    (out / "plan.json").write_text(json.dumps(plan, indent=1, default=str))
    if a.dry_run:
        print(json.dumps(plan, indent=1, default=str))
        return 0
    for name in ("base", "new"):
        for w in range(a.warm):
            tag = "warm%d_%s" % (w + 1, name)
            m = run_one(out, tag, name, None, trees[name],
                        common + ["--tops", "1", "--segments", "3"], a, 1, 3, plan["digests"][name])
            print("warm %-4s rc=%s %.1f s" % (name, m["rc"], m["wall"]), flush=True)
            if m["rc"] != 0 and not a.keep_going:      # the recorded runs would fail alike
                sys.exit("%s failed (rc=%s): see %s" % (tag, m["rc"], out / (tag + ".log")))
    for i, name in enumerate(seq):
        tag = "%02d_%s" % (i + 1, name)
        m = run_one(out, tag, name, i, trees[name],
                    common + ["--tops", str(a.tops), "--segments", str(a.segments)], a, a.tops, a.segments,
                    plan["digests"][name])
        for line in format_process(process_summary(out, tag))[:1]:
            print(line, flush=True)
        if m["rc"] != 0 and not a.keep_going:
            print("%s failed (rc=%s): see %s" % (tag, m["rc"], out / (tag + ".log")), flush=True)
            break
    return cmd_summarise(argparse.Namespace(dir=str(out), json=a.json or str(out / "summary.json")))


def cmd_summarise(a):
    S = summarise(a.dir)
    bad = print_summary(S)
    if a.json:
        Path(a.json).write_text(json.dumps(S, indent=1, default=str))
    return 1 if bad else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["hook"]:
        return hook(argv[1:])
    ladder = []
    if "--" in argv:
        k = argv.index("--")
        argv, ladder = argv[:k], argv[k + 1:]
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                epilog="Arguments after -- go to tools/ladder.py unchanged.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run and summarise an interleaved production-length comparison")
    r.add_argument("--base", required=True, help="the baseline tree (its own tools/ladder.py runs)")
    r.add_argument("--new", required=True, help="the tree under test")
    r.add_argument("--processes", type=int, default=4, help="processes per tree (default 4)")
    r.add_argument("--out", required=True, help="a new directory for the logs, reports and records")
    r.add_argument("--bank", required=True, help="the three-level bank (tools/ladder.py --bank)")
    r.add_argument("--profiles", default=None, help="the per-top reference profiles (--profiles)")
    r.add_argument("--device", default="gpu:0")
    r.add_argument("--tops", type=int, default=27)
    r.add_argument("--segments", type=int, default=28)
    r.add_argument("--cores", required=True,
                   help="taskset core list for every process, e.g. 12-15 (required: an unpinned "
                        "process moves between cores the machine's other jobs load)")
    r.add_argument("--nice", type=int, default=0)
    r.add_argument("--warm", type=int, default=1,
                   help="unrecorded short runs (1 top x 3 segments) of each tree first (default 1)")
    r.add_argument("--timeout", type=float, default=3600.0, help="seconds per process (default 3600)")
    r.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                   help="an environment variable for every process (repeatable; recorded)")
    r.add_argument("--python", default=sys.executable)
    r.add_argument("--load-interval", type=float, default=10.0, help="seconds between load samples")
    r.add_argument("--allow-stale", action="store_true", help="run a tree whose extension is older than its sources")
    r.add_argument("--keep-going", action="store_true", help="continue after a failed process")
    r.add_argument("--json", default=None, help="the summary as JSON (default OUT/summary.json)")
    r.add_argument("--dry-run", action="store_true", help="write and print the plan only")
    s = sub.add_parser("summarise", help="summarise a run directory")
    s.add_argument("dir")
    s.add_argument("--json", default=None)
    a = p.parse_args(argv)
    if a.cmd == "run":
        a.ladder = ladder
        return cmd_run(a)
    return cmd_summarise(a)


if __name__ == "__main__":
    sys.exit(main())
