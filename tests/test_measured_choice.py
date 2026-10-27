"""The one rule every measured choice follows (gatechain.measured_choice):
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


# ---- measured device and kernel choices ----------------------------------------------------

import pytest                                   # noqa: E402




@pytest.fixture(autouse=True)
def _test_kinds(monkeypatch):
    """The test-only choice kinds below, declared as every kind must be (_choice.SCOPES)."""
    from matchedfilter import _choice
    for kind in ("t-kind", "t-force", "t-close", "t-close2", "t-recheck", "t-untimed"):
        monkeypatch.setitem(_choice.SCOPES, kind, "machine")


def _single_contest(monkeypatch, tmp_path, cost, calls=40):
    """Play the GPU-or-CPU choice of single-template calls (TimeDomainFilterBank._single_choice,
    paired: Choice.play) on a fake bank with a deterministic clock, cost(side, i) seconds for
    a side's i-th run; returns the shape's state."""
    import time
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
    clock, k = [0.0], {"gpu": 0, "cpu": 0}
    monkeypatch.setattr(time, "perf_counter", lambda: clock[0])

    def run(label):
        side = td._side_of(label)
        clock[0] += cost(side, k[side])
        k[side] += 1
        return side
    ch = td._single_choice(bank.device, g.n, 24)
    ran = set()
    for _ in range(calls):
        if ch.winner is not None:
            break
        assert ch.play(run, ran) == "gpu"          # the call's result is the preference's
    (state,) = _choice.of_kind("single-device").values()
    return td, bank, g, state


def test_single_template_device_choice_follows_the_shared_rule_and_persists(monkeypatch, tmp_path):
    """The GPU-or-CPU choice of single-template calls is a paired contest played on the call
    and keeps its lock in MF_COST_FILE: a clear CPU win locks the CPU (after its
    confirmation), and the next process reuses it untimed."""
    td, bank, g, state = _single_contest(
        monkeypatch, tmp_path, lambda side, i: (1.0 if side == "gpu" else 0.4) * (1 + 0.01 * (i % 3)))
    assert state.winner == "side=cpu"
    from matchedfilter import _choice
    _choice.reset()                                # a new process: the stored side, no trial
    assert td.TimeDomainFilterBank._single_device(bank, g, 24) == (True, False)


def test_single_template_device_unclear_contest_keeps_the_banks_device(monkeypatch, tmp_path):
    """A CPU 'win' inside the noise plays further rounds, up to the cap, then the bank's own
    device (the GPU) stands."""
    rng = __import__("numpy").random.default_rng(3)
    td, _, _, state = _single_contest(monkeypatch, tmp_path,
                                      lambda side, i: float(rng.uniform(0.7, 1.3)))
    assert state.winner == "default"


def test_gpu_kernel_choices_carry_their_backend_artifacts():
    """CUDA-only kernels and compiled Metal libraries have their own build identity, for
    each backend this install carries (_kernel_dirs: no PTX on macOS, no Metal elsewhere)."""
    import json, pathlib
    from matchedfilter import _kernel_dirs
    package = pathlib.Path(gc.__file__).parent
    for backend, files, folder, field in (("vulkan", "spirv", "spirv", "build_id"),
                                          ("cuda", "ptx", "ptx", "build_id"),
                                          ("metal", "metal", "spirv", "metal_build_id")):
        if files not in _kernel_dirs.shipped():
            continue
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

