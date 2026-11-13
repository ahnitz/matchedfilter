"""The continuous correlation's fixed cost per block has a floor.

The block-size costs are (fixed, per template, per template per output sample), read from
three timings. The fixed cost is a difference of them, and came out zero whenever sixteen
templates cost more each than two (a loaded host; spectra leaving the second-level cache).
A zero fixed cost makes one group per filter look free."""
import numpy as np

from matchedfilter import _choice, _layout


def test_fixed_cost_is_at_least_half_a_template(monkeypatch):
    """Timings in which sixteen templates take ten times what two do, per block: the per-
    template cost then exceeds half the two-template block, and the difference is negative."""
    n, taps = 1024, 256
    seen = {}

    def rounds(cands, time_one, n_rounds, **kw):
        for c in cands:
            time_one(c)                              # the runs still work
        seen["cands"] = list(cands)
        return {0: 1.0, 1: 10.0, 2: 9.0}

    monkeypatch.setattr(_choice, "fastest_of_rounds", rounds)
    rng = np.random.default_rng(0)
    nblocks = 8
    length = nblocks * (n - taps) + n
    ser = (rng.standard_normal(length) + 1j * rng.standard_normal(length)).astype(np.complex64)
    a, b, w = _layout._corr_measure(n, "cpu", "cpu", rng, taps, nblocks, length, ser)
    assert seen["cands"] == [0, 1, 2]
    per_template = b + w * (n - taps)
    assert per_template > 0
    assert a >= 0.5 * per_template * (1 - 1e-12)


def test_layout_does_not_give_each_filter_its_own_group(monkeypatch):
    """With costs as a loaded Haswell node measured them (small sizes' fixed cost zero before
    the floor), five filters of 565 to 3189 taps land in at most two groups, not five."""
    measured = {2048: (0.0, 9.6, 0.0062), 4096: (0.0, 18.8, 0.0085), 8192: (1.0, 111.9, 0.0085),
                16384: (65.0, 220.6, 0.0073), 32768: (1246.0, 388.6, 0.0056),
                65536: (3142.0, 734.1, 0.0160)}          # microseconds

    def costs(n, device=None):
        a, b, w = (1e-6 * v for v in measured[int(n)])
        return max(a, 0.5 * (b + w * (n - n // 4))), b, w   # the floor _corr_measure applies

    monkeypatch.setattr(_layout, "_corr_block_costs", costs)
    counts = np.array([565, 991, 1485, 2285, 3189])
    groups, _ = _layout._corr_layout(counts, (2048, 4096, 8192, 16384, 32768, 65536), None, "cpu")
    assert len(groups) <= 2
    monkeypatch.setattr(_layout, "_corr_block_costs",
                        lambda n, device=None: tuple(1e-6 * v for v in measured[int(n)]))
    split, _ = _layout._corr_layout(counts, (2048, 4096, 8192, 16384, 32768, 65536), None, "cpu")
    assert len(split) == 5                               # what the zero fixed costs gave
