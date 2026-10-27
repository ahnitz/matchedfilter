"""Measured choices: one lifecycle for every choice the library makes by timing.

A choice picks one of a few candidates on this machine (a block size and the Q15 screen of a
filter, a GPU batch's fusion, where follow-ups run, a coarse kernel layout, ...). Every one
follows the same lifecycle, written here once:

  * candidates[0] is the preference: it stands unless another is clearly faster;
  * a lock already kept in MF_COST_FILE (store_key) is reused, so every process sharing
    the file makes the same choice; the first lock written stands (a process that finds
    another's lock on file adopts it);
  * the choice is made whether or not there is a cost file: without one it is kept for
    the process only;
  * every choice ends: an unclear contest runs rounds up to `cap`, and one whose rounds do
    not come (calls that could not be rounds) ends at its `budget` of attempts. Either way,
    without a clear win the preference stands.

A choice is decided by paired rounds on real work: every live candidate timed on the same
input, back to back, each run settled first, the order reversing every round (round; play
runs a real call so, returning the preference's result), and the rounds judged as ratios to
the preference (paired_choice: three quarters of the rounds beyond `tie`, with exact
elimination of a candidate that can no longer win, can_still_win). Rounds, not unpaired
samples: calls of other content, a burst of other work, or a run gaining from the one before
it are what unpaired comparisons mistook for a difference.

The offline decide remains where a real call cannot carry a candidate: the screens that
time kernel layouts on synthetic dispatches and keep pathological ones off the device (their
fastest two are played on real batches, _settings.slot), and the Vulkan subgroup
size, fixed when the device's pipelines are built (measured in subprocesses, one size each).

The state lives in a scope: the process registry by default, or the dict a caller passes
(a device's, for choices that belong to one device object); tests clear it with reset().

On file, a choice is one record "choice|<store_key>": {"value": label, "median": ...}.
"""
import sys
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Hashable, Optional, Sequence, Tuple

import numpy as np

from . import _config

#: Rounds before a first decision, and the most an unclear contest takes: every choice's
#: schedule (MF_TRIAL_ROUNDS sets the first, the cap following at twice it; rounds()).
MINIMUM = 5
CAP = 10


def rounds() -> Tuple[int, int]:
    """(minimum, cap) of rounds: MINIMUM and CAP, or MF_TRIAL_ROUNDS and twice it."""
    base = max(2, int(_config.get("MF_TRIAL_ROUNDS", MINIMUM)))
    return base, (CAP if base == MINIMUM else 2 * base)


_AUTOTUNE_LOCK = threading.Lock()
#: Whether a paired play (Choice.play) is running its candidates: choices met meanwhile take
#: their preference untimed.
_PLAYING = [False]


def playing() -> bool:
    """Whether a trial is running its candidates (Choice.play, a joint round's replays):
    every choice met meanwhile takes its preference untimed, and no trial nests in it."""
    return _PLAYING[0]


@contextmanager
def held():
    """A trial runs its candidates (playing() is True inside)."""
    was = _PLAYING[0]
    _PLAYING[0] = True
    try:
        yield
    finally:
        _PLAYING[0] = was


def _log_autotune(msg, *args):
    if _config.get("MF_AUTOTUNE_LOG"):
        text = msg % args if args else msg
        print(f"[MF_AUTOTUNE] {text}", file=sys.stderr, flush=True)


def _autotune_enabled():
    """MF_AUTOTUNE=0 keeps the model's choice (deterministic); otherwise close calls are measured."""
    return _config.get("MF_AUTOTUNE")


# ---- the one rule every measured choice follows ---------------------------------------
#
# Every choice decides with paired_choice over complete rounds (through Choice).
# History: M2 locked n=4096 on two samples 5.4% faster than n=2048 -- past
# TIE, inside the noise -- and ran 34% slower in steady state; dev2 locked the Q15 screen off
# on a 6% "win" and ran 5% slower without it.

#: Relative cost inside which two candidates are treated as tied, and the tie broken by a
#: fixed order (canonical_order) instead of by which calibration or trial read faster: cost
#: calibration and timed trials move by about this much between processes on a busy host,
#: and a choice that flips with them makes runs incomparable.
TIE = 0.05



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


def can_still_win(samples, model_samples, cap, tie=None):
    """Whether a candidate of a paired contest can still be chosen over the model by
    paired_choice: its rounds faster than the model's by `tie`, plus every round still to come
    up to `cap`, reach the share of rounds a win needs at the cap. (The share a win needs
    grows more slowly than the rounds, so the cap is where a late run of wins counts most.)"""
    tie = TIE if tie is None else tie
    r = np.asarray(samples, float) / np.asarray(model_samples, float)
    wins = int(np.count_nonzero(r < 1.0 - tie))
    return wins + max(0, cap - r.size) >= int(np.ceil(0.75 * max(cap, r.size)))


class Choice:
    """One measured choice between candidates (see the module docstring).

    label(c) is how a candidate is kept on file (a str or int); parse(text) maps a label's
    text back to a candidate -- needed when candidates are added later (add) than a stored
    lock is read. budget = (per_candidate, slack): the contest ends after per_candidate x
    candidates + slack attempts (tick). With `confirm`, a candidate other than the preference
    that the rule picks is not locked at once: a fresh contest of the preference against it
    alone (every other candidate dropped) must pick it again, or the preference stands --
    with many candidates one passes the rule on noise more often than one does."""

    def __init__(self, candidates: Sequence[Hashable] = (), store_key: Optional[str] = None,
                 what: Optional[str] = None, minimum: Optional[int] = None,
                 cap: Optional[int] = None,
                 tie: Optional[float] = None,
                 retrial: Optional[int] = None, label: Optional[Callable[[Any], Any]] = None,
                 parse: Optional[Callable[[str], Any]] = None,
                 budget: Optional[Tuple[int, int]] = None, confirm: bool = False):
        if len(set(candidates)) != len(candidates):
            raise ValueError("a choice needs distinct candidates: %r" % (candidates,))
        self.candidates: tuple = ()
        self.samples: Dict[Hashable, list] = {}
        self.dropped: set = set()
        self.attempts = 0
        self.store_key, self.what = store_key, what or store_key or "choice"
        self.label = label if label is not None else (lambda c: c)
        self._parse = parse
        base, top = rounds()
        self.minimum = int(base if minimum is None else minimum)
        self.cap = int(top if cap is None else cap)
        self.tie, self.retrial, self.calls = tie, retrial, 0
        self.budget = budget
        self.confirm, self.confirming = bool(confirm), None
        self.winner = None
        self.median: Optional[dict] = None
        self._replace = False
        self.candidates = tuple(candidates)  # (parse falls back to matching these)
        rec = self._record()
        self.held = None
        if isinstance(rec, dict) and "value" in rec:
            self.held = self.parse(rec["value"])
            if self.held is not None:
                self.median = self._by_label(rec.get("median"), float) or None
        self.candidates = ()
        for c in candidates:
            self.add(c)
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

    def add(self, cand) -> None:
        """A candidate joins the contest."""
        if cand in self.samples:
            return
        self.candidates += (cand,)
        self.samples[cand] = []

    @property
    def limit(self) -> int:
        """The most calls after which this contest has certainly locked, whatever the
        timings and whether or not its calls yield rounds: with a budget, its attempts (each
        call ticks once); else its cap of rounds. For tests and tools that drive a contest,
        instead of restating its schedule."""
        n = max(1, len(self.candidates))
        if self.budget is not None:
            return self.budget[0] * n + self.budget[1] + 1
        return self.cap

    def live(self):
        return [c for c in self.candidates if c not in self.dropped]

    def restart(self) -> None:
        """A re-trial: the contest starts afresh, and its lock replaces the stored one."""
        self.winner, self.median, self.attempts, self.confirming = None, None, 0, None
        self.samples = {c: [] for c in self.candidates}
        self.dropped = set()
        self._replace = True

    def tick(self):
        """One attempt at a round (a call run for the contest that could not be one): once
        the budget is spent, the contest ends (expire). Returns the winner."""
        if self.winner is not None:
            return self.winner
        self.attempts += 1
        if self.budget is not None and \
                self.attempts > self.budget[0] * max(1, len(self.candidates)) + self.budget[1]:
            self.expire()
        return self.winner

    def expire(self) -> None:
        """End the contest on the rounds it has: the paired rule over them, the preference
        standing unless a candidate is clearly faster -- and outright with too few rounds."""
        live = self.live()
        pref = live[0] if live else self.preference
        sub = {c: self.samples[c] for c in live}
        rounds = min((len(v) for v in sub.values()), default=0)
        w = pref
        if len(sub) > 1 and rounds >= 2:
            w = paired_choice({c: v[:rounds] for c, v in sub.items()}, pref, rounds,
                              minimum=rounds, tie=self.tie)[0] or pref
        _log_autotune("%s budget of %d attempts spent", self.what, self.attempts)
        self.lock(w)

    def drop(self, cand) -> None:
        """`cand` leaves the contest (it cannot or will not run here)."""
        if cand in self.samples:
            self.dropped.add(cand)

    # ---- paired rounds ------------------------------------------------------------------
    def round(self, timings: Dict[Hashable, float]):
        """One complete round: every candidate timed on the same input. Returns the winner."""
        if self.winner is not None:
            return self.winner
        for c in timings:
            self.add(c)
        live = self.live()
        for c in live:
            self.samples[c].append(float(timings[c]))
        w, _ = paired_choice({c: self.samples[c] for c in live},
                             self.preference, self.cap, minimum=self.minimum,
                             tie=self.tie)
        if w is None:
            # A candidate that can no longer win leaves the rounds: past the minimum, one
            # not faster than the preference by `tie` in the share of rounds a win needs.
            for c in live[1:]:
                if not can_still_win(self.samples[c], self.samples[self.preference],
                                     self.cap, tie=self.tie):
                    self.dropped.add(c)
                    _log_autotune("%s: %s cannot win, dropped", self.what, self.label(c))
            if len(self.live()) == 1:
                w = self.preference
        if w is not None and self.confirm and self.confirming is None and w != self.preference:
            # the rule picked a challenger: it must win again, alone against the preference
            self.confirming = w
            for c in self.candidates:
                if c not in (self.preference, w):
                    self.dropped.add(c)
            self.samples[self.preference], self.samples[w] = [], []
            _log_autotune("%s: %s to be confirmed against %s", self.what, self.label(w),
                          self.label(self.preference))
            w = None
        if w is not None:
            self.lock(w)
        return self.winner

    def play(self, run: Callable[[Hashable], Any], ran: Optional[set] = None,
             config: Optional[Callable[[Hashable], Hashable]] = None):
        """One call of a paired choice, on its real input: the result of run(candidate).

        Locked, the winner runs once. Open, every live candidate runs the same call back to
        back, each timed run right after an untimed run of the same candidate (it settles a
        first run's recordings and uploads, and makes every timed run a second run of the
        call: running second gains from the run before), the order reversing every round;
        the timings are a round (round), and the preference's result is returned. `ran`
        collects the configurations that have run (the caller's record of its state). While a play runs, every other choice it meets takes its preference
        untimed (playing()), so trials never nest. config(candidate) names what a candidate
        runs on this call: candidates that run alike are run once and share its timing (they
        can only tie), and `ran` holds configurations."""
        if self.winner is not None and self.retrial and not _PLAYING[0]:
            self.calls += 1
            if self.calls % self.retrial == 0:
                self.restart()
        if self.winner is not None or _PLAYING[0]:
            return run(self.winner if self.winner is not None else self.preference)
        import time
        ran = set() if ran is None else ran
        config = config or (lambda c: c)
        live = self.live()
        order = live if len(self.samples[live[0]]) % 2 == 0 else live[::-1]
        out, times, by_config, results = None, {}, {}, {}
        with held():
            for c in order:
                k = config(c)
                if k not in by_config:
                    # an untimed run of the same call first, every time: a call run second
                    # gains from the first (caches, inputs on the device: a GPU batch ran
                    # 20-30% faster), so each timed run is a second run, whatever the order
                    run(c)
                    ran.add(k)
                    t0 = time.perf_counter()
                    results[k] = run(c)
                    by_config[k] = time.perf_counter() - t0
                times[c] = by_config[k]
            out = results[config(self.preference)]
        if all(t > 0 for t in times.values()):     # a clock that did not move times nothing
            self.round(times)
        return out

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

    def _write(self, rec, replace=False):
        """Store rec unless a valid lock is on file (and replace is off); returns the record
        on file afterwards (rec itself when it was written)."""
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
            return rec
        return _costfile._update_cost(path, "choice|" + self.store_key, merge)


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
    "single-device": "workload", "gpu-batch": "workload", "gpu-single": "workload",
    "gpu-kernels": "machine", "vk-subgroup": "machine", "coarse": "machine", "gateway": "machine",
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
