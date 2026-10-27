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


def layout_label(band, ppg, tile, twt, subgroup=0):
    """A coarse layout's name on every backend: the build's stem, "w" when its twiddles come
    from the fp16 table, and "@<size>" when the pipeline requires a subgroup size (Vulkan):
    tierb_256_c16p2t2w, tierb_512_c16@16. The cost file keys and MF_COARSE_LAYOUT use it."""
    return coarse_stem(band, ppg, tile) + ("w" if twt else "") + ("@%d" % subgroup if subgroup else "")


def forced_layout(band):
    """The layout MF_COARSE_LAYOUT names for this band (comma-separated layout_label names;
    each names its own band), or None. The choice then takes it without timing, on every
    backend, so tests and measurements can run each layout through the production path."""
    from . import _config
    for name in (_config.get("MF_COARSE_LAYOUT") or "").split(","):
        name = name.strip()
        if next((t for t in name.split("_") if t.isdigit()), None) == str(band):
            return name
    return None


def shipped_tiles(band, ppg, shipped):
    """The tiles (> 1) built for this band and pairs per group; shipped(stem) -> bool."""
    return tuple(t for t in TILE_PROBE if shipped(coarse_stem(band, ppg, t)))


def parse_label(label):
    """(band, ppg, tile, twt, subgroup) of a coarse layout's name (layout_label's inverse),
    or None for a name that is not a packed fp16 build (a driver's own gate, such as CUDA's
    coarse_tc_512_w4)."""
    import re
    m = re.fullmatch(r"tierb_(\d+)_c16(?:p(\d+))?(?:t(\d+))?(w?)(?:@(\d+))?", label)
    if m is None:
        return None
    band, ppg, tile, twt, sg = m.groups()
    return int(band), int(ppg or 1), int(tile or 1), int(bool(twt)), int(sg or 0)


#: Interleaved rounds the fastest few of a screen are re-timed in together (screen).
RETIME_ROUNDS = 5
#: How many of a screen's fastest are re-timed together; the two fastest of those are the
#: shortlist the device trial plays on real batches.
RETIME = 3


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


def screen(stages, time_full, time_screen=None, rounds=3, screen_cut=4.0):
    """{candidate: time} over staged candidate sets: every backend's coarse screen, which
    ranks candidates on synthetic dispatches for a shortlist (the device trial then plays the
    two fastest on real batches: shortlist, _settings.slot).

    stages: candidate lists, or callables given the times so far that return the next list
    (the Vulkan tiles are offered at the two fastest untiled layouts only: building a
    pipeline is most of the cost). Within a stage, candidates are screened with time_screen
    (a short dispatch) and only those within screen_cut of the fastest get time_full, both
    in interleaved rounds (interleaved_min): some layouts are pathological on some devices
    (band 256 at subgroup 32 on an Iris Xe), and a full dispatch of one can run long enough
    for a driver to reset the device -- they never reach a real call. The RETIME fastest
    overall are then timed again together in interleaved rounds, so a burst that covered one
    stage cannot order them. None when a timer is (no timestamps)."""
    out = {}
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
    lead = sorted(out, key=out.get)[:RETIME]
    if len(lead) > 1:
        again = interleaved_min(lead, time_full, RETIME_ROUNDS)
        if again is None:
            return None
        out.update(again)
    return out


def shortlist(memo, kind, device, band, cands, label, kernel_id, measure, tiebreak=None,
              forced=None):
    """(first, second or None) of cands: the screen's fastest two (measure(cands) -> {candidate:
    time}, screen), kept in MF_COST_FILE under kind|device|band|labels|k<kernel_id> so every
    process sharing the file reproduces them and a build with other kernels screens afresh
    (gatechain.gpu_kernel_id). The first is the default, the second the alternative the
    device trial plays on real batches (_settings.slot). Ties go by tiebreak(c), then the
    candidates' order. Held in memo (the device's) for the process. forced (a label,
    forced_layout's) is taken as it is, unscreened and unstored; a label that is not a
    candidate here raises ValueError naming the candidates. A device that cannot be timed
    runs the first candidate, unstored."""
    from . import _costfile
    labels = [label(c) for c in cands]
    if forced is not None:
        if forced not in labels:
            raise ValueError("%s: no candidate %r at band %d on this device; candidates: %s"
                             % (kind, forced, band, ", ".join(labels)))
        return cands[labels.index(forced)], None
    if len(cands) == 1:
        return cands[0], None
    key = "%s|%s|%d|%s|k%s" % (kind, device, band, ";".join(labels), kernel_id)
    hit = memo.get(key)
    if hit is not None:
        return hit
    by_label = dict(zip(labels, cands))
    first, second = _costfile.stored_choice(key), _costfile.stored_choice(key, "alt")
    if first in by_label:
        hit = memo[key] = (by_label[first], by_label.get(second))
        return hit
    times = measure(list(cands)) or {}
    times = {c: t for c, t in times.items() if c in cands}     # only the candidates offered
    if not times:
        return cands[0], None
    rank = {c: i for i, c in enumerate(cands)}
    order = sorted(times, key=lambda c: (times[c], tuple(tiebreak(c)) if tiebreak else (), rank.get(c, 0)))
    hit = memo[key] = (order[0], order[1] if len(order) > 1 else None)
    _costfile.store_choice(key, label(hit[0]), **({"alt": label(hit[1])} if hit[1] is not None else {}))
    from ._choice import _log_autotune
    _log_autotune("%s %s band %d -> %s (then %s)  %s", kind, device, band, label(hit[0]),
                  None if hit[1] is None else label(hit[1]),
                  {label(c): "%.3g" % t for c, t in sorted(times.items(), key=lambda kv: kv[1])[:4]})
    return hit
