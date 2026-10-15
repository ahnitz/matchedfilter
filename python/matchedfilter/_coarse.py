"""Backend-neutral geometry of the packed (fp16) coarse kernel, shared by the Vulkan and
Metal hosts (docs/cross-platform-review.md: one launch rule, so hosts and harnesses that
dispatch a coarse build directly cannot disagree)."""


def coarse_launch(nd, nt, ppg, tile, cspan):
    """(binsize-slot value, workgroup count) for a packed coarse build, on every backend.

    Tiled builds (tile > 1) take ragged tiles: the slot carries the data row count and
    ceil(nd * ceil(nt/tile) / ppg) groups run. Untiled builds with more than one pair per
    group take ragged groups (tierb.slang RAGGED GROUPS): the row count again, and
    ceil(nd * nt / ppg) groups; a group's spare slots compute and write nothing, so no
    backend pads its rows. One pair per group is exact geometry, with the coarse span in
    the slot. The host and every harness that dispatches a coarse build directly must use
    this, so the two cannot disagree."""
    if tile > 1:
        return nd, -(-(nd * -(-nt // tile)) // ppg)
    if ppg > 1:
        return nd, -(-(nd * nt) // ppg)
    return cspan, nd * nt


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


def time_staged(stages, time_full, time_screen=None, rounds=3, screen_cut=4.0):
    """{candidate: time} over staged candidate sets, every backend's coarse timing rule.

    stages: candidate lists, or callables given the times so far that return the next list
    (the Vulkan tiles are offered at the two fastest untiled layouts only: building a
    pipeline is most of the cost). Within a stage, candidates are screened with time_screen
    (a short dispatch) and only those within screen_cut of the fastest get time_full, both
    in interleaved rounds (interleaved_min); some layouts are pathological on some devices
    (band 256 at subgroup 32 on an Iris Xe) and a full dispatch of one can run long enough
    for a driver to reset the device. The fastest of each stage is then confirmed against
    the overall fastest, paired (confirm_fastest). None when a timer is (no timestamps)."""
    out, rivals = {}, []
    for st in stages:
        cs = list(st(out) if callable(st) else st)
        if not cs:
            continue
        times = interleaved_min(cs, time_screen, rounds) if time_screen else {}
        if times is None:
            return None
        keep = [c for c in cs if not times or times[c] <= screen_cut * min(times.values())]
        full = interleaved_min(keep, time_full, rounds)
        if full is None:
            return None
        times.update(full)
        out.update(times)
        rivals.append(min(times, key=times.get))
    return confirm_fastest(out, time_full, rivals=rivals) if out else out


def stored_measured_choice(memo, kind, device, band, cands, label, kernel_id, measure,
                           tiebreak=None):
    """The fastest of cands, measured once per process and kept in MF_COST_FILE under
    kind|device|band|labels|k<kernel_id>, so every process sharing the file reproduces it
    and a build with other kernels measures afresh (gatechain.gpu_kernel_id).

    label(c) names a candidate in the file; measure(cands) returns {candidate: time}, or None
    when the device cannot be timed (the first candidate is then used, unstored). Ties break
    on tiebreak(c), then on the candidates' order."""
    labels = [label(c) for c in cands]
    k = (kind, band, tuple(labels))
    if k in memo:
        return memo[k]
    if len(cands) == 1:
        memo[k] = cands[0]
        return memo[k]
    from . import gatechain
    ckey = "%s|%s|%d|%s|k%s" % (kind, device, band, ";".join(labels), kernel_id)
    held = gatechain.stored_choice(ckey)
    if held in labels:
        memo[k] = cands[labels.index(held)]
        return memo[k]
    times = measure(cands)
    if not times:
        memo[k] = cands[0]
        return memo[k]
    rank = {c: i for i, c in enumerate(cands)}
    memo[k] = min(times, key=lambda c: (times[c],) + (tuple(tiebreak(c)) if tiebreak else ())
                  + (rank.get(c, 0),))
    gatechain.store_choice(ckey, label(memo[k]))
    return memo[k]
