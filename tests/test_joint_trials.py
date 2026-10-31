"""Joint trials (_trial): block sizes, chains and the Q15 screen decided together by paired
rounds of complete configurations, for banks (time_domain._joint_round) and for plans used on
their own (HierarchicalFilter.run_series)."""
import json
import time

import numpy as np
import pytest

import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank, _choice, _costfile, _settings, _trial
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
        # a plan's arm_config takes the trial lock (its model's screen setting): a round must
        # never resolve an arm while it holds the lock
        assert not _choice._AUTOTUNE_LOCK.locked()
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
    monkeypatch.setattr(time, "perf_counter", c)
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


def test_the_aa_arm_settles_its_round_and_logs_the_joint_trial(clock, monkeypatch, tmp_path):
    """With MF_TRIAL_AA_LOG a round also runs DEFAULT's configuration as the A/A arm, settled
    like every arm; the round returns DEFAULT's own timed run, kept as soon as it is taken
    (before the A/A arm runs when that comes after), the samples are the arms' own runs, and
    the round's record names the joint trial and its work."""
    log = tmp_path / "aa.jsonl"
    monkeypatch.setenv("MF_TRIAL_AA_LOG", str(log))
    conf = {_trial.DEFAULT: "a", "n=4096": "b"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 1.5})
    settled, kept = [], []

    def settle():
        clock.t += 100.0
        settled.append(s.arm_config(s.arm))
    tr = _trial.trial("t|aa", lambda: [_trial.DEFAULT, "n=4096"])
    for _ in range(2):
        res = _trial.run_round(tr, [s], s.replay, 7.0, settle=settle,
                               keep=lambda r: kept.append(len(s.ran)) or r)
        assert res == ("result", "a")
    assert settled == ["a", "b", "a", "a", "b", "a"]    # the A/A arm last, then first
    assert kept == [1, 6]                # DEFAULT's own timed run: first, then last
    assert tr.choice.samples[_trial.DEFAULT] == pytest.approx([1.0, 1.0])
    recs = [json.loads(x) for x in log.read_text().splitlines()]
    assert [(r["kind"], r["key"], r["work"], r["order"]) for r in recs] == [
        ("joint", "joint|t|aa", 7.0, ["default", "n=4096", "A/A"]),
        ("joint", "joint|t|aa", 7.0, ["A/A", "n=4096", "default"])]
    assert [r["A/A"] for r in recs] == pytest.approx([1.0, 1.0])


def test_the_aa_log_names_the_arms_that_ran_alike(clock, monkeypatch, tmp_path):
    """Arms an instance resolves alike run once: the log's order holds the runs made, and
    each arm that shared another's run names it."""
    log = tmp_path / "aa.jsonl"
    monkeypatch.setenv("MF_TRIAL_AA_LOG", str(log))
    conf = {_trial.DEFAULT: "a", "n=4096": "a", "n=model": "c", "q15=0": "a"}
    s = _Subject(clock, conf, {"a": 1.0, "c": 1.5})
    _drive(s, ARMS, rounds=1)
    rec = json.loads(log.read_text().splitlines()[0])
    assert rec["order"] == ["default", "n=model", "A/A"]
    assert rec["shared"] == {"n=4096": "default", "q15=0": "default"}
    assert rec["ratios"] == pytest.approx({"default": 1.0, "n=4096": 1.0, "n=model": 1.5,
                                           "q15=0": 1.0})


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
    assert not _choice.playing()


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
    for _ in range(4 * _choice.rounds()[1]):
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
    seq = iter([0.8] * _choice.rounds()[0] + [1.0] * 40)        # fast at first only

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
    """Every dimension's arms read back to themselves (_settings: one grammar for every trial),
    one move or several in DIMS order; a label that names no dimension or no value, or spells
    an arm out of order, is not an arm."""
    for label in (_settings.DEFAULT, "n=2048", "n=model", "q15=1", "q15=0",
                  "single=cpu", "side=cpu", "kern:coarse:256=tierb_256_c16w@64",
                  "n=4096,q15=0", "single=cpu,kern:coarse:256=tierb_256_c16w@64"):
        assert _settings.compose(_settings.moves(label)) == label
    assert _settings.moves("n=4096,q15=0") == {"n": 4096, "q15": False}
    for bad in ("chain=2048:256", "chain=+1", "blocks=2", "q15=2", "single=tpu", "n=", "fuse=0",
                "q15=0,n=4096", "n=4096,n=2048", "n=4096,"):
        with pytest.raises(ValueError):                    # chains are never arms
            _settings.moves(bad)


def test_a_pass_offers_the_winner_with_each_undecided_dimension_moved():
    proposals = ["n=4096", "n=model", "q15=1", "q15=0"]
    assert _settings.around(_trial.DEFAULT, proposals) == [_trial.DEFAULT] + proposals
    assert _settings.around("n=4096", proposals) == ["n=4096", "n=4096,q15=1", "n=4096,q15=0"]
    assert _settings.around("n=4096,q15=0", proposals) == ["n=4096,q15=0"]


def test_a_move_that_wins_only_after_another_is_found_by_the_next_pass(clock):
    """The screen off loses at the default size and wins at n=4096: the first pass locks
    n=4096, the pass around it locks the screen off there, and the search ends on both."""
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "q15=0": "c", "n=4096,q15=0": "d"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.8, "c": 1.2, "d": 0.6})
    tr, _ = _drive(s, ["n=4096", "q15=0"])
    assert tr.winner == "n=4096,q15=0" and s.locked == tr.winner
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.8, "c": 1.2, "d": 0.82})
    mf.clear_autotune_cache()
    tr, _ = _drive(s, ["n=4096", "q15=0"])                 # a tie around n=4096 keeps it
    assert tr.winner == "n=4096" and s.locked == "n=4096"


def test_each_pass_is_kept_and_an_open_pass_is_resumed(clock, monkeypatch, tmp_path):
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    conf = {_trial.DEFAULT: "a", "n=4096": "b", "n=4096,q15=0": "d"}
    s = _Subject(clock, conf, {"a": 1.0, "b": 0.8, "d": 0.6})
    tr = _trial.trial("t|unit", lambda: ["n=4096", "q15=0"])
    while tr.base == _trial.DEFAULT:
        _trial.run_round(tr, [s], s.replay, 1.0)
    assert tr.winner is None and tr.base == "n=4096"
    _trial.clear()
    assert _trial.winner("t|unit") is None                 # the pass around n=4096 is open
    tr = _trial.trial("t|unit", lambda: ["n=4096", "q15=0"])
    assert tr.base == "n=4096"                             # resumed there, not from DEFAULT
    while tr.winner is None:
        _trial.run_round(tr, [s], s.replay, 1.0)
    _trial.clear()
    assert _trial.winner("t|unit") == "n=4096,q15=0"


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
    assert [a for a in arms if a.startswith("n=")] == [_settings.arm("n", n) for n in bank._trial_cands[1:]]
    assert bank._layout_rank == bank._arm_rank(_trial.DEFAULT) == 0     # the smallest size
    assert {n for _, n in bank.chosen_layout} == {bank._trial_cands[0]}
    assert all(p._governed for p in bank._layout_plans(0))              # the bank's trial governs


@pytest.mark.parametrize("aa", [False, True])
def test_a_banks_trial_runs_without_a_cost_file_switches_exactly_and_locks(aa, monkeypatch,
                                                                           tmp_path):
    """Without MF_COST_FILE a bank's real calls are the trial's rounds; every arm reports the
    same triggering templates as an untrialled bank; the trial locks, and a later bank
    builds only the winner's layout. With the A/A diagnostic too, which logs every round
    and the lock."""
    log = tmp_path / "aa.jsonl"
    if aa:
        monkeypatch.setenv("MF_TRIAL_AA_LOG", str(log))
    bank, rng = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    plain, _ = _inspiral_bank()
    plain._in_trial = False
    data = _data(rng)
    ref = set(np.unique(plain.filter_series(data).template_indices))
    for _ in range(2 * _choice.rounds()[1] + 1):
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
    if aa:
        recs = [json.loads(x) for x in log.read_text().splitlines()]
        rounds = [r for r in recs if r["event"] == "round"]
        assert rounds and all(r["A/A"] > 0 and r["kind"] == "joint" for r in rounds)
        assert rounds[-1]["winner"] == w
        assert [r["value"] for r in recs if r["event"] == "lock"][-1] == w


def test_a_bank_adopts_a_persisted_lock_without_pricing(monkeypatch, tmp_path):
    """A lock on file applies at the bank's first reference: no trial, and for a lock that
    fixes no block size, no block-size pricing -- the default (smallest) size alone."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    bank, _ = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    key = td._trial_key(bank)
    smallest = bank._trial_cands[0]
    for k in ("choice|joint|" + key, "choice|joint|%s|q15=0" % key):          # a finished search
        _costfile._store_cost(str(tmp_path / "costs.json"), k, {"value": "q15=0"})
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
    tr.choice.lock(_settings.arm("n", other))
    tr.choice.lock(tr.base)                               # the pass around it keeps it
    assert tr.winner == _settings.arm("n", other)
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
    if not mf._hierarchical._q15_available(256):
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
    if mf._hierarchical._q15_available(chain[0]):
        p.use_arm("q15=1")
        assert p._q15
        p.use_arm("q15=0")
        assert not p._q15


def _settle_run(times, builds):
    """_settle over replays taking times[i] and building builds[i] recordings."""
    from matchedfilter import time_domain
    now, made, i = [0.0], [0], [0]

    def replay():
        now[0] += times[i[0]]
        made[0] += builds[i[0]]
        i[0] += 1
    return time_domain._settle(replay, lambda: made[0], clock=lambda: now[0])


def test_a_gpu_batch_settles_to_a_steady_time_not_only_to_no_builds():
    """A joint round's settle on a GPU replays until a replay builds nothing AND runs within
    half the tie of the one before: a batch that has built everything can still run 10-25%
    slower for a replay or two (dev3), and settled by builds alone the arm played first in a
    round read 14-21% slower than the same configuration played later."""
    # builds on the first replay, then runs slower for two more before it is steady
    assert _settle_run([10.0, 8.0, 6.5, 5.0, 5.05], [3, 0, 0, 0, 0]) == 5
    # steady at once after the build: two replays
    assert _settle_run([10.0, 5.0, 5.0], [3, 0, 0]) == 3
    assert _settle_run([5.0, 5.0], [0, 0]) == 2
    # a replay within the tolerance that built something is not steady state
    assert _settle_run([5.0, 5.0, 5.0], [0, 1, 0]) == 3
    # never steady: bounded
    from matchedfilter import time_domain
    assert _settle_run([10.0, 5.0, 10.0, 5.0, 10.0, 5.0], [0] * 6) == time_domain._SETTLE_REPLAYS
    assert time_domain._SETTLE_TOL == pytest.approx(0.025)


def test_get_autotune_state_does_not_deadlock_on_single_arm_trial():
    mf.clear_autotune_cache()
    _trial.trial("t|single_arm", lambda: [_trial.DEFAULT])
    state = mf.get_autotune_state()
    assert state["trials"]["t|single_arm"]["winner"] == _trial.DEFAULT


def test_held_playing_flag_is_thread_local():
    import threading
    other_saw = []
    ready = threading.Event()
    proceed = threading.Event()

    def worker():
        ready.wait(timeout=5.0)
        other_saw.append(_choice.playing())
        proceed.set()

    t = threading.Thread(target=worker)
    t.start()
    with _choice.held():
        assert _choice.playing() is True
        ready.set()
        proceed.wait(timeout=5.0)
    t.join(timeout=5.0)
    assert other_saw == [False]
    assert _choice.playing() is False
