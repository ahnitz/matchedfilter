"""Block-size trials (time_domain._BlockTrials): the model's candidate layouts measured end to end."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import time_domain as td
from matchedfilter import gatechain


def _run(factors, samples=2, seed=0, noise=0.05):
    """Per-rank batch times (a factor on 1.0, with noise) through a fresh trial; return the lock."""
    rng = np.random.default_rng(seed)
    tr = td._BlockTrials()
    for _ in range(64):
        if tr.winner("k") is not None:
            break
        r = tr.rank_for("k", len(factors))
        tr.record("k", r, factors[r] * rng.normal(1.0, noise))
    return tr.winner("k")


@pytest.fixture(autouse=True)
def _no_cost_file(monkeypatch):
    monkeypatch.delenv("MF_COST_FILE", raising=False)


@pytest.mark.parametrize("slower", [1.5, 2.0, 10.0])
def test_a_clearly_worse_block_size_is_never_locked(slower):
    for seed in range(20):
        assert _run({0: 1.0, 1: slower, 2: slower}, seed=seed) == 0
        assert _run({0: slower, 1: 1.0, 2: slower}, seed=seed) == 1
        assert _run({0: slower, 1: slower, 2: 1.0}, seed=seed) == 2


def test_a_tie_keeps_the_models_choice():
    assert _run({0: 1.00, 1: 0.99, 2: 1.01}, noise=0.0) == 0     # inside gatechain.TIE
    assert _run({0: 1.00, 1: 0.80, 2: 1.0}, noise=0.0) == 1      # outside it


def test_the_lock_persists_across_processes(monkeypatch, tmp_path):
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    tr = td._BlockTrials()
    for _ in range(16):
        if tr.winner("dev|model,2048,4096") is not None:
            break
        r = tr.rank_for("dev|model,2048,4096", 3)
        tr.record("dev|model,2048,4096", r, {0: 1.0, 1: 0.7, 2: 1.2}[r])
    assert tr.winner("dev|model,2048,4096") == 1
    fresh = td._BlockTrials()                                      # another process
    assert fresh.winner("dev|model,2048,4096") == 1
    assert fresh.rank_for("dev|model,2048,4096", 3) == 1           # no trial runs
    assert fresh.winner("dev|model,4096") is None                  # other candidate sets trial


def _inspiral_bank(seed=5):
    rng = np.random.default_rng(seed)
    counts = list(rng.integers(300, 900, 48))
    rate = 2048.0
    df = 1.0 / 16
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


def test_switching_layouts_is_exact_and_locks(monkeypatch, tmp_path):
    """Every candidate layout reports the same triggering templates, and a lock leaves one."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    bank, rng = _inspiral_bank()
    bank2, _ = _inspiral_bank()
    layouts = getattr(bank, "_layouts", None) or []
    if len(layouts) < 2:
        pytest.skip("the model offered one block size only")
    L = 1 << 16
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    data[30000:30400] += 40 * np.exp(1j * np.linspace(0, 30, 400))
    ref = bank2.filter_series(data)
    seen = set()
    for _ in range(240):          # each layout's chain and Q15 trials settle before it samples
        out = TimeDomainFilterBank.filter_series_many([(bank, data, {})])[0]
        seen.add(bank._layout_rank)
        assert set(np.unique(out.template_indices)) == set(np.unique(ref.template_indices))
        if bank._layouts is None:
            break
    assert bank._layouts is None                             # locked after the trial
    assert len(seen) >= 2                                    # more than one candidate ran


def test_a_bank_adopts_a_persisted_lock(monkeypatch, tmp_path):
    """A lock on file is applied at the bank's first reference: no trial, the same layout."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    bank, _ = _inspiral_bank()
    if not getattr(bank, "_layouts", None):
        pytest.skip("the model offered one block size only")
    key = td._trial_key(bank)
    from matchedfilter import gatechain
    cands = list(bank._candidate_sig)
    gatechain._store_cost(str(tmp_path / "costs.json"), "block-trial|" + key, {"winner": 1})
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())       # a new process
    again, rng = _inspiral_bank()
    assert td._trial_key(again) == key
    assert td._stored_cands(again) == cands                          # kept for the mapping
    assert again._layouts is None                                    # only the winner built
    assert {n for _, n in again.chosen_layout} == {int(cands[1])}     # the whole bank at it
    L = 1 << 15
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    TimeDomainFilterBank.filter_series_many([(again, data, {})])      # runs, with templates loaded


def test_no_trial_without_a_cost_file(monkeypatch):
    """Without MF_COST_FILE the lock cannot be kept: no candidates are built, the model's layout
    runs, exactly as before trials existed."""
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    bank, _ = _inspiral_bank()
    assert getattr(bank, "_layouts", None) is None
    assert getattr(bank, "_layout_rank", 0) == 0


def test_a_trial_continues_across_short_processes(monkeypatch, tmp_path):
    """Processes each too short to finish the trial (one sample apiece) carry its samples in
    MF_COST_FILE, so the trial completes and locks across them, as in one long process."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    key, cost = "dev|model,2048,4096", {0: 1.0, 1: 0.7, 2: 1.2}
    for proc in range(16):
        tr = td._BlockTrials()                                     # a new process
        if tr.winner(key) is not None:
            break
        assert tr.unlocked() == ([] if proc == 0 else [key])     # resumed from the file
        r = tr.rank_for(key, 3)
        tr.record(key, r, cost[r])                                 # one sample, then exit
    assert proc == 6                    # 3 ranks x 2 samples, one per process, then locked
    assert td._BlockTrials().winner(key) == 1
    assert td._BlockTrials().unlocked() == []


def test_two_short_ladder_processes_lock_the_trial(monkeypatch, tmp_path):
    """Two processes on one cost file, the first too short to finish the trial, finish it
    between them: the second continues from the file (its chain and Q15 locks included) and
    locks."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    rng = np.random.default_rng(3)
    L = 1 << 15
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    for proc, batches in ((0, 5), (1, 400)):        # 5 < ranks x (settle + samples)
        monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())   # a new process
        bank, _ = _inspiral_bank()
        if proc == 0 and len(getattr(bank, "_layouts", None) or []) < 2:
            pytest.skip("the model offered one block size only")
        for _ in range(batches):
            TimeDomainFilterBank.filter_series_many([(bank, data, {})])
            if bank._layouts is None:
                break
        if proc == 0:
            assert td._BLOCK_TRIALS.winner(td._trial_key(bank)) is None
    assert td._BLOCK_TRIALS.unlocked() == []
    assert td._BLOCK_TRIALS.winner(td._trial_key(bank)) is not None
    assert getattr(bank, "_layouts", None) is None


class _FakeTimer:
    """Deterministic batch times: rank r's true cost, plus a fixed noise sequence."""

    def __init__(self, true, noise):
        self.true, self.noise, self.k = true, noise, {}

    def __call__(self, r):
        k = self.k.get(r, 0)
        self.k[r] = k + 1
        return self.true[r] * (1.0 + self.noise[r][k % len(self.noise[r])])


def _drive(tr, key, timer, nranks=3, limit=64):
    for _ in range(limit):
        if tr.winner(key) is not None:
            break
        r = tr.rank_for(key, nranks)
        tr.record(key, r, timer(r))
    return tr.winner(key)


def test_two_noisy_samples_do_not_lock_a_slower_rank(monkeypatch, tmp_path):
    """The M2 failure: rank 1 is 10% SLOWER in truth, but its first two samples are 5.7%
    faster than rank 0's (just past TIE). The noise rule sees the gap is inside the samples'
    own spread, samples further, and keeps rank 0. The old rule (median past TIE on two
    samples) locked rank 1."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    timer = _FakeTimer({0: 1.0, 1: 1.10, 2: 1.5},
                       {0: [0.0, 0.10, 0.02, 0.03, -0.01, 0.0],
                        1: [-0.155, -0.045, 0.01, 0.0, 0.02, -0.01],
                        2: [0.0, 0.01]})
    first = [timer.true[r] * (1 + timer.noise[r][k]) for r in (0, 1) for k in (0, 1)]
    med0, med1 = np.median(first[:2]), np.median(first[2:])
    assert med1 < med0 * (1 - 0.05)                       # the old rule would lock rank 1
    assert _drive(td._BlockTrials(), "k", timer) == 0


def test_a_clear_win_still_locks_on_two_samples(monkeypatch, tmp_path):
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    timer = _FakeTimer({0: 1.0, 1: 0.7, 2: 1.3}, {r: [0.0, 0.01] for r in range(3)})
    tr = td._BlockTrials()
    assert _drive(tr, "k", timer) == 1
    assert sum(timer.k.values()) == 6                     # 2 samples each, no extension


def test_a_lock_steady_state_contradicts_is_reopened(monkeypatch, tmp_path):
    """Rank 1 measured faster in its trial, then runs 30% slower than the trial's best in
    steady state: the lock is reopened in the cost file, so the next process trials again."""
    monkeypatch.setenv("MF_TRIAL_RECHECK", "1")              # opt-in (off by default)
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    timer = _FakeTimer({0: 1.0, 1: 0.7, 2: 1.3}, {r: [0.0, 0.01] for r in range(3)})
    tr = td._BlockTrials()
    assert _drive(tr, "k", timer) == 1
    for _ in range(gatechain.RECHECK_N - 1):
        assert not tr.observe("k", 0.72)                  # agrees with the trial
    assert not tr.observe("k", 0.72)
    fresh = td._BlockTrials()                              # agreement keeps the lock
    assert fresh.winner("k") == 1
    for _ in range(gatechain.RECHECK_N):
        reopened = fresh.observe("k", 1.5)                 # 50% slower than the runner-up
    assert reopened
    again = td._BlockTrials()
    assert again.winner("k") is None                      # next process trials again
    assert _drive(again, "k", timer) == 1                  # (the fake timer still says 1)
    final = td._BlockTrials()
    for _ in range(2 * gatechain.RECHECK_N):
        assert not final.observe("k", 1.5)                # one re-check per key: no flapping
    assert td._BlockTrials().winner("k") == 1


def test_a_lock_is_final_without_the_recheck(monkeypatch, tmp_path):
    """By default (MF_TRIAL_RECHECK unset) steady state never reopens a block-size lock: a
    lock reopened from one process's timing let two processes sharing a cost file end on
    different block sizes."""
    monkeypatch.delenv("MF_TRIAL_RECHECK", raising=False)
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    timer = _FakeTimer({0: 1.0, 1: 0.7, 2: 1.3}, {r: [0.0, 0.01] for r in range(3)})
    tr = td._BlockTrials()
    assert _drive(tr, "k", timer) == 1
    fresh = td._BlockTrials()
    for _ in range(4 * gatechain.RECHECK_N):
        assert not fresh.observe("k", 1.5)                # far slower: still not reopened
    assert td._BlockTrials().winner("k") == 1


class _FakeBank:
    def __init__(self, calibrating):
        self._layouts = [object(), object()]
        self._layout_rank, self._layout_warm = 0, True
        self.filters_f = [0]
        self._choice_ns, self.device = (2048, 4096), "fake"
        plan = type("P", (), {"calibrating": lambda s, c=calibrating: c})()
        self._groups = [type("G", (), {"is_hier": True, "_plan": plan})()]

    def _use_layout(self, r):
        self._layout_rank = r

    def _lock_layout(self, r):
        self._layouts = None


def test_no_block_sample_while_a_plan_calibrates(monkeypatch, tmp_path):
    """A batch in which any of the bank's plans is still in a chain or Q15 trial is not a
    block-size sample: those calls switch kernels between them."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    x = np.zeros(8, np.complex64)
    for cal, expect in ((True, 0), (False, 1)):
        b = _FakeBank(cal)
        tok = td._trial_begin([(b, x, {})])
        td._trial_end(tok)
        n = sum(len(v) for v in td._BLOCK_TRIALS.state[td._trial_key(b)]["samples"].values())
        assert n == expect


def test_a_fresh_file_locks_the_block_size_within_a_bound(monkeypatch, tmp_path):
    """GPU-like plans: each candidate layout's plans would run a long chain trial (25 batches
    of calibrating after first use, like a per-batch GPU chain trial). Calibrations run in
    order -- the block size first, every layout at its model chain (held) -- so the block
    trial locks within ranks x (settle + samples) batches, and the winner's held trials start
    after. Nested per layout, it took ~100 segments on Vulkan and never left rank 0 on Metal."""
    from matchedfilter import HierarchicalFilter
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    real = HierarchicalFilter.calibrating
    runs = {}

    def gpu_like(self):
        if getattr(self, "_trial_hold", False):
            return real(self)
        k = id(self)
        runs[k] = runs.get(k, 0) + 1
        return runs[k] <= 25 or real(self)
    monkeypatch.setattr(HierarchicalFilter, "calibrating", gpu_like)
    bank, rng = _inspiral_bank()
    if len(getattr(bank, "_layouts", None) or []) < 2:
        pytest.skip("the model offered one block size only")
    L = 1 << 15
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    nr = len(bank._layouts)
    # The trial's own schedule, worst case: every rank settles once and takes its first
    # samples; then each unclear round (gatechain.measured_choice) asks one more sample of the
    # model's rank and of the best, alternating, so each costs a settle batch and a sample
    # batch for both -- up to _BLOCK_TRIAL_MAX samples. Timing noise decides how many rounds
    # run (a loaded shared runner reached the third), so the bound must allow all of them.
    need = td._BLOCK_TRIALS._base_need()
    rounds = max(0, td._BLOCK_TRIAL_MAX - need)
    bound = nr * (1 + need) + 2 * 2 * rounds + 2
    for i in range(bound):
        TimeDomainFilterBank.filter_series_many([(bank, data, {})])
        if bank._layouts is None:
            break
    assert bank._layouts is None, "block size not locked in %d batches" % bound
    held = [g.plan for g in bank._groups if g.is_hier and getattr(g.plan, "_trial_hold", False)]
    assert not held                                 # the winner's trials were released
