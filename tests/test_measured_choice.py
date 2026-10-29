"""Measured choices outside a filter's joint trial: the GPU-or-CPU side of lone single-template
calls (a paired choice played on the calls) and the offline screens that give the device trial
its kernel shortlists (_coarse.screen, shortlist). Deterministic fake timers, no real timing."""
from matchedfilter import gatechain as gc


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
    each backend this install carries (_kernel_dirs: no PTX on macOS, no Metal elsewhere):
    the identity of the programs its manifest records, which a change to any one moves."""
    from matchedfilter import _kernel_dirs, _kernel_id
    ids = {}
    for backend, (folder, _, _) in _kernel_id.BACKENDS.items():
        if folder not in _kernel_dirs.shipped():
            continue
        ids[backend] = gc.gpu_kernel_id(backend)
        assert ids[backend] == _kernel_id._digest(backend, _kernel_id._ids(backend))
        assert len(_kernel_id._ids(backend)) > 100
    assert len(set(ids.values())) == len(ids)


def test_a_burst_during_one_stage_does_not_order_the_shortlist():
    """The Iris Xe case: the untiled layouts were timed while other work held the shared
    GPU, the tiled ones after it ended, and the store kept a tiled layout 4.3x slower.
    Interleaved rounds put a burst into one round of every candidate, and the screen times
    its fastest few again together, so a burst that covered a whole stage cannot order them."""
    from matchedfilter import _coarse
    true = {"u1": 1.0, "u2": 1.1, "t2": 4.3}
    clock = {"n": 0, "burst": range(0, 6)}         # the first six timings run 5x slow

    def time_one(c):
        k = clock["n"]
        clock["n"] += 1
        return true[c] * (5.0 if k in clock["burst"] else 1.0)
    out = _coarse.screen([["u1", "u2"], ["t2"]], time_one, rounds=3)
    assert sorted(out, key=out.get)[:2] == ["u1", "u2"]


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


def test_the_screen_offers_later_stages_the_earlier_times():
    from matchedfilter import _coarse
    true = {"u1": 1.0, "u2": 2.0, "t1": 0.5, "t2": 3.0}
    seen = []

    def stage2(times):
        seen.append(dict(times))
        return ["t1", "t2"] if min(times, key=times.get) == "u1" else []
    out = _coarse.screen([["u1", "u2"], stage2], lambda c: true[c],
                         time_screen=lambda c: true[c], rounds=2)
    assert set(seen[0]) == {"u1", "u2"} and min(out, key=out.get) == "t1"


def test_a_shortlist_is_screened_once_stored_and_read_back_whole(monkeypatch, tmp_path):
    """The fastest two of a screen (_coarse.shortlist) are stored with the kernels' identity:
    a later process reads both back untimed, so its device trial still plays them; ties break
    by the tiebreak; a device that cannot be timed runs the first candidate, unstored."""
    from matchedfilter import _coarse
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    calls = []

    def measure(cs):
        calls.append(list(cs))
        return {"a": 2.0, "b": 1.0, "c": 1.0}
    pick = lambda memo: _coarse.shortlist(memo, "t-kind", "dev", 256, ["a", "b", "c"], str,
                                          "k1", measure, tiebreak=lambda c: (-ord(c),))
    assert pick({}) == ("c", "b") and len(calls) == 1      # tie b/c broken by the tiebreak
    assert pick({}) == ("c", "b") and len(calls) == 1      # a new process: read back untimed
    memo = {}
    assert _coarse.shortlist(memo, "t-kind", "dev", 256, ["a", "b"], str, "k2",
                             lambda cs: None) == ("a", None)   # untimeable: first, unstored
    assert _coarse.shortlist(memo, "t-kind", "dev", 256, ["a", "b"], str, "k2",
                             measure) == ("b", "a")            # (then timed: stored)


def test_a_forced_layout_is_taken_untimed_unstored_and_must_exist(monkeypatch, tmp_path):
    """MF_COARSE_LAYOUT names one layout per band (_coarse.forced_layout); the shortlist is it
    alone, untimed and unstored (no trial plays it), and a name that is not a candidate
    raises."""
    from matchedfilter import _coarse
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "c.json"))
    monkeypatch.setenv("MF_COARSE_LAYOUT", "tierb_256_c16p2t2w@16, tierb_512_c16p2t4")
    assert _coarse.forced_layout(256) == "tierb_256_c16p2t2w@16"
    assert _coarse.forced_layout(512) == "tierb_512_c16p2t4"
    assert _coarse.forced_layout(1024) is None
    assert _coarse.layout_label(256, 2, 2, 1, 16) == "tierb_256_c16p2t2w@16"
    assert _coarse.layout_label(512, 1, 1, 0) == "tierb_512_c16"
    names = ["tierb_256_c16@16", "tierb_256_c16p2t2w@16"]
    memo = {}

    def measure(cs):
        raise AssertionError("a forced layout is not timed")
    assert _coarse.shortlist(memo, "t-force", "dev", 256, names, str, "k", measure,
                             forced=_coarse.forced_layout(256)) == (names[1], None)
    assert not memo and not (tmp_path / "c.json").exists()
    with pytest.raises(ValueError, match="tierb_256_c16@16"):
        _coarse.shortlist(memo, "t-force", "dev", 256, names[:1], str, "k", measure,
                          forced="tierb_256_c16p2t2w@16")
