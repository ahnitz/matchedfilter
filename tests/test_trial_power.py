"""tools/trial_power.py: its exact computations against brute force and the library's own rule,
its simulated tests against their stated error, and its reading of an A/A log."""
import importlib.util
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pytest

from matchedfilter import _choice

ROOT = Path(__file__).resolve().parents[1]
_path = ROOT / "tools" / "trial_power.py"
if not _path.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)
_spec = importlib.util.spec_from_file_location("trial_power", _path)
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)


def _library_outcome(wins, minimum, cap):
    """(switched, rounds) of the library's paired rule (paired_choice, then can_still_win) on
    one challenger's win/loss sequence: a win is a round 0.9 of the preference's time, a loss
    one equal to it."""
    model, chal = [], []
    for n, w in enumerate(wins, 1):
        model.append(1.0)
        chal.append(0.9 if w else 1.0)
        got, _ = _choice.paired_choice({"m": model, "c": chal}, "m", cap, minimum=minimum)
        if got is not None:
            return got == "c", n
        if not _choice.can_still_win(chal, model, cap):
            return False, n
    return False, len(wins)


@pytest.mark.parametrize("minimum,cap", [(5, 10), (3, 8), (5, 12)])
def test_the_current_rules_dp_is_the_librarys_rule(minimum, cap):
    """current_dp's switch probability and expected rounds equal those of the library's rule
    summed over every win/loss sequence of the cap's length."""
    hist = [(_library_outcome(seq, minimum, cap), sum(seq)) for seq in
            itertools.product((0, 1), repeat=cap)]
    for p in (0.02, 0.3, 0.5, 0.8):
        sw = sum(p ** w * (1 - p) ** (cap - w) for (s, _), w in hist if s)
        rounds = sum(n * p ** w * (1 - p) ** (cap - w) for (_, n), w in hist)
        got_sw, got_rounds = tp.current_dp(p, minimum, cap)
        assert got_sw == pytest.approx(sw, rel=1e-12, abs=1e-15)
        assert got_rounds == pytest.approx(rounds, rel=1e-12)


def test_the_current_rules_rate_with_confirmation_and_arms():
    q, _ = tp.current_dp(0.3)
    assert tp.current_rate(0.3, 1, confirm=False) == pytest.approx(q)
    assert tp.current_rate(0.3, 1) == pytest.approx(q * q)
    assert tp.current_rate(0.3, 4) == pytest.approx((1 - (1 - q) ** 4) * q)


def _sign_brute(crit, p, cap):
    """(P(reject), expected rounds) of the sequential sign test by enumeration, stopping at a
    rejection, where no later boundary can be met, or at the cap."""
    rej = rounds = 0.0
    for seq in itertools.product((0, 1), repeat=cap):
        w, stop, hit = 0, cap, False
        for n, x in enumerate(seq, 1):
            w += x
            if crit[n] is not None and w >= crit[n]:
                stop, hit = n, True
                break
            if not any(crit[m] is not None and w + (m - n) >= crit[m] for m in range(n + 1, cap + 1)):
                stop = n
                break
        pr = p ** sum(seq) * (1 - p) ** (cap - sum(seq))
        rej += pr * hit
        rounds += pr * stop
    return rej, rounds


@pytest.mark.parametrize("alpha,cap", [(0.05, 10), (0.01, 12), (1e-3, 12)])
def test_the_sign_tests_dp_and_its_boundary(alpha, cap):
    """sign_dp equals enumeration; sign_boundary's test is within alpha and the next nominal
    level is not (it is the largest)."""
    crit, achieved, level = tp.sign_boundary(alpha, 5, cap)
    for p in (0.5, 0.7, 0.95):
        assert tp.sign_dp(crit, p, cap) == pytest.approx(_sign_brute(crit, p, cap), rel=1e-12)
    assert 0 < achieved <= alpha and achieved == pytest.approx(tp.sign_dp(crit, 0.5, cap)[0])
    above = min(t for n in range(5, cap + 1) for t in tp._tails(n) if t > level)
    assert tp.sign_dp(tp.sign_crit(above, 5, cap), 0.5, cap)[0] > alpha


def test_a_fixed_n_sign_test_retested_every_round_inflates_its_error():
    """The critique's numbers: alpha 0.05 at every round from 5 is 0.051 / 0.099 / 0.145 at
    caps 10 / 20 / 40; the group-sequential boundary holds 0.05 at each."""
    got = [tp.naive_sign_alpha(0.05, 5, c) for c in (10, 20, 40)]
    assert [round(v, 3) for v in got] == [0.051, 0.099, 0.145]
    assert all(tp.sign_boundary(0.05, 5, c)[1] <= 0.05 for c in (10, 20, 40))


def test_no_sign_test_exists_in_fewer_rounds_than_its_error_needs():
    """A sign test at alpha needs ceil(log2(1/alpha)) straight wins."""
    assert all(c is None for c in tp.sign_boundary(1e-4, 5, 13)[0])
    assert any(c is not None for c in tp.sign_boundary(1e-4, 5, 14)[0])


def test_the_incremental_wilcoxon_statistic_is_the_direct_one():
    rng = np.random.default_rng(3)
    y = rng.standard_normal((50, 12))
    z = tp._wilcoxon_z(y)
    for n in range(1, 13):
        a = np.abs(y[:, :n])
        ranks = np.argsort(np.argsort(a, axis=1), axis=1) + 1
        w = np.where(y[:, :n] > 0, ranks, 0).sum(axis=1)
        want = (w - n * (n + 1) / 4) / math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        assert z[:, n - 1] == pytest.approx(want)


@pytest.mark.parametrize("stat", ["t", "wilcoxon"])
def test_a_calibrated_sequential_test_holds_its_error_on_fresh_null_draws(stat):
    """Calibrated on one set of null contests, the test rejects alpha of a fresh set (within
    four binomial standard errors), and a 10% gain far more often."""
    rng = np.random.default_rng(5)
    x = rng.standard_t(4, size=4000) * 0.02            # a heavy-tailed null
    alpha, n = 0.01, 40000
    test = tp.calibrate(stat, -rng.choice(x, size=(n, 20)), alpha, 5)
    got, _ = tp.simulate(stat, -rng.choice(x, size=(n, 20)), test, 5)
    assert abs(got - alpha) < 4 * math.sqrt(alpha * (1 - alpha) / n)
    assert tp.simulate(stat, -(math.log(0.9) + rng.choice(x, size=(n, 20))), test, 5)[0] > 0.9


def test_the_log_is_read_into_contests(tmp_path):
    """Records of one process and key split into contests where the round number restarts or
    the phase changes; a pattern that matches nothing raises."""
    def rec(rnd, phase, ratio, pid=1):
        return {"event": "round", "pid": pid, "host": "h", "key": "k", "what": "w", "round": rnd,
                "phase": phase, "aa_ratio": ratio, "load": [1.0, 1.0, 1.0], "preference": "a",
                "order": ["a", "b", "A/A"], "times": {"a": 1.0, "b": 2.0}}
    lines = [rec(1, "contest", 1.01), rec(2, "contest", 0.99), rec(1, "confirm", 1.0),
             rec(2, "confirm", 1.02), rec(1, "contest", 1.0, pid=2),
             {"event": "lock", "pid": 2, "value": "a"}]
    (tmp_path / "a.jsonl").write_text("\n".join(json.dumps(r) for r in lines) + "\n")
    rounds, locks = tp.load([str(tmp_path / "*.jsonl")])
    assert len(rounds) == 5 and len(locks) == 1
    assert [len(c) for c in tp.contests(rounds)] == [2, 2, 1]
    assert tp.log_ratios(rounds) == pytest.approx(np.log([1.01, 0.99, 1.0, 1.02, 1.0]))
    with pytest.raises(FileNotFoundError):
        tp.load([str(tmp_path / "nothing*.jsonl")])


def test_a_gzipped_extract_is_read_and_filtered_by_field(tmp_path):
    """The checked-in evidence form: gzipped records whose ratios are left to be derived
    from the times, each naming its process's log, chosen by a field."""
    import gzip
    recs = [{"event": "round", "set": s, "_file": "h/%s/a" % s, "pid": 1, "host": "h", "key": "k",
             "round": 1, "phase": "contest", "load": [1.0, 1.0, 1.0], "preference": "a",
             "order": ["a", "b", "A/A"], "times": {"a": 2.0, "b": 3.0}, "A/A": 2.2}
            for s in ("offs", "long")]
    path = tmp_path / "rounds.jsonl.gz"
    with gzip.open(path, "wt") as f:
        f.write("\n".join(json.dumps(r) for r in recs) + "\n")
    rounds, _ = tp.load([str(path)], where=lambda r: r["set"] == "long")
    assert len(rounds) == 1 and rounds[0]["_file"] == "h/long/a"
    assert rounds[0]["aa_ratio"] == pytest.approx(1.1)
    assert rounds[0]["ratios"] == pytest.approx({"a": 1.0, "b": 1.5})


def test_a_contest_effect_is_integrated_exactly():
    """with_contest_effect is E[rate(u)] for u ~ N(0, tau^2): exact for polynomials."""
    assert tp.with_contest_effect(lambda u: 3.0 + u, 0.0) == 3.0
    assert tp.with_contest_effect(lambda u: 3.0 + 2 * u, 0.05) == pytest.approx(3.0)
    assert tp.with_contest_effect(lambda u: u * u, 0.05) == pytest.approx(0.0025)
    assert tp.with_contest_effect(lambda u: u ** 4, 0.1) == pytest.approx(3e-4)


def test_a_rounds_cost_counts_every_run_but_the_calls_own():
    """Each configuration that ran is settled and timed (twice its time); the preference's
    timed run is the call's work; arms that ran alike and the A/A arm cost nothing more."""
    r = {"times": {"a": 1.0, "b": 3.0, "c": 1.0}, "shared": {"c": "a"}, "preference": "a", "A/A": 1.1}
    assert tp.round_cost([r]) == pytest.approx(2 * (1.0 + 3.0) - 1.0)


def test_the_interval_brackets_the_rate():
    lo, hi = tp.clopper_pearson(3, 100)
    assert lo == pytest.approx(0.0062299715, rel=1e-6) and hi == pytest.approx(0.0851760530, rel=1e-6)
    assert tp.clopper_pearson(0, 100) == (0.0, pytest.approx(0.0362166926, rel=1e-6))
