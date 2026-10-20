"""Measured choices: one lifecycle for every choice the library makes by timing.

A choice picks one of a few candidates for a call shape on this machine (a GPU plan or a
CPU plan for single-template calls, fused batches or not, a coarse kernel layout, ...).
Every one follows the same lifecycle, written here once:

  * candidates[0] is the preference: it stands unless another is clearly faster;
  * a lock already kept in MF_COST_FILE (store_key) is reused, so every process sharing
    the file makes the same choice;
  * the choice is made whether or not there is a cost file: without one it is kept for
    the process only;
  * the winner is locked for the process and stored for later processes.

How candidates are timed differs, and a choice is made one of two ways:

  * online (next/record): the next calls alternate the candidates (the one with the fewest
    samples goes next, ties in candidate order), each timed by the caller; the first
    `warmup` samples of each are dropped; once every candidate has the same count, at
    least `minimum` past the warm-up, the shared rule decides (gatechain.measured_choice:
    past `tie` and `z` standard errors, else more samples up to `cap` each, then the
    preference stands). `retrial` calls after a lock, the contest starts again (a choice
    made under passing load does not stick).
  * offline (decide): `measure` times every candidate at once. A stored lock is first
    timed against the runners-up stored with it, and remeasured when one beats it beyond
    the noise (a clock or power transition spoils one process, not every later one).

The state lives in a scope: the process registry by default, or the dict a caller passes
(a device's, for choices that belong to one device object); tests clear it with reset().
"""
from typing import Any, Callable, Dict, Hashable, Optional, Sequence, Tuple

import numpy as np

#: Samples kept per candidate before a first decision, and the most an unclear contest
#: takes, after the dropped warm-up sample (the single-template device choice's schedule,
#: which the other online two-way choices share).
WARMUP = 1
MINIMUM = 3
CAP = 5


class Choice:
    """One measured choice between candidates (see the module docstring)."""

    __slots__ = ("candidates", "samples", "winner", "held", "store_key", "what", "label",
                 "warmup", "minimum", "cap", "tie", "z", "retrial", "calls")

    def __init__(self, candidates: Sequence[Hashable], store_key: Optional[str] = None,
                 what: Optional[str] = None, warmup: int = WARMUP, minimum: int = MINIMUM,
                 cap: int = CAP, tie: Optional[float] = None, z: Optional[float] = None,
                 retrial: Optional[int] = None, label: Optional[Callable[[Any], Any]] = None,
                 recheck_stored: bool = False):
        if len(candidates) < 2 or len(set(candidates)) != len(candidates):
            raise ValueError("a choice needs two or more distinct candidates: %r" % (candidates,))
        self.candidates = tuple(candidates)
        self.samples: Dict[Hashable, list] = {c: [] for c in self.candidates}
        self.store_key, self.what = store_key, what or store_key or "choice"
        self.label = label if label is not None else (lambda c: c)
        self.warmup, self.minimum, self.cap = int(warmup), int(minimum), int(cap)
        self.tie, self.z, self.retrial, self.calls = tie, z, retrial, 0
        self.winner = None
        self.held = self._stored()
        if not recheck_stored:
            self.winner = self.held

    @property
    def preference(self):
        return self.candidates[0]

    def _stored(self):
        """The candidate stored under store_key, or None (no file, no entry, or a value that
        names no candidate here)."""
        if self.store_key is None:
            return None
        from . import gatechain
        held = gatechain.stored_choice(self.store_key)
        return next((c for c in self.candidates if self.label(c) == held), None)

    # ---- online -------------------------------------------------------------------------
    def next(self) -> Tuple[Hashable, Optional[Callable[[float], None]]]:
        """(candidate for the next call, record or None): record(seconds) is the caller's
        timing of that call; None while the choice is locked."""
        if self.winner is not None:
            self.calls += 1
            if not self.retrial or self.calls % self.retrial:
                return self.winner, None
            self.winner = None                           # a re-trial: start afresh
            self.samples = {c: [] for c in self.candidates}
        cand = min(self.candidates, key=lambda c: (len(self.samples[c]),
                                                    self.candidates.index(c)))
        return cand, lambda seconds, cand=cand: self.record(cand, seconds)

    def record(self, cand, seconds: float) -> None:
        """One sample of `cand`; decides once the contest is complete enough."""
        if self.winner is not None:
            return
        self.samples[cand].append(float(seconds))
        counts = {len(v) for v in self.samples.values()}
        if len(counts) != 1 or counts.pop() - self.warmup < self.minimum:
            return
        from . import gatechain
        kept = {c: v[self.warmup:] for c, v in self.samples.items()}
        w, _ = gatechain.measured_choice(kept, self.preference, self.cap, tie=self.tie, z=self.z)
        if w is not None:
            self.lock(w, kept)

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
                      if c != self.held and self.label(c) in self._stored_rivals()]
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
        rank = {c: i for i, c in enumerate(self.candidates)}
        if all(isinstance(v, (list, tuple)) for v in times.values()):
            from . import gatechain
            w, _ = gatechain.measured_choice(
                times, self.preference, min(len(v) for v in times.values()), tie=self.tie, z=self.z)
            self.lock(w if w is not None else self.preference, times)
            return self.winner
        fastest = min(times, key=lambda c: (times[c], rank.get(c, 0)))
        near = {c for c in times if times[c] == times[fastest]} | set(getattr(times, "close", ()))
        w = min(near, key=lambda c: (tuple(tiebreak(c)) if tiebreak else ()) + (rank.get(c, 0),))
        runners = [c for c in sorted(times, key=lambda c: (times[c], rank.get(c, 0))) if c != w]
        self.lock(w, rivals=";".join(str(self.label(c)) for c in runners[:2]))
        return self.winner

    def _stored_rivals(self):
        if self.store_key is None:
            return set()
        from . import gatechain
        return set((gatechain.stored_choice(self.store_key, "rivals") or "").split(";")) - {""}

    # ---- both ---------------------------------------------------------------------------
    def lock(self, winner, kept=None, **extra) -> None:
        """Lock `winner` for this process and store it (with `extra` fields) for later ones."""
        self.winner = winner
        if self.store_key is not None:
            from . import gatechain
            gatechain.store_choice(self.store_key, self.label(winner), **extra)
        from . import _log_autotune
        if kept is None:
            kept = {c: v[self.warmup:] for c, v in self.samples.items()}
        _log_autotune("%s -> %s  %s", self.what, self.label(winner),
                      {str(self.label(c)): "%.3g" % float(np.median(v if isinstance(v, (list, tuple)) else [v]))
                       for c, v in kept.items() if (v if isinstance(v, (list, tuple)) else [v])})


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


#: Every measured choice of this process: (kind, key) -> Choice.
_CHOICES: Dict[Tuple[str, Hashable], Choice] = {}


def choice(kind: str, key: Hashable, candidates: Sequence[Hashable],
           scope: Optional[dict] = None, **kw: Any) -> Choice:
    """The choice of `kind` for `key`, made on first use (Choice(candidates, **kw); kw
    applies only then), kept in the process registry or in `scope` (a dict: choices that
    belong to one device object live in its state)."""
    table = _CHOICES if scope is None else scope.setdefault("_choices", {})
    ch = table.get((kind, key))
    if ch is None:
        ch = table[(kind, key)] = Choice(candidates, **kw)
    return ch


def of_kind(kind: str, scope: Optional[dict] = None) -> Dict[Hashable, Choice]:
    """{key: Choice} of one kind made so far in the process registry (or in `scope`)."""
    table = _CHOICES if scope is None else scope.get("_choices", {})
    return {k: ch for (t, k), ch in table.items() if t == kind}


def reset(kind: Optional[str] = None) -> None:
    """Forget the process registry's choices (of one kind): the next use starts afresh,
    from MF_COST_FILE's locks."""
    for k in [k for k in _CHOICES if kind is None or k[0] == kind]:
        del _CHOICES[k]
