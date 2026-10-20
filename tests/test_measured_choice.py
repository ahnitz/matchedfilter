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


def test_steady_state_reopens_a_contradicted_choice_once(monkeypatch):
    monkeypatch.setenv("MF_TRIAL_RECHECK", "1")              # opt-in (off by default)
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
    return p._chain_trial_key()


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


def _drive_batches(tk, true, never=(), limit=200):
    """Drive a GPU chain trial batch by batch, as time_domain does: the scheduler picks a
    candidate, its batches after a 2-batch warm-up are samples -- except for candidates in
    `never`, whose batches never come back (a plan that cannot run them)."""
    from matchedfilter.time_domain import _CHAIN_WARM_BATCHES as warm
    last, run = None, 0
    for i in range(limit):
        c = mf._chain_trial_next(tk)
        if c is None:
            return mf._CHAIN_TRIALS[tk]["winner"], i
        run = run + 1 if c == last else 1
        last = c
        if run > warm and c not in never:
            mf._chain_trial_batch(tk, c, true[c])
    return None, limit


def test_a_candidate_that_never_runs_still_yields_a_lock(monkeypatch, tmp_path):
    """Metal: the trial waited on a candidate whose batches never came. It is dropped after
    its warm-up and samples (+2) without one, and the contest goes on without it."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    tk = (2048, 6.0, 0.001, 2, "gpu:0")
    a, b, c = (256, 512), (256, 1024), (256,)
    mf._CHAIN_TRIALS[tk] = {"samples": {a: [], b: [], c: []}, "assigned": {}, "winner": None}
    w, batches = _drive_batches(tk, {a: 1.0e-12, b: 1.3e-12, c: 0.8e-12}, never=(c,))
    assert w == a
    assert c in mf._CHAIN_TRIALS[tk]["dropped"]
    base = mf._CHAIN_BATCH_TRIALS
    assert batches <= 3 * (2 + base) + 6 + 1               # within the batch budget


def test_a_full_trial_locks_within_its_batch_count(monkeypatch, tmp_path):
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    tk = (2048, 6.0, 0.001, 2, "gpu:0")
    a, b, c = (256, 512), (256, 1024), (256,)
    mf._CHAIN_TRIALS[tk] = {"samples": {a: [], b: [], c: []}, "assigned": {}, "winner": None}
    w, batches = _drive_batches(tk, {a: 1.0e-12, b: 1.3e-12, c: 0.8e-12})
    assert w == c                                          # the measured best
    assert batches <= 3 * (2 + mf._CHAIN_BATCH_TRIALS) + 1


def _single_contest(monkeypatch, tmp_path, timer, calls=40):
    """Drive TimeDomainFilterBank._single_device (the GPU-or-CPU choice of single-template
    calls) on fake banks with a deterministic timer; returns the shape's state."""
    from types import SimpleNamespace
    from matchedfilter import device as _device
    from matchedfilter import time_domain as td
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setenv("MF_AUTOTUNE", "1")
    monkeypatch.delenv("MF_SINGLE_DEVICE", raising=False)
    monkeypatch.setattr(_device, "parse", lambda spec: SimpleNamespace(kind="gpu"))
    from matchedfilter import _choice
    monkeypatch.setattr(_choice, "_CHOICES", {})
    bank, g = SimpleNamespace(device="gpu:0"), SimpleNamespace(n=2048)
    k = {"gpu": 0, "cpu": 0}
    for _ in range(calls):
        on_cpu, rec = td.TimeDomainFilterBank._single_device(bank, g, 24)
        if rec is None:
            break
        side = "cpu" if on_cpu else "gpu"
        rec(timer(side, k[side]))
        k[side] += 1
    (state,) = _choice.of_kind("single-device").values()
    return td, bank, g, state


def test_single_template_device_choice_follows_the_shared_rule_and_persists(monkeypatch, tmp_path):
    """The GPU-or-CPU choice of single-template calls decides by measured_choice and keeps its
    lock in MF_COST_FILE: a clear CPU win locks the CPU, and the next process reuses it untimed."""
    td, bank, g, state = _single_contest(
        monkeypatch, tmp_path, lambda side, i: (1.0 if side == "gpu" else 0.4) * (1 + 0.01 * (i % 3)))
    assert state.winner == "cpu"
    from matchedfilter import _choice
    _choice.reset()                                # a new process: the stored side, no trial
    assert td.TimeDomainFilterBank._single_device(bank, g, 24) == (True, None)


def test_single_template_device_unclear_contest_keeps_the_banks_device(monkeypatch, tmp_path):
    """A CPU 'win' inside the noise samples further, up to the cap, then the bank's own device
    (the GPU) stands -- a bare median rule picked whichever side the noise favoured."""
    seq = {"gpu": [5.0, 1.0, 1.3, 0.8, 1.25, 0.85, 1.0, 1.1],     # first: warm-up, dropped
           "cpu": [5.0, 0.8, 1.2, 0.85, 1.3, 0.75, 1.15, 0.9]}
    td, _, _, state = _single_contest(monkeypatch, tmp_path, lambda side, i: seq[side][i])
    assert state.winner == "gpu"
    assert len(state.samples["gpu"]) - state.warmup == state.cap


def test_a_lock_the_model_kept_is_not_reopened_by_its_own_steady_state(monkeypatch):
    """The model's candidate stood because the contest was unclear, with a worse trial median
    than the runner-up. Steady samples like its own trial median must not reopen it (they
    did, against the runner-up's median: the L40S two-process flake)."""
    monkeypatch.setenv("MF_TRIAL_RECHECK", "1")
    st = {"winner": "model", "median": {"model": 2.23e-10, "other": 1.76e-10}}
    for _ in range(3 * gc.RECHECK_N):
        assert not gc.observe_steady(st, 2.3e-10, lambda: None)
    st2 = {"winner": "model", "median": {"model": 2.23e-10, "other": 1.76e-10}}
    got = [gc.observe_steady(st2, 3.2e-10, lambda: None) for _ in range(gc.RECHECK_N)]
    assert got[-1]                                         # 43% over its own: a real mistake


def test_a_stored_lock_decides_every_plan_of_the_key(monkeypatch, tmp_path):
    """The first plan of the key cannot run the locked chain (not in its feasible set): it runs
    its model's chain, opens no trial, and every later plan of the key still adopts the
    lock. Before, the first plan cached "no lock" and the others re-trialled."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    mf.clear_autotune_cache()
    shape_a, shape_b = [300, 400, 500, 600] * 4, [700, 800, 850, 880] * 4
    pb = _hier_plan(shape_b)                              # learn B's key and feasible chains
    key_b = next(iter(mf._CHAIN_CHOICE))
    model_b, shortlist_b, feasible_b = mf._CHAIN_CHOICE[key_b]
    lock = next((c for c in feasible_b if c != model_b), None)
    if lock is None:
        pytest.skip("one feasible chain only")
    pa = _hier_plan(shape_a)
    key_a = next(k for k in mf._CHAIN_CHOICE if k != key_b)
    tk = _tkey(pb)
    assert _tkey(pa) == tk                                # one lock key, two group shapes
    model_a, shortlist_a, feasible_a = mf._CHAIN_CHOICE[key_a]
    mf._store_chain_lock(tk, lock)                         # what an earlier process locked
    # A new process in which shape A's feasible set lacks the locked chain:
    choices = {key_a: (model_a, tuple(c for c in shortlist_a if c != lock) or (model_a,),
                       tuple(c for c in feasible_a if c != lock)),
               key_b: (model_b, shortlist_b, feasible_b)}
    mf.clear_autotune_cache()
    monkeypatch.setattr(mf, "_CHAIN_CHOICE", dict(choices))
    qa = _hier_plan(shape_a)                               # first plan of the key: cannot run it
    assert qa._chain_trial is None                         # a locked key opens no trial
    assert tuple(qa._chain) == tuple(choices[key_a][0])    # its model's chain
    qb = _hier_plan(shape_b)                               # a later plan of the key
    assert tuple(qb._chain) == tuple(lock)
    assert qb._chain_trial is None


def test_the_steady_recheck_is_off_by_default(monkeypatch):
    """A re-check verdict from one process's timing reopens the lock for every later process,
    so two processes on one cost file can disagree (L40S 2 of 10, macOS Metal CI): off unless
    MF_TRIAL_RECHECK=1, and a stored lock is final until the cost file is deleted."""
    monkeypatch.delenv("MF_TRIAL_RECHECK", raising=False)
    st = {"winner": "b", "median": {"a": 1.0, "b": 0.7}}
    calls = []
    for _ in range(10 * gc.RECHECK_N):
        assert not gc.observe_steady(st, 5.0, lambda: calls.append(1))
    assert calls == [] and not st.get("rechecked")


def test_gpu_kernel_choices_carry_their_backend_artifacts():
    """CUDA-only kernels and compiled Metal libraries have their own build identity."""
    import json, pathlib
    package = pathlib.Path(gc.__file__).parent
    for backend, folder, field in (("vulkan", "spirv", "build_id"),
                                   ("cuda", "ptx", "build_id"),
                                   ("metal", "spirv", "metal_build_id")):
        manifest = json.loads((package / folder / "manifest.json").read_text())
        assert gc.gpu_kernel_id(backend) == manifest[field][:16]


def test_a_burst_during_one_stage_does_not_decide_a_coarse_layout():
    """The Iris Xe case: the untiled layouts were timed while other work held the shared
    GPU, the tiled ones after it ended, and the store kept a tiled layout 4.3x slower.
    Interleaved rounds put a burst into one round of every candidate, and the paired
    confirmation of each stage's fastest undoes a burst that covered a whole stage."""
    from matchedfilter import _coarse
    true = {"u1": 1.0, "u2": 1.1, "t2": 4.3}
    clock = {"n": 0, "burst": range(0, 6)}         # the first six timings run 5x slow

    def time_one(c):
        k = clock["n"]
        clock["n"] += 1
        return true[c] * (5.0 if k in clock["burst"] else 1.0)

    untiled = _coarse.interleaved_min(["u1", "u2"], time_one, 3)   # 6 timings: all in the burst
    assert untiled["u1"] > true["t2"]                               # the trap
    tiled = _coarse.interleaved_min(["t2"], time_one, 3)
    times = dict(untiled, **tiled)
    assert min(times, key=times.get) == "t2"
    times = _coarse.confirm_fastest(times, time_one, rivals=["u1", "t2"])
    assert min(times, key=times.get) == "u1"
    assert abs(times["u1"] / times["t2"] - true["u1"] / true["t2"]) < 1e-9


def test_interleaved_rounds_take_each_candidates_best_round():
    from matchedfilter import _coarse
    seq, calls = iter([5.0, 2.0, 1.0, 3.0, 4.0, 4.0]), []

    def time_one(c):
        calls.append(c)
        return next(seq)

    t = _coarse.interleaved_min(["a", "b"], time_one, 3)
    assert calls == ["a", "b", "b", "a", "a", "b"]          # the order reverses each round
    assert t == {"a": 3.0, "b": 1.0}
    assert _coarse.interleaved_min(["a"], lambda c: None, 2) is None


def test_stored_measured_choice_measures_once_stores_and_breaks_ties(monkeypatch, tmp_path):
    """Every backend's coarse choice (_coarse.stored_measured_choice): the fastest is stored
    under its label and the kernels' identity; a later process reads it back untimed; an
    unmeasurable device runs the first candidate, unstored; ties break deterministically."""
    from matchedfilter import _coarse
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    calls = []

    def measure(cs):
        calls.append(list(cs))
        return {"a": 2.0, "b": 1.0, "c": 1.0}
    pick = lambda memo: _coarse.stored_measured_choice(
        memo, "t-kind", "dev", 256, ["a", "b", "c"], str, "k1", measure,
        tiebreak=lambda c: (-ord(c),))
    assert pick({}) == "c" and len(calls) == 1          # tie b/c broken by the tiebreak
    assert pick({}) == "c" and len(calls) == 2          # a new process: read back, re-checked
    assert sorted(calls[1]) == ["a", "b", "c"]          # against the stored runners-up
    memo = {}
    assert _coarse.stored_measured_choice(memo, "t-kind", "dev", 256, ["a", "b"], str, "k2",
                                          lambda cs: None) == "a"   # unmeasurable: first
    assert _coarse.stored_measured_choice(memo, "t-kind", "dev", 256, ["a", "b"], str, "k2",
                                          measure) == "a"          # memo by labels


def test_time_staged_offers_later_stages_the_earlier_times():
    from matchedfilter import _coarse
    true = {"u1": 1.0, "u2": 2.0, "t1": 0.5, "t2": 3.0}
    seen = []

    def stage2(times):
        seen.append(dict(times))
        return ["t1", "t2"] if min(times, key=times.get) == "u1" else []
    out = _coarse.time_staged([["u1", "u2"], stage2], lambda c: true[c],
                              time_screen=lambda c: true[c], rounds=2)
    assert set(seen[0]) == {"u1", "u2"} and min(out, key=out.get) == "t1"


def test_a_close_call_goes_to_the_preference_not_the_noise():
    """confirm_fastest marks a contender whose paired ratio to the fastest is within the
    measurement's noise; stored_measured_choice then takes the backend's preference, so the
    choice does not flip with the noise. A real difference still picks the fastest."""
    from matchedfilter import _coarse
    noise = iter([1.000, 1.002, 0.999, 1.001, 1.000, 0.998, 1.001, 1.000, 1.000, 1.001] * 4)
    true = {"pref": 1.000, "fast": 0.999, "slow": 1.10}
    t = _coarse.confirm_fastest({"pref": 1.0, "fast": 0.999, "slow": 1.1},
                                lambda c: true[c] * next(noise), rivals=["slow"])
    assert "pref" in t.close and "slow" not in t.close
    pick = _coarse.stored_measured_choice({}, "t-close", "dev", 1, ["pref", "fast", "slow"],
                                          str, "k", lambda cs: t)
    assert pick == "pref"
    real = _coarse.Timings({"pref": 1.0, "fast": 0.9})
    assert _coarse.stored_measured_choice({}, "t-close2", "dev", 1, ["pref", "fast"], str, "k",
                                          lambda cs: real) == "fast"


def test_a_forced_layout_is_taken_untimed_unstored_and_must_exist(monkeypatch, tmp_path):
    """MF_COARSE_LAYOUT names one layout per band (_coarse.forced_layout); the choice takes
    it without timing or storing it, and a name that is not a candidate raises."""
    from matchedfilter import _coarse
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    monkeypatch.setenv("MF_COARSE_LAYOUT", "tierb_256_c16p2t2w@16, coarse_tc_512_w4")
    assert _coarse.forced_layout(256) == "tierb_256_c16p2t2w@16"
    assert _coarse.forced_layout(512) == "coarse_tc_512_w4"
    assert _coarse.forced_layout(1024) is None
    assert _coarse.layout_label(256, 2, 2, 1, 16) == "tierb_256_c16p2t2w@16"
    assert _coarse.layout_label(512, 1, 1, 0) == "tierb_512_c16"
    names = ["tierb_256_c16@16", "tierb_256_c16p2t2w@16"]
    memo = {}

    def measure(cs):
        raise AssertionError("a forced layout is not timed")
    assert _coarse.stored_measured_choice(memo, "t-force", "dev", 256, names, str, "k", measure,
                                          forced=_coarse.forced_layout(256)) == names[1]
    assert not memo and not (tmp_path / "c.json").exists()
    with pytest.raises(ValueError, match="tierb_256_c16@16"):
        _coarse.stored_measured_choice(memo, "t-force", "dev", 256, names[:1], str, "k",
                                       measure, forced="tierb_256_c16p2t2w@16")


def test_a_stored_choice_is_rechecked_against_its_runners_up(monkeypatch, tmp_path):
    """A process reading a stored choice back times it against the two stored runners-up;
    it keeps the choice when it is still the fastest, and measures everything again when a
    runner-up is clearly faster (a measurement spoiled by a clock change is not kept)."""
    from matchedfilter import _coarse, gatechain
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    true = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    calls = []

    def measure(cs):
        calls.append(sorted(cs))
        return _coarse.Timings({c: true[c] for c in cs})
    pick = lambda: _coarse.stored_measured_choice({}, "t-recheck", "dev", 256, list("abcd"),
                                                  str, "k", measure)
    assert pick() == "a" and calls == [list("abcd")]
    assert pick() == "a" and calls[1:] == [list("abc")]          # re-checked, kept
    ckey = "t-recheck|dev|256|a;b;c;d|kk"
    gatechain.store_choice(ckey, "d", rivals="a;b")               # a spoiled measurement
    calls.clear()
    assert pick() == "a" and calls == [list("abd"), list("abcd")]   # re-measured
    assert gatechain.stored_choice(ckey) == "a"


def test_a_recheck_that_does_not_time_the_choice_measures_everything(monkeypatch, tmp_path):
    """A backend's staged timing may skip a candidate; a re-check whose result lacks the
    stored choice cannot vouch for it, so everything is measured again."""
    from matchedfilter import _coarse, gatechain
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    calls = []

    def measure(cs):
        calls.append(sorted(cs))
        return _coarse.Timings({c: 1.0 + ord(c) for c in cs if c != "c"})   # never times c
    ckey = "t-untimed|dev|256|a;b;c|kk"
    gatechain.store_choice(ckey, "c", rivals="a;b")
    pick = _coarse.stored_measured_choice({}, "t-untimed", "dev", 256, list("abc"), str, "k",
                                          measure)
    assert pick == "a" and calls == [list("abc"), list("abc")]
