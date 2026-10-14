"""Backend-neutral geometry of the packed (fp16) coarse kernel, shared by the Vulkan and
Metal hosts (docs/cross-platform-review.md: one launch rule, so hosts and harnesses that
dispatch a coarse build directly cannot disagree)."""


def coarse_launch(nd, nt, ppg, tile, cspan):
    """(binsize-slot value, workgroup count) for a packed coarse build.

    Tiled builds (tile > 1) take ragged tiles: the slot carries the data row count and
    ceil(nd * ceil(nt/tile) / ppg) groups run. Untiled builds take the coarse span and
    exact geometry. The host and every harness that dispatches a coarse build directly
    must use this, so the two cannot disagree."""
    if tile > 1:
        return nd, -(-(nd * -(-nt // tile)) // ppg)
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
