"""Joint trials: every coupled measured choice of a filter decided at once, on real calls.

A filter's measured choices -- a bank's block size and the Q15 screen of its plans' first tiers
-- are decided together, by one trial per key, over complete configurations (each plan's gate
chain is the model's: a chain's merit depends on the profile, and a pooled chain decision
sampled on a search's first banks picked one faster there and 5-10% slower over the rest):

  * an arm is a label. DEFAULT is every dimension at its default -- a bank's smallest
    candidate block size, and for each plan the model's screen setting for its chain -- and it
    is the preference: it stands unless another arm is clearly faster. (The smallest size, not
    the model's priced layout: a tie keeps the layout that needs no pricing, and the model
    misjudged block sizes under load, 2026-10-25.) In a first pass every other arm moves one
    dimension -- a block size ("n=4096", or the model's priced layout, "n=model"), the screen ("q15=0") --
    and the instance's model fills in the rest, conditional on it. Both are properties of the
    machine, the same for every profile, so the banks a trial samples first stand for the rest.
    An instance that cannot take an arm's value (a block size that is not among its candidates,
    a screen its first band does not have) runs its default there: its smallest candidate size,
    no screen.
  * instances resolve an arm to a configuration (arm_config) and run it (use_arm); arms an
    instance resolves alike are one configuration, timed once, so they can only tie.
  * a sample is a paired round: every distinct configuration of the live arms run on the same
    work back to back, each after an untimed settling run, the order reversed every round.
    Rounds pool as ratios to DEFAULT (_choice.paired_choice), never as raw times, so instances
    of different cost -- banks of other profiles, plans of other shapes -- pool into one trial.
  * an arm that can no longer win is dropped from later rounds (_choice.Choice.round). An arm
    the rule picks over DEFAULT must then win again, alone against DEFAULT in fresh rounds,
    before it locks (Choice confirm): with seven challengers on a loaded node one passes the
    rule on noise more often than one does. A pass ends at its cap of rounds, or at its
    budget of calls that could not be rounds, with its base standing unless an arm was
    clearly faster twice.
  * a trial is a coordinate search (current_pass): when a pass locks an arm other than its
    base, the next pass starts from that arm and offers it with each dimension it has not
    moved moved too ("n=4096,q15=0"), so a move that only pays after another is found; the
    search ends at a pass that keeps its base. A first pass that keeps DEFAULT ends it, so a
    trial costs a second pass only when something moved.
  * the search's end is applied by each instance resolving the winning label (lock_arm), now
    and in instances made later; every pass's lock is kept in MF_COST_FILE (store key
    "joint|" + key, then pass_key's) when one is set. A later process takes the locked passes
    and runs the first open one afresh: rounds are not kept between processes.

Instances are TimeDomainFilterBanks (their block sizes and their plans' screens;
time_domain._joint_round) and HierarchicalFilters used on their own (their screen;
HierarchicalFilter.run_series). A plan inside a bank is governed by the bank's trial and runs
none of its own.
"""
from typing import Callable, Dict, Optional, Sequence

from . import _choice, _settings
from ._choice import _AUTOTUNE_LOCK, _log_autotune


#: The arm with every dimension at its default (see the module docstring): the preference.
DEFAULT = _settings.DEFAULT


#: A trial ends after this many calls of its instances that could not be a round (follow-ups,
#: calls too small to stand for the work) without a decision; DEFAULT then stands.
UNROUNDED_BUDGET = 64


def pass_key(key: str, base) -> str:
    """The store key of a coordinate pass around base (the first pass's, around DEFAULT, is key)."""
    return key if base == DEFAULT else "%s|%s" % (key, base)


def current_pass(make: Callable[[object, list], "_choice.Choice"], proposals: Sequence[str]):
    """A coordinate search's pass now: the first open one, or the last when the search is over
    (its winner is the search's). make(base, arms) gives the pass around base (its arms
    _settings.around(base, proposals), base first: base is its preference); a pass that locks
    an arm other than its base opens the pass around that arm. A pass with nothing left to
    move locks its base at once, so the search's end is on file like any pass."""
    base = DEFAULT
    while True:
        arms = _settings.around(base, proposals)
        ch = make(base, arms)
        if ch.winner is None and len(arms) < 2:
            with _AUTOTUNE_LOCK:
                ch.lock(base)
        if ch.winner is None or ch.winner == base:
            return ch
        base = ch.winner


def stored_search(key: str):
    """The end of a coordinate search kept in MF_COST_FILE under key (pass_key), or None
    while a pass is open."""
    base = DEFAULT
    while True:
        w = _choice.stored_lock(pass_key(key, base), _settings.valid)
        if w is None or w == base:
            return w
        base = w


class Trial:
    """One key's joint trial: a coordinate search (current_pass) of paired measured choices
    (_choice.Choice) over arm labels, DEFAULT first."""

    def __init__(self, key: str, arms: Sequence[str]):
        self.key = key
        self.proposals = [a for a in dict.fromkeys(arms) if a != DEFAULT]
        self._passes: Dict[str, _choice.Choice] = {}

    def _make(self, base, arms):
        ch = self._passes.get(base)
        if ch is None:
            what = "TRIAL %s" % self.key + ("" if base == DEFAULT else " around %s" % base)
            if base != DEFAULT:
                _log_autotune("%s: arms %s", what, list(arms))
            ch = self._passes[base] = _choice.Choice(
                tuple(arms), store_key=pass_key("joint|" + self.key, base), what=what,
                budget=(0, UNROUNDED_BUDGET), label=str, parse=_settings.valid, confirm=True,
                kind="joint")
        return ch

    @property
    def choice(self) -> "_choice.Choice":
        """The pass now (current_pass)."""
        return current_pass(self._make, self.proposals)

    @property
    def base(self):
        """What the subjects run while the trial is open: the current pass's base."""
        return self.choice.preference

    @property
    def winner(self) -> Optional[str]:
        ch = self.choice
        return ch.winner

    @property
    def arms(self):
        """Every arm the trial has offered, pass by pass (the first pass's first)."""
        self.choice                                         # the passes reached so far
        return tuple(dict.fromkeys(a for ch in self._passes.values() for a in ch.candidates))

    def live(self):
        return self.choice.live()

    @property
    def rounds(self) -> int:
        """Rounds of every pass so far."""
        return sum(len(ch.samples.get(ch.preference, ())) for ch in self._passes.values())

    def round(self, timings: Dict[str, float]) -> Optional[str]:
        self.choice.round(timings)
        return self.winner

    def tick(self) -> Optional[str]:
        """A call of the trial's instances that could not be a round."""
        self.choice.tick()
        return self.winner


#: key -> Trial, for the process (forgotten by clear_autotune_cache).
_TRIALS: Dict[str, Trial] = {}


def trial(key: str, arms: Callable[[], Sequence[str]]) -> Trial:
    """The trial of key, made on first use with the arms arms() proposes (the first instance's
    proposal: later instances resolve the same labels)."""
    with _AUTOTUNE_LOCK:
        tr = _TRIALS.get(key)
    if tr is None:
        proposed = list(arms())
        with _AUTOTUNE_LOCK:
            tr = _TRIALS.get(key)
            if tr is None:
                tr = _TRIALS[key] = Trial(key, proposed)
                _log_autotune("TRIAL %s arms %s", key, list(tr.arms))
    return tr


def winner(key: str) -> Optional[str]:
    """The key's lock: reached in this process or kept in MF_COST_FILE (None if neither)."""
    with _AUTOTUNE_LOCK:
        tr = _TRIALS.get(key)
    if tr is not None:
        return tr.winner
    return stored_search("joint|" + key)


def run_round(tr: Trial, subjects: Sequence, replay: Callable[[], object], work: float,
              settle: Optional[Callable[[], None]] = None,
              keep: Optional[Callable[[object], object]] = None):
    """One paired round of tr over subjects, all on the same work (Choice.play: the one round
    engine): each distinct configuration of the live arms is put on every subject (use_arm),
    run untimed (settle(), else replay(): a GPU batch settles by replaying until it builds no
    more recordings) and then timed over one replay(), the order reversing every round.
    The round belongs to the trial's current pass (current_pass). Returns the result of the
    pass's base's timed replay (passed through keep() as soon as it is taken, before another
    arm's replay can reuse its buffers). When the search ends, every subject locks its winner
    (lock_arm); otherwise they are left on the base of the pass now open. `work` (the round's
    pairs) only scales the logs (MF_AUTOTUNE_LOG, MF_TRIAL_AA_LOG): rounds are judged as
    ratios to DEFAULT."""
    def use(label):
        for s in subjects:
            s.use_arm(label)

    def run(label):
        use(label)
        return replay()

    def warm(label):
        use(label)
        (settle or replay)()

    ch = tr.choice
    try:
        res = ch.play(run, set(), config=lambda a: tuple(s.arm_config(a) for s in subjects),
                      warm=warm, keep=keep, work=work)
    except BaseException:
        use(ch.preference)
        raise
    _log_autotune("%s round %d: %s", ch.what, tr.rounds,
                  {a: "%.3g" % (v[-1] / max(work, 1e-30)) for a, v in ch.samples.items() if v})
    w = tr.winner
    for s in subjects:
        if w is not None:
            s.lock_arm(w)
        else:
            s.use_arm(tr.base)
    return res


def clear() -> None:
    with _AUTOTUNE_LOCK:
        _TRIALS.clear()
