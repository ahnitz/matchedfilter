"""Backend-neutral geometry of the packed (fp16) coarse kernel, shared by the Vulkan and
Metal hosts (docs/cross-platform-review.md: one launch rule, so hosts and harnesses that
dispatch a coarse build directly cannot disagree)."""


def coarse_launch(nd, nt, ppg, tile, cspan, ragged_groups=False):
    """(binsize-slot value, workgroup count) for a packed coarse build.

    Tiled builds (tile > 1) take ragged tiles: the slot carries the data row count and
    ceil(nd * ceil(nt/tile) / ppg) groups run. Untiled builds with more than one pair per
    group are ragged too where the kernel says so (ragged_groups: Vulkan, tierb.slang
    RAGGED GROUPS): the row count again, and ceil(nd * nt / ppg) groups. Otherwise an
    untiled build takes the coarse span and exact geometry (Metal and CUDA pad the pair
    count to whole groups instead). The host and every harness that dispatches a coarse
    build directly must use this, so the two cannot disagree."""
    if tile > 1:
        return nd, -(-(nd * -(-nt // tile)) // ppg)
    if ragged_groups and ppg > 1:
        return nd, -(-(nd * nt) // ppg)
    return cspan, nd * nt // ppg


#: Templates per pair slot a tiled build may carry. The host never assumes one: it offers
#: every tile shipped for a band and layout and the device's measured choice runs. A fixed
#: per-band table (tuned once, on RDNA) cost 11% of the fine stage on GCN and 4% on the
#: RDNA part it was tuned for, at band 256 alone.
TILE_PROBE = (2, 4, 8, 16)


def coarse_stem(band, ppg, tile):
    """File stem of a packed coarse build, as every build script and host spells it: "p1"
    and "t1" are omitted (tierb_256_c16, tierb_256_c16p4t2)."""
    return "tierb_%d_c16%s%s" % (band, "p%d" % ppg if ppg > 1 else "",
                                 "t%d" % tile if tile > 1 else "")


def shipped_tiles(band, ppg, shipped):
    """The tiles (> 1) built for this band and pairs per group; shipped(stem) -> bool."""
    return tuple(t for t in TILE_PROBE if shipped(coarse_stem(band, ppg, t)))


def forced_tile(env_var):
    """A tile forced by the environment (for measurement and the tests), or None."""
    import os
    v = os.environ.get(env_var, "")
    return int(v) if v.strip() else None


#: Interleaved rounds the contenders of a coarse layout choice are re-timed in.
CONFIRM_ROUNDS = 5


def interleaved_min(cands, time_one, rounds):
    """{candidate: min over `rounds` rounds of time_one(candidate)}: each round times every
    candidate once, the order reversing between rounds; None as soon as time_one does (no
    device timestamps). A burst of other work on a shared GPU then slows one round of every
    candidate rather than every rep of a few: timed back to back, the Iris Xe stored a tiled
    band-256 layout 4.3x slower than the untiled one, and MF_COST_FILE kept it."""
    out = {c: float("inf") for c in cands}
    order = list(cands)
    for r in range(rounds):
        for c in (order if r % 2 == 0 else order[::-1]):
            t = time_one(c)
            if t is None:
                return None
            out[c] = min(out[c], t)
    return out


def confirm_fastest(times, time_one, rivals=(), rounds=CONFIRM_ROUNDS, near=1.5):
    """`times` with the contenders re-timed against the fastest, interleaved: the fastest's
    value stands and each contender's becomes it times the median of the per-round ratios,
    so the choice rests on paired comparisons rather than on minima taken at different
    moments. Contenders: every candidate within `near` of the fastest, and `rivals` (the
    fastest of each separately timed stage, which a burst during one stage could have put
    anywhere). None when time_one is."""
    import statistics
    ref = min(times, key=times.get)
    cont = [c for c in times if c != ref and (times[c] <= near * times[ref] or c in rivals)]
    if not cont:
        return times
    order = [ref] + cont
    samples = {c: [] for c in order}
    for r in range(rounds):
        for c in (order if r % 2 == 0 else order[::-1]):
            t = time_one(c)
            if t is None:
                return None
            samples[c].append(t)
    out = dict(times)
    for c in cont:
        out[c] = times[ref] * statistics.median(a / b for a, b in zip(samples[c], samples[ref]))
    return out
