"""Measured choices: one lifecycle for every choice the library makes by timing.

A choice picks one of a few candidates for a call shape on this machine (a GPU plan or a
CPU plan for single-template calls, fused batches or not, a coarse kernel layout, a gate
chain, a block size, the Q15 screen, ...). Every one follows the same lifecycle, written
here once:

  * candidates[0] is the preference: it stands unless another is clearly faster;
  * a lock already kept in MF_COST_FILE (store_key) is reused, so every process sharing
    the file makes the same choice; the first lock written stands (a process that finds
    another's lock on file adopts it);
  * the choice is made whether or not there is a cost file: without one it is kept for
    the process only;
  * the winner is locked for the process and stored for later processes;
  * every choice ends: an unclear contest samples up to `cap`, and a choice whose samples
    do not come (candidates nobody runs, processes too short to take one) ends at its
    `budget` of attempts. Either way, without a clear win the preference stands.

How candidates are timed differs, and a choice is made one of three ways:

  * online (next/record, or pick/record when the caller places the work): the candidate
    with the fewest samples goes next, ties in candidate order; each process drops its
    first `warmup` samples of each; once every candidate has its `minimum` (or the more an
    unclear contest asked for), the shared rule decides (measured_choice: past
    `tie` and `z` standard errors, else more samples up to `cap` each, then the preference
    stands). `retrial` calls after a lock, the contest starts again (a choice made under
    passing load does not stick). With `persist`, the samples are kept in MF_COST_FILE as
    they come, so a contest longer than one process continues in the next.
  * paired rounds (round): every candidate timed on the same input in one round; decided
    by paired_choice over complete rounds.
  * offline (decide): `measure` times every candidate at once. A stored lock is first
    timed against the runners-up stored with it, and remeasured when one beats it beyond
    the noise (a clock or power transition spoils one process, not every later one).

The state lives in a scope: the process registry by default, or the dict a caller passes
(a device's, for choices that belong to one device object); tests clear it with reset().

On file, a choice is one record "choice|<store_key>": {"value": label, ...} once locked,
or, while a persisted contest is open, {"samples", "need", "attempts", "dropped"} by label.
"""
import sys
import threading
from typing import Any, Callable, Dict, Hashable, Optional, Sequence, Tuple

import numpy as np

from . import _config

#: Samples kept per candidate before a first decision, and the most an unclear contest
#: takes, after the dropped warm-up sample (the single-template device choice's schedule,
#: which the other online two-way choices share).
WARMUP = 1
MINIMUM = 3
CAP = 5
#: The fewest samples a candidate needs to count when a budget runs out.
BUDGET_MINIMUM = 2


_AUTOTUNE_LOCK = threading.Lock()


def _log_autotune(msg, *args):
    if _config.get("MF_AUTOTUNE_LOG"):
        text = msg % args if args else msg
        print(f"[MF_AUTOTUNE] {text}", file=sys.stderr, flush=True)


def _autotune_enabled():
    """MF_AUTOTUNE=0 keeps the model's choice (deterministic); otherwise close calls are measured."""
    return _config.get("MF_AUTOTUNE")


# ---- the one rule every measured choice follows ---------------------------------------
#
# Block-size trials (time_domain._BlockTrials), Q15 screen trials, and chain trials on the CPU
# (per call) and GPU (per batch) all decide with measured_choice (through Choice).
# History: M2 locked n=4096 on two samples 5.4% faster than n=2048 -- past
# TIE, inside the noise -- and ran 34% slower in steady state; dev2 locked the Q15 screen off
# on a 6% "win" and ran 5% slower without it.

#: Relative cost inside which two candidates are treated as tied, and the tie broken by a
#: fixed order (canonical_order) instead of by which calibration or trial read faster: cost
#: calibration and timed trials move by about this much between processes on a busy host,
#: and a choice that flips with them makes runs incomparable.
TIE = 0.05


#: A candidate beats the model's choice only by more than TIE and by more than Z standard
#: errors of the difference of the two medians.
CHOICE_Z = 2.0


def sample_spread(v):
    """Standard deviation of samples: MAD-based (robust to the outliers a batch after a
    switch or a host hiccup produces -- the plain estimate let one such spike keep a 26% gap
    "unclear" until the model's slower chain stood), falling back to the plain estimate
    when MAD reads 0 (half the samples tie: timer quantisation, a repeated cache state)."""
    v = np.asarray(v, float)
    if v.size < 2:
        return float("inf")
    mad = 1.4826 * float(np.median(np.abs(v - np.median(v))))
    return mad if mad > 0 else float(np.std(v, ddof=1))


def paired_choice(samples, model, cap, minimum=5, tie=None):
    """Choose from complete, comparable rounds, using median ratios to the model.

    Each index must describe the same workload for every candidate. Callers reverse
    execution order between rounds and settle each candidate before timing it. A
    majority of rounds must support a gain beyond TIE; an ambiguous contest collects
    more complete rounds up to cap. This does not turn unrelated calls into pairs.
    """
    tie = TIE if tie is None else tie
    if model not in samples or not samples:
        raise ValueError("paired trial requires its model candidate")
    lengths = {len(v) for v in samples.values()}
    if len(lengths) != 1:
        raise ValueError("paired trial requires complete rounds")
    count = lengths.pop()
    if count < minimum:
        return None, {c: minimum for c in samples}
    base = np.asarray(samples[model], float)
    if any(not np.all(np.isfinite(v)) or np.any(np.asarray(v) <= 0)
           for v in samples.values()):
        raise ValueError("paired timings must be finite and positive")
    ratios = {c: np.asarray(v, float) / base for c, v in samples.items()}
    # Require agreement beyond a bare majority: one or two bursts must not decide
    # a small trial. At the cap the model remains the explicit uncertainty fallback.
    needed = int(np.ceil(0.75 * count))
    supported = [c for c, r in ratios.items()
                 if c != model and np.count_nonzero(r < 1.0 - tie) >= needed]
    if supported:
        return min(supported, key=lambda c: float(np.median(ratios[c]))), {}
    if all(c == model or np.count_nonzero(r >= 1.0 - tie) >= needed
           for c, r in ratios.items()):
        return model, {}
    if count < cap:
        return None, {c: count + 1 for c in samples}
    return model, {}


def measured_choice(samples, model, cap, tie=None, z=None):
    """Decide a measured choice from samples {candidate: [cost, ...]} (lower is better).

    For choices that change results or whose effect is a large share of what a sample
    times. A choice whose effect on a whole call is under the tie margin -- a kernel that is
    a small part of the call, with results equal to rounding -- is PRICED instead (timed
    once on its own, the cheaper kept in MF_COST_FILE: _cpu_forward_platform, the corr-pfft
    price in time_domain._corr_block_costs). Trialled over whole calls it sits at the tie
    and the model's choice wins about half the time (cpu-fft on the M2: 4.6-5.2% per call
    for a transform 30% faster).

    Returns (winner, more): winner is the candidate to lock, or None while more samples are
    needed, in which case `more` maps the candidates to measure further to the sample count
    each needs. The fastest median wins only if it is more than `tie` (TIE) below the model's
    candidate's AND the gap exceeds `z` (CHOICE_Z) standard errors of the two medians'
    difference; an unclear contest asks for one more sample of both, up to `cap` each, then
    the model's choice stands. A candidate missing from samples is the model's when model is
    None (the first key)."""
    tie = TIE if tie is None else tie
    z = CHOICE_Z if z is None else z
    if model not in samples:
        model = next(iter(samples))
    med = {c: float(np.median(v)) for c, v in samples.items() if len(v)}
    if model not in med:
        return None, {model: 1}
    best = min(med, key=lambda c: (med[c], c != model))
    if not np.isfinite(med[model]) and np.isfinite(med[best]):
        return best, {}                 # the model's candidate is unusable (priced at inf)
    if best == model or not med[best] < med[model] * (1.0 - tie):
        return model, {}
    a, b = samples[model], samples[best]
    se = float(np.sqrt(sample_spread(a) ** 2 / len(a) + sample_spread(b) ** 2 / len(b)))
    if med[model] - med[best] > z * se:
        return best, {}
    if min(len(a), len(b)) < cap:
        return None, {model: len(a) + 1, best: len(b) + 1}
    return model, {}


class Choice:
    """One measured choice between candidates (see the module docstring).

    label(c) is how a candidate is kept on file (a str or int); parse(text) maps a label's
    text back to a candidate -- needed when candidates are added later (add) than a stored
    lock is read. budget = (per_candidate, slack): the contest ends after per_candidate x
    candidates + slack attempts (tick)."""

    def __init__(self, candidates: Sequence[Hashable] = (), store_key: Optional[str] = None,
                 what: Optional[str] = None, warmup: int = WARMUP, minimum: int = MINIMUM,
                 cap: int = CAP, tie: Optional[float] = None, z: Optional[float] = None,
                 retrial: Optional[int] = None, label: Optional[Callable[[Any], Any]] = None,
                 parse: Optional[Callable[[str], Any]] = None, recheck_stored: bool = False,
                 persist: bool = False, budget: Optional[Tuple[int, int]] = None,
                 paired: bool = False):
        if len(set(candidates)) != len(candidates):
            raise ValueError("a choice needs distinct candidates: %r" % (candidates,))
        self.candidates: tuple = ()
        self.samples: Dict[Hashable, list] = {}
        self.need: Dict[Hashable, int] = {}
        self.pending: Dict[Hashable, int] = {}
        self.dropped: set = set()
        self.attempts = 0
        self.store_key, self.what = store_key, what or store_key or "choice"
        self.label = label if label is not None else (lambda c: c)
        self._parse = parse
        self.warmup, self.minimum, self.cap = int(warmup), int(minimum), int(cap)
        self.tie, self.z, self.retrial, self.calls = tie, z, retrial, 0
        self.persist, self.budget, self.paired = bool(persist), budget, bool(paired)
        self.winner = None
        self.median: Optional[dict] = None
        self._warm: Dict[Hashable, int] = {}
        # A persisted contest's samples, needs and drops for candidates not added yet.
        self._pool: dict = {}
        self._need_pool: dict = {}
        self._drop_pool: set = set()
        self._replace = False
        # (attempts, samples) of the open record on file as this process last read or wrote
        # it; one further along was written by another process meanwhile (_write says so).
        self._seen = (0, 0)
        self.candidates = tuple(candidates)  # (parse falls back to matching these)
        rec = self._record()
        self.held = None
        if isinstance(rec, dict):
            if "value" in rec:
                self.held = self.parse(rec["value"])
                if self.held is not None:
                    self.median = self._by_label(rec.get("median"), float) or None
            elif self.persist and isinstance(rec.get("samples"), dict) \
                    and rec.get("method") == self._method():
                self._pool = {str(k): [float(x) for x in v] for k, v in rec["samples"].items()}
                self._need_pool = {str(k): int(v) for k, v in (rec.get("need") or {}).items()}
                self._drop_pool = {str(k) for k in rec.get("dropped", ())}
                self.attempts = int(rec.get("attempts", 0))
                self._seen = _progress(rec)
        self.candidates = ()
        for c in candidates:
            self.add(c)
        if not recheck_stored:
            self.winner = self.held

    @property
    def preference(self):
        return self.candidates[0] if self.candidates else None

    def parse(self, value):
        """The candidate a stored label names, or None (a value that names no candidate)."""
        if value is None:
            return None
        if self._parse is not None:
            return self._parse(str(value))
        return next((c for c in self.candidates if str(self.label(c)) == str(value)), None)

    def _by_label(self, d, conv):
        if not isinstance(d, dict):
            return {}
        out = {}
        for k, v in d.items():
            c = self.parse(k)
            if c is not None:
                out[c] = conv(v)
        return out

    def _method(self):
        return "paired" if self.paired else None

    def add(self, cand) -> None:
        """A candidate joins the contest (another plan's shortlist, another rank), with any
        samples a persisted contest kept for it."""
        if cand in self.samples:
            return
        self.candidates += (cand,)
        key = str(self.label(cand))
        self.samples[cand] = list(self._pool.pop(key, ()))
        n = self._need_pool.pop(key, None)
        if n is not None:
            self.need[cand] = n
        if key in self._drop_pool:
            self.dropped.add(cand)

    @property
    def sampled(self) -> bool:
        """Whether the contest has samples (of candidates added or still to be)."""
        return any(self.samples.values()) or any(self._pool.values())

    @property
    def limit(self) -> int:
        """The most calls after which this contest has certainly locked, whatever the
        timings and whether or not its calls yield samples: with a budget, its attempts
        (each call ticks once); else every candidate sampled to the cap after its warm-up
        (complete rounds, for a paired contest). For tests and tools that drive a contest,
        instead of restating its schedule. Read it once the candidates are known."""
        n = max(1, len(self.candidates))
        if self.budget is not None:
            return self.budget[0] * n + self.budget[1] + 1
        return self.cap if self.paired else n * (self.warmup + self.cap)

    def needs(self, cand) -> int:
        return max(self.minimum, self.need.get(cand, 0))

    def live(self):
        return [c for c in self.candidates if c not in self.dropped]

    # ---- online -------------------------------------------------------------------------
    def next(self) -> Tuple[Hashable, Optional[Callable[[float], None]]]:
        """(candidate for the next call, record or None): record(seconds) is the caller's
        timing of that call; None while the choice is locked."""
        if self.winner is not None:
            self.calls += 1
            if not self.retrial or self.calls % self.retrial:
                return self.winner, None
            self.restart()
        cand = self.pick()
        return cand, lambda seconds, cand=cand: self.record(cand, seconds)

    def restart(self) -> None:
        """A re-trial: the contest starts afresh, and its lock replaces the stored one."""
        self.winner, self.median, self.attempts = None, None, 0
        self.samples = {c: [] for c in self.candidates}
        self.need, self.pending, self._warm, self.dropped = {}, {}, {}, set()
        self._replace = True

    def pick(self, among: Optional[Sequence] = None, stay=None, placed: Optional[dict] = None):
        """The candidate the next sample should come from (None when none is live): `stay`
        while it still needs samples (a caller for whom switching costs), else the one with
        the fewest, counting samples in flight (pending) and the caller's `placed` work,
        candidates still short of their samples first, ties in candidate order. `among`
        limits it to some candidates (one plan's shortlist)."""
        pool = self.candidates if among is None else [c for c in among if c in self.samples]
        live = [c for c in pool if c not in self.dropped]
        if not live:
            return None
        placed = placed or {}
        have = {c: len(self.samples[c]) + self.pending.get(c, 0) + placed.get(c, 0) for c in live}
        full = {c: have[c] >= self.needs(c) for c in live}
        if stay in live and (not full[stay] or all(full.values())):
            return stay
        return min(live, key=lambda c: (full[c], have[c] + self._warm.get(c, 0),
                                        self.candidates.index(c)))

    def record(self, cand, seconds: float):
        """One sample of `cand`; decides once the contest is complete enough. Returns the
        winner (None while open). A paired choice takes rounds only (round)."""
        if self.winner is not None or cand in self.dropped or self.paired:
            return self.winner
        self.add(cand)
        if self._warm.get(cand, 0) < self.warmup:
            self._warm[cand] = self._warm.get(cand, 0) + 1
            return None
        self.samples[cand].append(float(seconds))
        live = self.live()
        if all(len(self.samples[c]) >= self.needs(c) for c in live):
            w = self.judge(live)
            if w is not None:
                self.lock(w)
                return self.winner
        self._save()
        return self.winner

    def judge(self, among: Sequence):
        """The shared rule over `among` (its first the preference) once each has its samples:
        the winner, or None -- then the candidates it asks about need more (need). Locks
        nothing: a caller may settle a part of the contest on its own (one plan's shortlist)."""
        among = list(among)
        if not among or any(len(self.samples[c]) < self.needs(c) for c in among):
            return None
        w, more = measured_choice({c: self.samples[c] for c in among}, among[0],
                                  self.cap, tie=self.tie, z=self.z)
        if w is None:
            self.need.update(more)
            _log_autotune("%s unclear, sampling further %s", self.what,
                          {str(self.label(c)): n for c, n in more.items()})
        return w

    def tick(self):
        """One attempt at a sample (a call or batch run for the contest, sampled or not):
        once the budget is spent, the contest ends (expire). Returns the winner."""
        if self.winner is not None:
            return self.winner
        self.attempts += 1
        if self.budget is not None and \
                self.attempts > self.budget[0] * max(1, len(self.candidates)) + self.budget[1]:
            self.expire()
        else:
            self._save()
        return self.winner

    def expire(self) -> None:
        """End the contest on what was measured: the shared rule over the candidates with at
        least BUDGET_MINIMUM samples, the preference standing unless one of them is clearly
        faster than it -- and standing outright when it has too few to compare."""
        live = self.live()
        pref = live[0] if live else self.preference
        sub = {c: self.samples[c] for c in live if len(self.samples[c]) >= BUDGET_MINIMUM}
        w = pref
        if pref in sub and len(sub) > 1:
            w = measured_choice(sub, pref, 0, tie=self.tie, z=self.z)[0] or pref
        _log_autotune("%s budget of %d attempts spent", self.what, self.attempts)
        self.lock(w)

    def drop(self, cand) -> None:
        """`cand` leaves the contest (it cannot or will not run here)."""
        if cand in self.samples and cand not in self.dropped:
            self.dropped.add(cand)
            self._save()

    # ---- paired rounds ------------------------------------------------------------------
    def round(self, timings: Dict[Hashable, float]):
        """One complete round: every candidate timed on the same input. Returns the winner."""
        if self.winner is not None:
            return self.winner
        for c in timings:
            self.add(c)
        for c in self.candidates:
            self.samples[c].append(float(timings[c]))
        w, _ = paired_choice({c: self.samples[c] for c in self.candidates},
                             self.preference, self.cap, minimum=self.minimum,
                             tie=self.tie)
        if w is not None:
            self.lock(w)
        else:
            self._save()
        return self.winner

    # ---- offline ------------------------------------------------------------------------
    def decide(self, measure: Callable[[list], Any],
               tiebreak: Optional[Callable[[Any], tuple]] = None):
        """The winner, measured now if need be: measure(candidates) returns {candidate:
        seconds} (optionally a Timings, whose `close` holds the contenders its paired
        confirmation could not tell from the fastest) or {candidate: [seconds, ...]}, or
        None when the device cannot be timed (the preference is then used, not stored).
        Seconds per candidate: the fastest wins, close contenders go to the preference
        (tiebreak(c), then candidate order), and the two runners-up are stored with it.
        Samples per candidate: the shared rule decides."""
        if self.winner is not None:
            return self.winner
        if self.held is not None:
            rivals = [c for c in self.candidates
                      if c != self.held and str(self.label(c)) in self._stored_rivals()]
            if not rivals or _still_fastest(self.held, rivals, measure):
                self.winner = self.held
                return self.winner
        times = measure(list(self.candidates))
        if not times:
            self.winner = self.preference
            return self.winner
        # Another process may have measured meanwhile: its choice stands (first writer
        # wins), so processes sharing a cost file make one choice.
        other = self._stored()
        if other is not None and other != self.held:
            self.winner = other
            return other
        self._replace = self.held is not None          # the stale lock is replaced
        rank = {c: i for i, c in enumerate(self.candidates)}
        if all(isinstance(v, (list, tuple)) for v in times.values()):
            w, _ = measured_choice(
                times, self.preference, min(len(v) for v in times.values()), tie=self.tie, z=self.z)
            self.lock(w if w is not None else self.preference, times)
            return self.winner
        fastest = min(times, key=lambda c: (times[c], rank.get(c, 0)))
        near = {c for c in times if times[c] == times[fastest]} | set(getattr(times, "close", ()))
        w = min(near, key=lambda c: (tuple(tiebreak(c)) if tiebreak else ()) + (rank.get(c, 0),))
        runners = [c for c in sorted(times, key=lambda c: (times[c], rank.get(c, 0))) if c != w]
        self.lock(w, times, rivals=";".join(str(self.label(c)) for c in runners[:2]))
        return self.winner

    def _stored_rivals(self):
        rec = self._record()
        rivals = rec.get("rivals") if isinstance(rec, dict) else None
        return set((rivals or "").split(";")) - {""}

    # ---- the record on file -------------------------------------------------------------
    def lock(self, winner, kept=None, **extra) -> None:
        """Lock `winner` for this process and store it (with `extra` fields) for later ones.
        A lock another process stored first stands: this process adopts it."""
        self.winner = winner
        med = {c: float(np.median(v)) for c, v in self.samples.items() if len(v)}
        if med:
            self.median = med
        rec = {"value": self.label(winner), **extra}
        if med:
            rec["median"] = {str(self.label(c)): v for c, v in med.items()}
        on_file = self._write(rec, replace=self._replace)
        self._replace = False
        if on_file is not rec:
            self._adopt(on_file)
        if kept is None:
            kept = self.samples
        _log_autotune("%s -> %s  %s", self.what, self.label(self.winner),
                      {str(self.label(c)): "%.3g" % float(np.median(v if isinstance(v, (list, tuple)) else [v]))
                       for c, v in kept.items() if (v if isinstance(v, (list, tuple)) else [v])})

    def _adopt(self, rec) -> None:
        w = self.parse(rec.get("value")) if isinstance(rec, dict) else None
        if w is not None:
            self.winner = w
            self.median = self._by_label(rec.get("median"), float) or self.median

    def _save(self) -> None:
        """Keep an open persisted contest on file (its samples, needs, attempts, dropped
        candidates), so the next process continues it; adopt a lock found there instead."""
        if not self.persist or self.winner is not None:
            return
        lbl = lambda c: str(self.label(c))     # noqa: E731
        rec = {"samples": {**self._pool, **{lbl(c): v for c, v in self.samples.items()}},
               "need": {lbl(c): n for c, n in self.need.items()},
               "attempts": int(self.attempts),
               "dropped": sorted(lbl(c) for c in self.dropped)}
        if self._method():
            rec["method"] = self._method()
        on_file = self._write(rec, check_writer=True)
        if on_file is not rec:
            self._adopt(on_file)
        else:
            self._seen = _progress(rec)

    def _record(self):
        if self.store_key is None:
            return None
        from . import _costfile
        path = _costfile._cost_file()
        if path is None:
            return None
        return _costfile._load_cost_file(path).get("choice|" + self.store_key)

    def _stored(self):
        """The candidate a lock on file names, or None (no file, no lock, or a value that
        names no candidate here)."""
        rec = self._record()
        return self.parse(rec.get("value")) if isinstance(rec, dict) else None

    def _write(self, rec, replace=False, check_writer=False):
        """Store rec unless a valid lock is on file (and replace is off); returns the record
        on file afterwards (rec itself when it was written). With check_writer, an open
        record on file further along than this process last saw it means another process is
        sampling the same contest: that is said once per contest, and rec is written as
        before (replacing the other's samples; one writer per open contest keeps them all)."""
        if self.store_key is None:
            return rec
        from . import _costfile
        path = _costfile._cost_file()
        if path is None:
            return rec

        def merge(old):
            if (not replace and isinstance(old, dict) and "value" in old
                    and self.parse(old["value"]) is not None):
                return None                                  # a lock on file stands
            if (check_writer and isinstance(old, dict) and "value" not in old
                    and old.get("method") == self._method()):   # one this choice continues
                on_file = _progress(old)
                if on_file[0] > self._seen[0] or on_file[1] > self._seen[1]:
                    _costfile._cost_warn(path, "writer|" + self.store_key,
                                         "another process is sampling %s; one writer per "
                                         "open contest keeps all samples" % self.what)
            return rec
        return _costfile._update_cost(path, "choice|" + self.store_key, merge)


def _progress(rec) -> Tuple[int, int]:
    """(attempts, samples) of an open contest's record: how far along it is."""
    samples = rec.get("samples")
    return (int(rec.get("attempts", 0)),
            sum(len(v) for v in samples.values()) if isinstance(samples, dict) else 0)


def _still_fastest(choice, rivals, measure):
    """True unless a rival times faster than choice beyond the noise (measure over the
    three; Timings.close holds the contenders within it of the fastest), or choice was not
    timed at all. A device that cannot be timed keeps the choice."""
    t = measure([choice] + list(rivals))
    if not t:
        return True
    if choice not in t:
        return False
    if all(isinstance(v, (list, tuple)) for v in t.values()):
        t = {c: float(np.median(v)) for c, v in t.items()}
    fastest = min(t, key=t.get)
    return fastest == choice or t[choice] == t[fastest] or choice in getattr(t, "close", ())


def stored_lock(store_key: str, parse: Callable[[str], Any]):
    """The candidate (parse(label)) a lock on file names under store_key, or None."""
    from . import _costfile
    path = _costfile._cost_file()
    if path is None:
        return None
    rec = _costfile._load_cost_file(path).get("choice|" + store_key)
    if not isinstance(rec, dict) or "value" not in rec:
        return None
    return parse(str(rec["value"]))


#: Every measured choice of this process: (kind, key) -> Choice.
_CHOICES: Dict[Tuple[str, Hashable], Choice] = {}

#: Each kind of choice and what forgets it: "workload" choices depend on what runs (which
#: calls, on which device) and clear_autotune_cache forgets them; "machine" choices are a
#: property of the hardware and outlive it. A kind must be declared here before use.
SCOPES: Dict[str, str] = {
    "single-device": "workload", "single-batch": "workload", "fused-batch": "workload",
    "sparse-way": "machine", "vk-subgroup": "machine", "coarse": "machine", "gateway": "machine",
    "interleave": "machine",
}


def choice(kind: str, key: Hashable, candidates: Sequence[Hashable] = (),
           scope: Optional[dict] = None, **kw: Any) -> Choice:
    """The choice of `kind` for `key`, made on first use (Choice(candidates, **kw); kw
    applies only then), kept in the process registry or in `scope` (a dict: choices that
    belong to one device object live in its state)."""
    if kind not in SCOPES:
        raise ValueError("declare choice kind %r in _choice.SCOPES (workload or machine)" % kind)
    table = _CHOICES if scope is None else scope.setdefault("_choices", {})
    ch = table.get((kind, key))
    if ch is None:
        ch = table[(kind, key)] = Choice(candidates, **kw)
    return ch


def of_kind(kind: str, scope: Optional[dict] = None) -> Dict[Hashable, Choice]:
    """{key: Choice} of one kind made so far in the process registry (or in `scope`)."""
    table = _CHOICES if scope is None else scope.get("_choices", {})
    return {k: ch for (t, k), ch in table.items() if t == kind}


def reset(kind: Optional[str] = None, scope: Optional[str] = None) -> None:
    """Forget the process registry's choices -- every one, those of one kind, or those of
    every kind declared with this reset scope (SCOPES): the next use starts afresh, from
    MF_COST_FILE's locks."""
    for k in [k for k in _CHOICES if (kind is None or k[0] == kind)
              and (scope is None or SCOPES.get(k[0]) == scope)]:
        del _CHOICES[k]
