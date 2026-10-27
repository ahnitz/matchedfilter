"""Joint trials: every coupled measured choice of a filter decided at once, on real calls.

A filter's measured choices -- a bank's block size and the Q15 screen of its plans' first tiers
-- are decided together, by one trial per key, over complete configurations (each plan's gate
chain is the model's: a chain's merit depends on the profile, and a pooled chain decision
sampled on a search's first banks picked one faster there and 5-10% slower over the rest):

  * an arm is a label. DEFAULT is every dimension at its default -- a bank's smallest
    candidate block size, and for each plan the model's screen setting for its chain -- and it
    is the preference: it stands unless another arm is clearly faster. (The smallest size, not
    the model's priced layout: a tie keeps the layout that needs no pricing, and the model
    misjudged block sizes under load, 2026-10-25.) Every other arm moves one dimension -- a
    block size ("n=4096", or the model's priced layout, "n=model"), the screen ("q15=0") --
    and the instance's model fills in the rest, conditional on it. Both are properties of the
    machine, the same for every profile, so the banks a trial samples first stand for the rest. An instance that cannot take an arm's value (a chain outside
    a plan's feasible set, a screen its first band does not have) runs its model choice there.
  * instances resolve an arm to a configuration (arm_config) and run it (use_arm); arms an
    instance resolves alike are one configuration, timed once, so they can only tie.
  * a sample is a paired round: every distinct configuration of the live arms run on the same
    work back to back, each after an untimed settling run, the order reversed every round.
    Rounds pool as ratios to DEFAULT (_choice.paired_choice), never as raw times, so instances
    of different cost -- banks of other profiles, plans of other shapes -- pool into one trial.
  * an arm that can no longer win is dropped from later rounds (_choice.Choice.round). An arm
    the rule picks over DEFAULT must then win again, alone against DEFAULT in fresh rounds,
    before it locks (Choice confirm): with seven challengers on a loaded node one passes the
    rule on noise more often than one does. A trial ends at its cap of rounds, or at its
    budget of calls that could not be rounds, with DEFAULT standing unless an arm was
    clearly faster twice.
  * a lock is applied by each instance resolving the winning label (lock_arm), now and in
    instances made later; it is kept in MF_COST_FILE (store key "joint|" + key) when one is set.

Instances are TimeDomainFilterBanks (their block sizes and their plans' screens;
time_domain._joint_round) and HierarchicalFilters used on their own (their screen;
HierarchicalFilter.run_series). A plan inside a bank is governed by the bank's trial and runs
none of its own.
"""
import time
from typing import Callable, Dict, Optional, Sequence

from . import _choice, _settings
from ._choice import _AUTOTUNE_LOCK, _log_autotune


#: The arm with every dimension at its default (see the module docstring): the preference.
DEFAULT = _settings.DEFAULT


#: A trial ends after this many calls of its instances that could not be a round (follow-ups,
#: calls too small to stand for the work) without a decision; DEFAULT then stands.
UNROUNDED_BUDGET = 64


class Trial:
    """One key's joint trial: a paired measured choice (_choice.Choice) over arm labels,
    DEFAULT first."""

    def __init__(self, key: str, arms: Sequence[str]):
        arms = [DEFAULT] + [a for a in dict.fromkeys(arms) if a != DEFAULT]
        self.key = key
        self.choice = _choice.Choice(
            tuple(arms), store_key="joint|" + key, what="TRIAL %s" % key,
            budget=(0, UNROUNDED_BUDGET), label=str, parse=_settings.valid,
            confirm=True)

    @property
    def winner(self) -> Optional[str]:
        return self.choice.winner

    @property
    def arms(self):
        return self.choice.candidates

    def live(self):
        return self.choice.live()

    @property
    def rounds(self) -> int:
        return len(self.choice.samples.get(DEFAULT, ()))

    def round(self, timings: Dict[str, float]) -> Optional[str]:
        return self.choice.round(timings)

    def tick(self) -> Optional[str]:
        """A call of the trial's instances that could not be a round."""
        return self.choice.tick()


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
    return _choice.stored_lock("joint|" + key, _settings.valid)


def run_round(tr: Trial, subjects: Sequence, replay: Callable[[], object], work: float,
              settle: Optional[Callable[[], None]] = None,
              keep: Optional[Callable[[object], object]] = None):
    """One paired round of tr over subjects, all on the same work (Choice.play: the one round
    engine): each distinct configuration of the live arms is put on every subject (use_arm),
    run untimed (settle(), else replay(): a GPU batch settles by replaying until it builds no
    more recordings) and then timed over one replay(), the order reversing every round.
    Returns the result of DEFAULT's timed replay (passed through keep() as soon as it is
    taken, before another arm's replay can reuse its buffers). On a decision, every subject
    locks the winner (lock_arm); otherwise they are left on DEFAULT. `work` (the round's
    pairs) only scales the log: rounds are judged as ratios to DEFAULT."""
    def use(label):
        for s in subjects:
            s.use_arm(label)

    def run(label):
        use(label)
        return replay()

    def warm(label):
        use(label)
        (settle or replay)()

    try:
        res = tr.choice.play(run, set(), config=lambda a: tuple(s.arm_config(a) for s in subjects),
                             warm=warm, keep=keep)
    except BaseException:
        use(DEFAULT)
        raise
    w = tr.choice.winner
    _log_autotune("TRIAL %s round %d: %s", tr.key, tr.rounds,
                  {a: "%.3g" % (v[-1] / max(work, 1e-30)) for a, v in tr.choice.samples.items() if v})
    for s in subjects:
        if w is not None:
            s.lock_arm(w)
        else:
            s.use_arm(DEFAULT)
    return res


def clear() -> None:
    with _AUTOTUNE_LOCK:
        _TRIALS.clear()
