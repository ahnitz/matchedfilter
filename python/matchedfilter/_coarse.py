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
