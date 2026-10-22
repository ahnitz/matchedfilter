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


def forced_tile(env_var):
    """A tile forced by the environment (for measurement and the tests), or None."""
    from . import _config
    return _config.get(env_var)


#: Interleaved rounds the contenders of a coarse layout choice are re-timed in.
CONFIRM_ROUNDS = 5
#: The smallest paired difference a choice acts on. A contender within this of the fastest,
#: or within CLOSE_MADS median absolute deviations of its per-round ratios, is a close call:
#: the backend's fixed preference decides it, not the noise (stored_measured_choice).
CLOSE_FLOOR = 0.005
CLOSE_MADS = 3.0


class Timings(dict):
    """{candidate: time} with `close`: the contenders a paired confirmation could not tell
    from the fastest (confirm_fastest)."""
    close = frozenset()


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
        return Timings(times)
    order = [ref] + cont
    samples = {c: [] for c in order}
    for r in range(rounds):
        for c in (order if r % 2 == 0 else order[::-1]):
            t = time_one(c)
            if t is None:
                return None
            samples[c].append(t)
    out = Timings(times)
    close = set()
    for c in cont:
        ratios = [a / b for a, b in zip(samples[c], samples[ref])]
        med = statistics.median(ratios)
        mad = statistics.median(abs(r - med) for r in ratios)
        out[c] = times[ref] * med
        if abs(med - 1.0) <= max(CLOSE_FLOOR, CLOSE_MADS * mad):
            close.add(c)
    out.close = frozenset(close)
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
                           tiebreak=None, forced=None):
    """The fastest of cands, measured once and kept in MF_COST_FILE under
    kind|device|band|labels|k<kernel_id>, so every process sharing the file reproduces it
    and a build with other kernels measures afresh (gatechain.gpu_kernel_id). An offline
    _choice.Choice kept in `memo` (the device's): label(c) names a candidate in the file;
    measure(cands) returns {candidate: time} (a Timings, whose close calls go to the
    preference: tiebreak(c), then the candidates' order), or None when the device cannot be
    timed (the first candidate is then used, unstored). A stored choice is first timed
    against the two runners-up stored with it (Choice.decide).

    forced (a label, forced_layout's) is taken as it is, neither measured nor stored; a label
    that is not a candidate here raises ValueError naming the candidates."""
    labels = [label(c) for c in cands]
    if forced is not None:
        if forced not in labels:
            raise ValueError("%s: no candidate %r at band %d on this device; candidates: %s"
                             % (kind, forced, band, ", ".join(labels)))
        return cands[labels.index(forced)]
    if len(cands) == 1:
        return cands[0]
    from . import _choice
    ckey = "%s|%s|%d|%s|k%s" % (kind, device, band, ";".join(labels), kernel_id)
    ch = _choice.choice(kind, (band, tuple(labels)), list(cands), scope=memo, store_key=ckey,
                        label=label, recheck_stored=True, what="%s %s band %d" % (kind, device, band))
    return ch.decide(measure, tiebreak)
