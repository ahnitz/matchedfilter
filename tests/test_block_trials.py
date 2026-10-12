"""Block-size trials (time_domain._BlockTrials): the model's candidate layouts measured end to end."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import time_domain as td


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
    for _ in range(16):
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
    """Two processes on one cost file, each running fewer batches than the trial needs,
    finish it between them: the second one locks."""
    monkeypatch.setenv("MF_COST_FILE", str(tmp_path / "costs.json"))
    rng = np.random.default_rng(3)
    L = 1 << 15
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    for proc in range(2):
        monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())   # a new process
        bank, _ = _inspiral_bank()
        if proc == 0 and len(getattr(bank, "_layouts", None) or []) < 2:
            pytest.skip("the model offered one block size only")
        for _ in range(6):                     # < 3 ranks x (settle + 2 samples) = 9
            TimeDomainFilterBank.filter_series_many([(bank, data, {})])
        if proc == 0:
            assert td._BLOCK_TRIALS.unlocked() == [td._trial_key(bank)]
    assert td._BLOCK_TRIALS.unlocked() == []
    assert td._BLOCK_TRIALS.winner(td._trial_key(bank)) is not None
    assert getattr(bank, "_layouts", None) is None
