"""The coarse-layout screen's tiled stage (_coarse.tile_offer): which tiled layouts it times
after the untiled ones. Recorded timings only, no device."""
from matchedfilter import _coarse
from matchedfilter._choice import TIE

# Band 256 on the 8060S (pycbc job, 2026-11-25): (subgroup, pairs per group, tile, twiddle
# table), each untiled layout's time relative to the fastest untiled, and the tiled ones'.
# The untiled layouts lie within a few percent of each other; their tiled siblings differ by
# more than the whole untiled spread.
UNTILED = {(64, 4, 1, 1): 1.000, (64, 8, 1, 1): 1.024, (64, 4, 1, 0): 1.053, (64, 8, 1, 0): 1.072,
           (32, 2, 1, 1): 1.115, (64, 2, 1, 0): 1.120, (64, 16, 1, 1): 1.140, (32, 1, 1, 0): 1.300}
TILED = {(64, 8, 2, 1): 0.729, (64, 4, 2, 1): 0.737, (64, 16, 2, 1): 0.741, (64, 4, 4, 1): 0.773,
         (64, 8, 4, 1): 0.777, (32, 2, 2, 1): 0.790, (64, 2, 2, 1): 0.805, (32, 1, 4, 1): 0.95}
CANDS = list(UNTILED) + list(TILED)


def _shuffled():
    """The untiled ranking reshuffled within the screen's scatter (a few percent): the two
    layouts timed fastest are not the two whose tiles are fastest."""
    t = dict(UNTILED)
    t[(64, 2, 1, 0)] = 0.995
    t[(32, 2, 1, 1)] = 1.010
    t[(64, 4, 1, 1)] = 1.025
    t[(64, 8, 1, 1)] = 1.030
    return t


def test_the_tiles_of_every_untiled_layout_within_the_scatter_are_timed():
    shuffled = _shuffled()
    # today's rule (scatter 0): the two fastest untiled (subgroup, pairs per group) only --
    # the fastest tiled layout's sibling, 3.5% behind, loses its tiles
    old = _coarse.tile_offer(CANDS, shuffled, 0.0)
    assert (64, 8, 2, 1) not in old and (64, 4, 2, 1) not in old
    new = _coarse.tile_offer(CANDS, shuffled, TIE)
    assert {(64, 8, 2, 1), (64, 4, 2, 1), (64, 2, 2, 1), (32, 2, 2, 1)} <= set(new)
    assert (64, 16, 2, 1) not in new and (32, 1, 4, 1) not in new     # 14% and 30% behind
    # in the ranking as usually timed, the rule offers what today's does and more
    assert set(_coarse.tile_offer(CANDS, UNTILED, 0.0)) <= set(_coarse.tile_offer(CANDS, UNTILED, TIE))


def test_the_screen_keeps_the_fastest_tiled_layout_when_the_untiled_ranking_shuffles():
    """Through the screen as the device runs it (untiled stage, then tile_offer's), with the
    recorded times: the fastest layout it returns is the fastest tiled one."""
    shuffled = _shuffled()
    times = {**shuffled, **TILED}
    out = _coarse.screen([[c for c in CANDS if c[2] == 1],
                          lambda t: _coarse.tile_offer(CANDS, t, TIE)],
                         lambda c: times[c], time_screen=lambda c: times[c], rounds=3)
    assert min(out, key=out.get) == (64, 8, 2, 1)
    old = _coarse.screen([[c for c in CANDS if c[2] == 1],
                          lambda t: _coarse.tile_offer(CANDS, t, 0.0)],
                         lambda c: times[c], time_screen=lambda c: times[c], rounds=3)
    assert min(old, key=old.get) != (64, 8, 2, 1)


def test_a_layout_whose_timer_recorded_nothing_leads_no_tiles():
    """A time of 0 (a timer that recorded nothing) is no time: it does not make its layout's
    tiles the ones timed."""
    t = dict(UNTILED)
    t[(32, 1, 1, 0)] = 0.0
    offered = _coarse.tile_offer(CANDS, t, TIE)
    assert (32, 1, 4, 1) not in offered and (64, 8, 2, 1) in offered
