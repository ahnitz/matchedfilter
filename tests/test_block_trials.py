"""Block-size trials (time_domain._BlockTrials): the model's candidate layouts measured end to end."""
import numpy as np
import pytest

from matchedfilter import TimeDomainFilterBank
from matchedfilter import time_domain as td


def _run(timings, need=1):
    """Feed per-rank seconds (work 1) through a fresh trial in its own schedule; return the lock."""
    tr = td._BlockTrials()
    feeds = {r: list(v) for r, v in timings.items()}
    for _ in range(64):
        if tr.winner("k") is not None:
            break
        r = tr.rank_for("k", len(timings))
        tr.record("k", r, feeds[r].pop(0), 1.0)
    return tr.winner("k")


@pytest.mark.parametrize("slower", [1.5, 2.0, 10.0])
def test_a_clearly_worse_block_size_is_never_locked(slower):
    # either rank may be the bad one: the measured faster wins whatever the model's order
    assert _run({0: [1.0] * 4, 1: [slower] * 4}) == 0
    assert _run({0: [slower] * 4, 1: [1.0] * 4}) == 1


def test_a_tie_keeps_the_models_choice():
    assert _run({0: [1.00] * 4, 1: [0.97] * 4}) == 0          # inside gatechain.TIE
    assert _run({0: [1.00] * 4, 1: [0.80] * 4}) == 1          # outside it


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


def test_switching_layouts_is_exact_and_locks(monkeypatch):
    """Every candidate layout gives the same triggers' identity rules as running it alone, and
    a lock leaves one layout."""
    monkeypatch.setattr(td, "_BLOCK_TRIALS", td._BlockTrials())
    monkeypatch.setattr(td, "_BLOCK_TRIAL_MARGIN", 10.0)     # force an alternative to exist
    bank, rng = _inspiral_bank()
    bank2, _ = _inspiral_bank()
    layouts = getattr(bank, "_layouts", None) or []
    if len(layouts) < 2:
        pytest.skip("the model offered one block size only")
    L = 1 << 16
    data = ((rng.standard_normal(L) + 1j * rng.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    data[30000:30400] += 40 * np.exp(1j * np.linspace(0, 30, 400))
    ref = bank2.filter_series(data)                          # rank 0, never trialled
    seen = set()
    for _ in range(8):
        out = TimeDomainFilterBank.filter_series_many([(bank, data, {})])[0]
        seen.add(bank._layout_rank if bank._layouts else -1)
        # a block size changes which lags a bin can report, not which templates trigger
        assert set(np.unique(out.template_indices)) == set(np.unique(ref.template_indices))
        if bank._layouts is None:
            break
    assert bank._layouts is None                             # locked after the trial
    assert len(seen) >= 2                                    # both candidates actually ran
