"""The one rule every measured choice follows (gatechain.measured_choice, observe_steady):
block-size trials, Q15 screen trials, and chain trials on the CPU (per call) and the GPU
(per batch). Deterministic fake timers, no real timing."""
import numpy as np

from matchedfilter import gatechain as gc


def _drive(true, noise, model, cap, base=2, limit=200):
    """Sample every candidate to its required count from a deterministic timer and apply the
    rule until it decides; returns (winner, samples per candidate)."""
    k = {c: 0 for c in true}
    smp = {c: [] for c in true}
    need = {c: base for c in true}
    for _ in range(limit):
        for c in true:
            while len(smp[c]) < need[c]:
                smp[c].append(true[c] * (1.0 + noise[c][k[c] % len(noise[c])]))
                k[c] += 1
        w, more = gc.measured_choice(smp, model, cap)
        if w is not None:
            return w, {c: len(v) for c, v in smp.items()}
        need.update(more)
    raise AssertionError("never decided")


def test_faster_on_two_noisy_samples_but_slower_in_truth_keeps_the_model():
    """The M2 case: candidate 'b' is 10% slower in truth, but its first two samples are 5.7%
    faster than the model's -- past TIE. A bare median rule locks 'b'; this one sees the gap
    inside the noise, samples further, and keeps the model's candidate."""
    true = {"a": 1.0, "b": 1.10}
    noise = {"a": [0.0, 0.10, 0.02, 0.03, -0.01, 0.0], "b": [-0.155, -0.045, 0.01, 0.0, 0.02, -0.01]}
    two = {c: [true[c] * (1 + noise[c][i]) for i in (0, 1)] for c in true}
    assert np.median(two["b"]) < np.median(two["a"]) * (1 - gc.TIE)     # the trap
    w, n = _drive(true, noise, "a", cap=6)
    assert w == "a" and n["b"] > 2


def test_a_clear_win_locks_on_the_first_samples():
    w, n = _drive({"a": 1.0, "b": 0.7}, {"a": [0.0, 0.01], "b": [0.0, 0.01]}, "a", cap=6)
    assert w == "b" and n == {"a": 2, "b": 2}


def test_an_unclear_contest_ends_with_the_model_at_the_cap():
    # 8% apart with +-15% noise: never clear, so the model stands after cap samples each.
    cyc = [0.0, 0.15, -0.15, 0.0]
    w, n = _drive({"a": 1.0, "b": 0.92}, {"a": cyc, "b": cyc}, "a", cap=6)
    assert w == "a" and min(n.values()) >= 6


def test_a_tie_keeps_the_model_without_more_samples():
    w, n = _drive({"a": 1.0, "b": 0.98}, {"a": [0.0], "b": [0.0]}, "a", cap=6)
    assert w == "a" and n == {"a": 2, "b": 2}


def test_an_unusable_model_candidate_never_stands():
    smp = {"a": [float("inf"), float("inf")], "b": [1.0, 1.5]}
    assert gc.measured_choice(smp, "a", 6) == ("b", {})


def test_steady_state_reopens_a_contradicted_choice_once():
    st = {"winner": "b", "median": {"a": 1.0, "b": 0.7}}
    calls = []
    for _ in range(gc.RECHECK_N - 1):
        assert not gc.observe_steady(st, 0.72, lambda: calls.append(1))
    assert not gc.observe_steady(st, 0.72, lambda: calls.append(1))   # agrees: no reopen
    st2 = {"winner": "b", "median": {"a": 1.0, "b": 0.7}}
    got = [gc.observe_steady(st2, 1.5, lambda: calls.append(1)) for _ in range(gc.RECHECK_N)]
    assert got[-1] and calls == [1]
    for _ in range(3 * gc.RECHECK_N):                                   # once per choice
        assert not gc.observe_steady(st2, 2.0, lambda: calls.append(1))
    assert calls == [1]


# ---- chain trials across processes ---------------------------------------------------------

import pytest                                   # noqa: E402

import matchedfilter as mf                      # noqa: E402
from matchedfilter import TimeDomainFilterBank  # noqa: E402


def _hier_plan(counts, seed=5):
    rng = np.random.default_rng(seed)
    rate, df = 2048.0, 1.0 / 16
    f = np.arange(int(rate / 2 / df) + 1) * df
    w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
    taps = []
    for c in counts:
        ff = np.fft.rfftfreq(c, 1 / rate)
        h = np.fft.irfft(np.sqrt(np.interp(ff, f, w)) * np.exp(2j * np.pi * rng.random(ff.size)), c)
        taps.append((h / np.linalg.norm(h)).astype(np.float32))
    bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.5,
                                false_dismissal=0.001, binsize=256, fft_lengths=[2048])
    bank.set_reference(w, delta_f=df)
    g = next(g for g in bank._groups if g.is_hier)
    p = g.plan
    p._ensure()
    return p


def _tkey(p):
    tiers = min(p.max_tiers, p._MAX_TIERS[p.device.kind])
    return (p.n, float(p._fs_snr or p.snr), float(p.fd), tiers, str(p.device))


@pytest.mark.parametrize("shape", [(300, 400, 500, 600), (700, 800, 850, 880)])
def test_a_stored_lock_applies_whatever_this_groups_shortlist(monkeypatch, tmp_path, shape):
    """Two processes, different group shapes, one lock key: the second adopts the chain the
    first locked even when that chain is not on its own shortlist (or its shortlist is one
    chain), as long as the gate model covers it for this plan."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    p = _hier_plan(list(shape) * 4)
    key = next(k for k in mf._CHAIN_CHOICE)
    model, shortlist, feasible = mf._CHAIN_CHOICE[key]
    off = [c for c in feasible if c not in shortlist]
    if not off:
        pytest.skip("every feasible chain is on the shortlist here")
    lock = off[-1]
    mf._store_chain_lock(_tkey(p), lock)                  # what another process locked
    mf.clear_autotune_cache()                             # a new process
    q = _hier_plan(list(shape) * 4)
    assert tuple(q._chain) == tuple(lock)
    assert q._chain_trial is None


def test_a_batch_trial_with_a_never_run_candidate_still_locks(monkeypatch, tmp_path):
    """A GPU batch trial whose third candidate no live plan runs (another process's shortlist)
    decides once its budget is spent, on the candidates it measured."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    tk = (2048, 6.0, 0.001, 2, "gpu:0")
    a, b, c = (256, 1024), (512,), (128, 512)
    mf._CHAIN_TRIALS[tk] = {"samples": {a: [], b: [], c: []}, "assigned": {}, "winner": None}
    base = mf._CHAIN_BATCH_TRIALS
    w = None
    for i in range(10 * base):
        w = mf._chain_trial_batch(tk, a if i % 2 else b, 1.0 if i % 2 else 1.3)
        if w is not None:
            break
    assert w == a                                          # clearly faster than b
    assert i + 1 <= mf._TRIAL_BUDGET * base * 3            # within the budget


def test_a_batch_trial_locks_the_measured_best_through_outliers(monkeypatch, tmp_path):
    """The L40S case: the model's chain (512, 1024) measured 4.05e-12 s/unit, (256, 512)
    3.0e-12, with spikes (the batch after a switch, a host hiccup). The lock is the measured
    best -- the plain-std spread let one spike keep the 26% gap "unclear" until the model's
    slower chain stood."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    tk = (2048, 6.0, 0.001, 2, "gpu:0")
    model, fast, third = (512, 1024), (256, 512), (128, 512)
    mf._CHAIN_TRIALS[tk] = {"samples": {model: [], fast: [], third: []}, "assigned": {},
                            "winner": None}
    true = {model: 4.05e-12, fast: 3.0e-12, third: 5.0e-12}
    noise = [0.9, 0.02, -0.03, 0.01, 0.6, -0.02, 0.03, 0.0]     # spikes at samples 0 and 4
    k = {c: 0 for c in true}
    w = None
    for _ in range(100):
        c = mf._chain_trial_next(tk)
        if c is None:
            break
        w = mf._chain_trial_batch(tk, c, true[c] * (1 + noise[k[c] % len(noise)]))
        k[c] += 1
        if w is not None:
            break
    assert tuple(w) == fast
    med = mf._CHAIN_TRIALS[tk]["median"]
    assert min(med, key=med.get) == fast                       # the lock is the measured best
