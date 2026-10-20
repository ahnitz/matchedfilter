"""Measured choices: one lifecycle for every choice the library makes by timing.

A choice picks one of a few candidates for a call shape on this machine (a GPU plan or a
CPU plan for single-template calls, fused batches or not, ...). Every one follows the same
lifecycle, written here once:

  * candidates[0] is the preference: it stands unless another is clearly faster;
  * a lock already kept in MF_COST_FILE (store_key) is taken as it is, untimed, so every
    process sharing the file makes the same choice;
  * otherwise the next calls alternate the candidates (the one with the fewest samples
    goes next, ties in candidate order), each timed by the caller through record(seconds);
  * the first `warmup` samples of each candidate are dropped (they build records, wake the
    device);
  * once every candidate has the same number of samples, at least `minimum` past the
    warm-up, the shared rule decides (gatechain.measured_choice: past TIE and past the
    noise, else more samples up to `cap` each, then the preference stands);
  * the winner is locked for the process and stored for later processes.

The state is the process's (registry below); tests clear it with reset().
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

    __slots__ = ("candidates", "samples", "winner", "store_key", "what", "warmup",
                 "minimum", "cap")

    def __init__(self, candidates: Sequence[Hashable], store_key: Optional[str] = None,
                 what: Optional[str] = None, warmup: int = WARMUP, minimum: int = MINIMUM,
                 cap: int = CAP):
        if len(candidates) < 2 or len(set(candidates)) != len(candidates):
            raise ValueError("a choice needs two or more distinct candidates: %r" % (candidates,))
        self.candidates = tuple(candidates)
        self.samples: Dict[Hashable, list] = {c: [] for c in self.candidates}
        self.store_key, self.what = store_key, what or store_key or "choice"
        self.warmup, self.minimum, self.cap = int(warmup), int(minimum), int(cap)
        self.winner = None
        if store_key is not None:
            from . import gatechain
            held = gatechain.stored_choice(store_key)
            if held in self.candidates:
                self.winner = held

    @property
    def preference(self):
        return self.candidates[0]

    def next(self) -> Tuple[Hashable, Optional[Callable[[float], None]]]:
        """(candidate for the next call, record or None): record(seconds) is the caller's
        timing of that call; None once the choice is locked."""
        if self.winner is not None:
            return self.winner, None
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
        w, _ = gatechain.measured_choice(kept, self.preference, self.cap)
        if w is not None:
            self.lock(w, kept)

    def lock(self, winner, kept=None) -> None:
        """Lock `winner` for this process and store it for later ones."""
        self.winner = winner
        if self.store_key is not None:
            from . import gatechain
            gatechain.store_choice(self.store_key, winner)
        from . import _log_autotune
        kept = kept or {c: v[self.warmup:] for c, v in self.samples.items()}
        _log_autotune("%s -> %s  median s %s", self.what, winner,
                      {c: "%.3g" % float(np.median(v)) for c, v in kept.items() if len(v)})


#: Every measured choice of this process: (kind, key) -> Choice.
_CHOICES: Dict[Tuple[str, Hashable], Choice] = {}


def choice(kind: str, key: Hashable, candidates: Sequence[Hashable], **kw: Any) -> Choice:
    """The process's choice of `kind` for `key`, made on first use (Choice(candidates,
    **kw)); kw (store_key, what, schedule) applies only then."""
    ch = _CHOICES.get((kind, key))
    if ch is None:
        ch = _CHOICES[(kind, key)] = Choice(candidates, **kw)
    return ch


def of_kind(kind: str) -> Dict[Hashable, Choice]:
    """{key: Choice} of one kind made so far in this process."""
    return {k: ch for (t, k), ch in _CHOICES.items() if t == kind}


def reset(kind: Optional[str] = None) -> None:
    """Forget the process's choices (of one kind): the next use starts afresh, from
    MF_COST_FILE's locks."""
    for k in [k for k in _CHOICES if kind is None or k[0] == kind]:
        del _CHOICES[k]
