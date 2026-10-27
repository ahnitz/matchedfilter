"""Joint trials (_trial): block sizes, chains and the Q15 screen decided together by paired
rounds of complete configurations, for banks (time_domain._joint_round) and for plans used on
their own (HierarchicalFilter.run_series)."""
import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank, _costfile, _trial
from matchedfilter import time_domain as td


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    mf.clear_autotune_cache()
    yield
    mf.clear_autotune_cache()


# ---- the round, on fake subjects with a fake clock -------------------------------------------

class _Clock:
    """perf_counter for _trial: advanced by the fake replays."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class _Subject:
    """An instance whose arms resolve to configurations through `conf`, whose replay costs
    `cost[config]` seconds (and settling `settle_cost` more), recording what ran."""

    def __init__(self, clock, conf, cost, settle_cost=0.0):
        self.clock, self.conf, self.cost, self.settle_cost = clock, conf, cost, settle_cost
        self.arm, self.ran, self.locked = _trial.DEFAULT, [], None

    def arm_config(self, label):
        return self.conf.get(label, self.conf[_trial.DEFAULT])

    def use_arm(self, label):
        self.arm = label

    def lock_arm(self, label):
        self.arm, self.locked = label, label

    def replay(self):
        c = self.arm_config(self.arm)
        self.ran.append(c)
        self.clock.t += self.cost[c]
        return ("result", c)


def _drive(subject, arms, rounds=40, settle=None):
    tr = _trial.trial("t|unit", lambda: arms)
    out = []
    for _ in range(rounds):
        if tr.winner is not None:
            break
        out.append(_trial.run_round(tr, [subject], subject.replay, 1.0, settle=settle))
    return tr, out


@pytest.fixture
def clock(monkeypatch):
    c = _Clock()
    monkeypatch.setattr(_trial.time, "perf_counter", c)
    return c


ARMS = [_trial.DEFAULT, "n=4096", "n=model", "q15=0"]


def test_a_clearly_faster_arm_locks_and_a_slower_one_never_does(clock):
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "n=model": "c", "q15=0": "d"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 2.0, "c": 0.8, "d": 1.3})
    tr, _ = _drive(s, ARMS)
    assert tr.winner == "n=model" and s.locked == tr.winner
    s = _Subject(clock, conf, {"a": 1.0, "b": 2.0, "c": 1.2, "d": 1.3})
    mf.clear_autotune_cache()
    tr, _ = _drive(s, ARMS)
    assert tr.winner == _trial.DEFAULT


def test_a_tie_keeps_the_default(clock):
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "n=model": "c", "q15=0": "d"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.98, "c": 1.01, "d": 0.99})   # inside TIE
    tr, _ = _drive(s, ARMS)
    assert tr.winner == _trial.DEFAULT


def _loaded(clock, conf, factor, sd, seed):
    """A subject whose every run costs factor[config], times a lognormal load swing of sd."""
    rng = np.random.default_rng(seed)

    class Loaded(_Subject):
        def replay(self):
            c = self.arm_config(self.arm)
            self.ran.append(c)
            self.clock.t += factor[c] * float(np.exp(rng.normal(0.0, sd)))
            return ("result", c)
    return Loaded(clock, conf, {})


def test_a_large_gain_locks_under_heavy_load(clock):
    """Under +-25% a run, an arm 40% faster (the screen against no screen, 18-46% on the CPUs
    measured) is found."""
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "q15=1": "c"}
    found = 0
    for seed in range(20):
        mf.clear_autotune_cache()
        tr, _ = _drive(_loaded(clock, conf, {"a": 1.0, "b": 1.6, "c": 0.6}, 0.25, seed),
                       [_trial.DEFAULT, "n=4096", "q15=1"])
        found += tr.winner == "q15=1"
    assert found >= 19


def test_a_worse_arm_never_locks_under_heavy_load(clock):
    """Under the same load an arm 30% slower never locks."""
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "q15=0": "c"}
    for seed in range(50):
        mf.clear_autotune_cache()
        tr, _ = _drive(_loaded(clock, conf, {"a": 1.0, "b": 1.3, "c": 1.3}, 0.25, seed),
                       [_trial.DEFAULT, "n=4096", "q15=0"])
        assert tr.winner == _trial.DEFAULT, seed


def test_arms_resolving_alike_are_timed_once_and_can_only_tie(clock):
    """An arm an instance resolves to DEFAULT's configuration (the model's layout equal to the
    smallest size's, a screen the band does not have) shares its timing: one replay a round
    for both, and it cannot win."""
    conf = {_trial.DEFAULT: "a", "n=4096": "a", "n=model": "c", "q15=0": "a"}
    s = _Subject(clock, conf, {"a": 1.0, "c": 1.5})
    tr, _ = _drive(s, ARMS, rounds=1)
    assert sorted(set(s.ran)) == ["a", "c"] and len(s.ran) == 4      # settle + timed, two configs
    samples = tr.choice.samples
    assert samples["n=4096"] == samples[_trial.DEFAULT] == samples["q15=0"]


def test_settling_is_not_timed_and_the_order_alternates(clock):
    conf = {_trial.DEFAULT: "a", "n=4096": "b"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.7})
    settled = []

    def settle():
        clock.t += 100.0                     # a settling run's cost: not in the round
        settled.append(s.arm_config(s.arm))
    tr, _ = _drive(s, [_trial.DEFAULT, "n=4096"], rounds=2, settle=settle)
    assert tr.choice.samples[_trial.DEFAULT] == pytest.approx([1.0, 1.0])
    assert tr.choice.samples["n=4096"] == pytest.approx([0.7, 0.7])
    assert settled == ["a", "b", "b", "a"]          # reversed on the second round


def test_the_round_returns_defaults_result_kept_before_later_arms(clock):
    conf = {_trial.DEFAULT: "a", "n=4096": "b"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 1.5})
    kept = []
    tr = _trial.trial("t|keep", lambda: [_trial.DEFAULT, "n=4096"])
    res = _trial.run_round(tr, [s], s.replay, 1.0, keep=lambda r: kept.append(len(s.ran)) or r)
    assert res == ("result", "a")
    assert kept == [2]               # taken right after DEFAULT's timed run, before b ran
    assert s.arm == _trial.DEFAULT    # left on DEFAULT while the trial is open


def test_an_arm_that_cannot_win_leaves_the_rounds(clock):
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "n=model": "c"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 3.0, "c": 0.9})
    tr = _trial.trial("t|drop", lambda: [_trial.DEFAULT, "n=4096", "n=model"])
    for _ in range(3):
        _trial.run_round(tr, [s], s.replay, 1.0)
    assert "n=4096" in tr.choice.dropped and "n=4096" not in tr.live()
    s.ran.clear()
    _trial.run_round(tr, [s], s.replay, 1.0)
    assert "b" not in s.ran                     # no longer run


def test_a_replay_error_releases_the_guard(clock):
    class Boom(_Subject):
        def replay(self):
            raise RuntimeError("replay")
    s = Boom(clock, {_trial.DEFAULT: "a"}, {"a": 1.0})
    tr = _trial.trial("t|boom", lambda: [_trial.DEFAULT, "n=4096"])
    with pytest.raises(RuntimeError):
        _trial.run_round(tr, [s], s.replay, 1.0)
    assert not tr.replaying


def test_a_lock_persists_across_processes_and_an_open_trial_does_not(clock, monkeypatch, tmp_path):
    """A trial's lock is kept in MF_COST_FILE and read back without a trial; an open trial's
    rounds are the process's own (a new process starts it afresh)."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    conf = {_trial.DEFAULT: "a", "n=4096": "b"}
    arms = [_trial.DEFAULT, "n=4096"]
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.7})
    tr = _trial.trial("t|persist", lambda: arms)
    _trial.run_round(tr, [s], s.replay, 1.0)
    mf.clear_autotune_cache()                                       # a new process
    tr = _trial.trial("t|persist", lambda: arms)
    assert tr.rounds == 0 and tr.winner is None
    for _ in range(4 * _trial.ROUND_CAP):
        if tr.winner is not None:
            break
        _trial.run_round(tr, [s], s.replay, 1.0)
    assert tr.winner == "n=4096"
    mf.clear_autotune_cache()
    assert _trial.winner("t|persist") == "n=4096"


def test_a_winner_on_noise_is_not_confirmed(clock):
    """An arm the rule picks must win again, alone against the default: a burst of wins that
    does not repeat leaves the default standing."""
    conf = {_trial.DEFAULT: "a", "n=4096": "b"}
    seq = iter([0.8] * _trial.rounds_wanted() + [1.0] * 40)        # fast at first only

    class Burst(_Subject):
        def replay(self):
            c = self.arm_config(self.arm)
            self.ran.append(c)
            self.clock.t += next(seq) if c == "b" else 1.0
            return ("result", c)
    s = Burst(clock, conf, {})
    tr, _ = _drive(s, [_trial.DEFAULT, "n=4096"])
    assert tr.winner == _trial.DEFAULT


def test_labels_round_trip():
    for label in (_trial.DEFAULT, "n=2048", "n=model", "q15=1", "q15=0"):
        kind, v = _trial.parse_arm(label)
        again = {"default": lambda: _trial.DEFAULT, "n": lambda: _trial.n_arm(v),
                 "q15": lambda: _trial.q15_arm(v)}[kind]()
        assert again == label
    for bad in ("chain=2048:256", "chain=+1", "blocks=2"):    # chains are never arms
        with pytest.raises(ValueError):
            _trial.parse_arm(bad)


# ---- banks ------------------------------------------------------------------------------------

def _inspiral_bank(seed=5):
    rng = np.random.default_rng(seed)
    counts = list(rng.integers(300, 900, 48))
    rate, df = 2048.0, 1.0 / 16
    f = np.arange(int(rate / 2 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    taps = []
    for c in counts:
        ff = np.fft.rfftfreq(c, 1 / rate)
        amp = np.sqrt(np.interp(ff, f, w))
        h = np.fft.irfft(amp * np.exp(2j * np.pi * rng.random(ff.size)), c)
        taps.append((h / np.linalg.norm(h)).astype(np.float32))
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5,
                                false_dismissal=0.001, binsize=256)
    bank.set_reference(w, delta_f=df)
    return bank, rng


def _data(rng, L=1 << 16):
    x = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    x[30000:30400] += 40 * np.exp(1j * np.linspace(0, 30, 400))
    return x


def test_a_bank_proposes_sizes_chains_and_the_screen_and_starts_on_the_default():
    bank, _ = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    bank._prepare_arms()
    arms = bank._joint_arms()
    assert arms[0] == _trial.DEFAULT
    assert [a for a in arms if a.startswith("n=")] == [_trial.n_arm(n) for n in bank._trial_cands[1:]]
    assert bank._layout_rank == bank._arm_rank(_trial.DEFAULT) == 0     # the smallest size
    assert {n for _, n in bank.chosen_layout} == {bank._trial_cands[0]}
    assert all(p._governed for p in bank._layout_plans(0))              # the bank's trial governs


def test_a_banks_trial_runs_without_a_cost_file_switches_exactly_and_locks():
    """Without MF_COST_FILE a bank's real calls are the trial's rounds; every arm reports the
    same triggering templates as an untrialled bank; the trial locks, and a later bank
    builds only the winner's layout."""
    bank, rng = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    plain, _ = _inspiral_bank()
    plain._in_trial = False
    data = _data(rng)
    ref = set(np.unique(plain.filter_series(data).template_indices))
    for _ in range(2 * _trial.ROUND_CAP + 1):
        out = TimeDomainFilterBank.filter_series_many([(bank, data, {})])[0]
        assert set(np.unique(out.template_indices)) == ref
        if not bank._in_trial:
            break
    assert not bank._in_trial and bank._layouts is None                # locked, the rest freed
    w = _trial.winner(td._trial_key(bank))
    assert w is not None and bank._bank_arm == w
    later, _ = _inspiral_bank()
    assert later._layouts is None and not later._in_trial              # only the winner built
    assert later.chosen_layout == bank.chosen_layout


def test_a_bank_adopts_a_persisted_lock_without_pricing(monkeypatch, tmp_path):
    """A lock on file applies at the bank's first reference: no trial, and for a lock that
    fixes no block size, no block-size pricing -- the default (smallest) size alone."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    bank, _ = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    key = td._trial_key(bank)
    smallest = bank._trial_cands[0]
    _costfile._store_cost(str(tmp_path / "costs.json"), "choice|joint|" + key, {"value": "q15=0"})
    mf.clear_autotune_cache()                                          # a new process
    from matchedfilter import _calibration
    priced = []
    orig = _calibration.price_block_sizes
    monkeypatch.setattr(_calibration, "price_block_sizes", lambda *a, **k: priced.append(1) or orig(*a, **k))
    again, rng = _inspiral_bank()
    assert td._trial_key(again) == key
    assert again._layouts is None and not again._in_trial and not priced
    assert {n for _, n in again.chosen_layout} == {smallest}
    TimeDomainFilterBank.filter_series_many([(again, _data(rng, 1 << 15), {})])
    assert all(p._arm == "q15=0" and not p._q15 for p in again._layout_plans(0))


def test_a_banks_size_lock_builds_that_size():
    bank, _ = _inspiral_bank()
    if len(bank._trial_cands) < 3:
        pytest.skip("one single size only")
    other = bank._trial_cands[1]
    tr = _trial.trial(td._trial_key(bank), bank._joint_arms)
    tr.choice.lock(_trial.n_arm(other))
    again, _ = _inspiral_bank()
    assert {n for _, n in again.chosen_layout} == {other} and again._layouts is None


# ---- plans used on their own --------------------------------------------------------------------

def _plan(chain=None, nt=7, seed=123):
    rng = np.random.default_rng(seed)
    n = 1024
    k = np.arange(n)
    power = np.where((k > 4) & (k < n // 2), np.maximum(k, 1.0) ** (-7.0 / 3), 0.0)
    p = mf.HierarchicalFilter(n, 1, nt, snr=5.5, fd=1e-3, chain=chain)
    p.set_reference(power)
    t = (rng.normal(size=(nt, n)) + 1j * rng.normal(size=(nt, n))).astype(np.complex64)
    p.set_templates(t / np.linalg.norm(t, axis=1, keepdims=True))
    series = rng.normal(size=8192).astype(np.float32)
    starts = (np.arange(7) * n).astype(np.int64)
    return p, series, starts


def _run(p, series, starts, raw=False):
    m = len(starts)
    return p.run_series(series, starts=starts, win_start=np.zeros(m, np.int64),
                        win_end=np.full(m, p.n, np.int64), raw=raw)


@pytest.mark.parametrize("raw", [False, True])
def test_a_plans_rounds_return_the_defaults_results(raw):
    """The screen changes no result, so a pinned plan's rounds (its only arms: the screen) give
    the same peaks as an untrialled run; raw results, which reuse buffers, are copies."""
    if not mf._q15_available(256):
        pytest.skip("backend has no Q15 screen")
    p, series, starts = _plan(chain=(256, 512))
    p._governed = True                                  # no trial: the reference result
    ref = _run(p, series, starts, raw=raw)
    ref = tuple(x.copy() for x in ref) if raw else ref.copy()
    p._governed = False
    for _ in range(3):
        got = _run(p, series, starts, raw=raw)
        for a, b in (zip(got, ref) if raw else [(got, ref)]):
            np.testing.assert_array_equal(a, b)
    (trial,) = mf.get_autotune_state()["trials"].values()
    assert set(trial["arms"]) == {_trial.DEFAULT, "q15=1", "q15=0"}
    assert len(trial["samples"][_trial.DEFAULT]) == 3
    assert tuple(p.config) == (256, 512)                 # a pinned chain stands


def test_no_trial_with_autotune_off_or_inside_a_bank(monkeypatch):
    p, series, starts = _plan()
    p._governed = True
    _run(p, series, starts)
    assert not mf.get_autotune_state()["trials"]
    monkeypatch.setenv("MF_AUTOTUNE", "0")
    q, series, starts = _plan()
    _run(q, series, starts)
    assert not mf.get_autotune_state()["trials"] and q.autotune_info["status"] == "model"


def test_a_plan_runs_its_model_chain_whatever_the_arm():
    """Arms move the screen (and a bank's block size), never a plan's chain: its model's."""
    p, series, starts = _plan()
    _run(p, series, starts)
    chain = tuple(p.config)
    assert chain == p.autotune_info["model"]
    for arm in (_trial.DEFAULT, "q15=1", "q15=0", "n=4096", "n=model"):
        p.use_arm(arm)
        assert tuple(p.config) == chain
        assert p.arm_config(arm)[0] == chain
    if mf._q15_available(chain[0]):
        p.use_arm("q15=1")
        assert p._q15
        p.use_arm("q15=0")
        assert not p._q15
