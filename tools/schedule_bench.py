#!/usr/bin/env python3
"""Time a captured search's middle-to-leaf chunks under the untiled and the tiled schedule.

A CPU search runs each chunk's inner correlations and the leaf searches that read them
untiled: the correlations write the middle rows whole, then the leaves read them. The tiled
schedule (``correlate_and_filter_many(..., tile_bytes=B)``) interleaves the two per time tile
of B bytes of middle output, so the leaves read the rows while they are in cache. It is not
the default: on a Zen 5 machine (2026-11-28) it was 1.05-1.6x slower on a PyCBC job's
full-data chunks at every tile size, and tied on its injection-window chunks (the tiles
re-read every leaf bank's templates; what they save, the leaves' read of the middle output
from memory, was 2-3% of a full-data pass). Another machine's caches may answer otherwise;
this tool is how to find out.

It builds the search of a capture (tools/search_bench.py's format), runs one pass with no-op
hooks while recording every chunk's correlation and leaf jobs (the walk's jobs, as
HierarchicalSearch hands them to the table), and compiles each chunk once per arm: untiled
(``_batches._chunk_steps``) and tiled at each tile budget (``_batches._cascade_steps``, the
middle output written whole, as in a search with hooks). It then runs the arms on the
chunks in alternating order, repeat by repeat, checks that every arm gives the untiled
arm's peaks and middle output bit for bit, and prints per arm the median seconds of a pass
over every chunk, its ratio to untiled, and its one-time compile seconds.

    python tools/schedule_bench.py CAPTURE.pkl
    python tools/schedule_bench.py CAPTURE.pkl --windows inj4 --tiles 0,1M,4M,32M

``--windows`` takes the capture's own windows (``full``), an injection job's (``injN``: one
9-second window per block for the first N leaves, ``injall`` for every leaf, as
tools/golden.py makes them) or the standard injection mix (``injstd``: a window every 50 s).
Tile budgets take K and M suffixes; 0 is untiled. Run on one core with one thread
(OMP_NUM_THREADS=1, taskset), and note the machine's load.

Instruction, cycle and cache counts: run one arm alone (``--only B``) under perf stat at two
repeat counts and take the difference per repeat, so setup cancels:

    for R in 3 13; do OMP_NUM_THREADS=1 taskset -c 13 perf stat -x, \\
        -e instructions:u,cycles:u,ls_any_fills_from_sys.dram_io_all:u -o perf_$R.txt \\
        python tools/schedule_bench.py CAPTURE.pkl --only 4M --repeats $R; done

(``ls_any_fills_from_sys.dram_io_all`` is AMD Zen's count of L1D fills from memory; on Intel
use ``mem_load_retired.l3_miss`` or ``LLC-load-misses``.) Alternate the arms between runs.
"""
import argparse
import pickle
import statistics
import sys
import time
from pathlib import Path

import numpy as np

# the repo's own python/ last, so a PYTHONPATH build (an A/B variant) wins
sys.path.append(str(Path(__file__).resolve().parent.parent / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def windows_of(search, inputs, windows, kind):
    """The windows answer of the run: the capture's own (``full``), an injection job's
    (``injN``, ``injall``) or the standard injection mix (``injstd``)."""
    import golden
    if kind == "full":
        return windows
    if kind == "injall":
        return golden._injection_windows(search, inputs, live_leaves=10 ** 6)
    if kind.startswith("inj") and kind[3:].isdigit():
        return golden._injection_windows(search, inputs, live_leaves=int(kind[3:]))
    if kind == "injstd":
        guard = 2048 + 2 * search.pad(search.roots[0])
        half = int(4.5 * 2048)

        def every_50_s(lf, k, c, extra):
            v0, v1 = inputs[c].valid[k]
            return [(t - half - guard - extra, t + half + guard + extra)
                    for t in range(v0 + 25 * 2048, v1, 50 * 2048)]
        return every_50_s
    raise ValueError("unknown windows %r" % (kind,))


def chunk_jobs(search, inputs, windows):
    """Every chunk's (correlation jobs, leaf jobs) of one pass of search, with no-op hooks
    (the middle output is written whole, as in a search with hooks)."""
    from matchedfilter import _batches
    seen = []
    compile_chunk = _batches._chunk_steps

    def recording(corr_jobs, leaf_jobs):
        seen.append((list(corr_jobs), list(leaf_jobs)))
        return compile_chunk(corr_jobs, leaf_jobs)
    _batches._chunk_steps = recording
    try:
        search.run(inputs, windows=windows, on_peaks=lambda ctx: None)
    finally:
        _batches._chunk_steps = compile_chunk
    return seen


def _size(text):
    text = text.strip().upper()
    scale = {"K": 1 << 10, "M": 1 << 20}.get(text[-1:], 1)
    return int(text[:-1] if scale > 1 else text) * scale


def _compile(chunks, tile_bytes):
    """Per chunk the arm's (steps, series, output slots, tiles, the correlation jobs'
    outputs); the compile seconds."""
    from matchedfilter import _batches
    t0 = time.perf_counter()
    compiled = []
    for corr_jobs, leaf_jobs in chunks:
        middle = [kw["out"] for _, _, kw in corr_jobs]
        if tile_bytes == 0:
            steps, series, outs = _batches._chunk_steps(corr_jobs, leaf_jobs)
            compiled.append((steps, series, outs, None, middle))
            continue
        screened_out, cohorts = _batches._tiling_cohorts(
            corr_jobs, _batches._leaves_by_producer(corr_jobs, leaf_jobs)[0])
        cascade = _batches._cascade_steps(corr_jobs, leaf_jobs, screened_out, cohorts,
                                          tile_bytes, None, 0.0)
        if (cascade is None or cascade.before or cascade.leftover or cascade.empty
                or len(cascade.steps.calls) != len(leaf_jobs)):
            raise SystemExit("a chunk does not run tiled whole at %d bytes" % tile_bytes)
        compiled.append((cascade.steps, cascade.series, cascade.outs, cascade.tiles, middle))
    return compiled, time.perf_counter() - t0


def _run(compiled):
    """One pass of an arm over every chunk: its seconds, and per chunk the peaks and the
    middle outputs (the arrays themselves: read them before the next pass)."""
    from matchedfilter import _batches
    t0 = time.perf_counter()
    got = []
    for steps, series, outs, tiles, middle in compiled:
        res, _ = _batches._run_steps(steps, series, outs, None, tiles)
        got.append((res, middle))
    return time.perf_counter() - t0, got


def _digest(got):
    """Every peak column and middle output of a pass, as bytes."""
    return [np.asarray(c).tobytes() for res, middle in got for r in res for c in r] + [
        hash(m.tobytes()) for _, middle in got for m in middle]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("capture")
    ap.add_argument("--windows", default="full")
    ap.add_argument("--tiles", default="0,1M,4M,32M",
                    help="tile budgets, comma separated (0: untiled; default 0,1M,4M,32M)")
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--only", default=None, help="run this one budget alone (for perf stat)")
    a = ap.parse_args(argv)
    import search_bench
    with open(a.capture, "rb") as f:
        capture = pickle.load(f)
    search, inputs, windows, _, _ = search_bench.build(capture, "cpu")
    windows = windows_of(search, inputs, windows, a.windows)
    for _ in range(2):              # the banks built, their trials decided
        search.run(inputs, windows=windows, on_peaks=lambda ctx: None)
    search._chunk_plans.clear()
    chunks = chunk_jobs(search, inputs, windows)
    if not chunks:
        raise SystemExit("the search ran no chunk as one table")
    budgets = [_size(a.only)] if a.only is not None else [_size(t) for t in a.tiles.split(",")]
    arms = {b: _compile(chunks, b) for b in budgets}
    times = {b: [] for b in budgets}
    reference = None
    for r in range(a.repeats):
        for b in (budgets if r % 2 == 0 else budgets[::-1]):
            dt, got = _run(arms[b][0])
            times[b].append(dt)
            if r < 2:               # every arm checked twice against the first
                digest = _digest(got)
                if reference is None:
                    reference = digest
                elif digest != reference:
                    raise SystemExit("tile budget %d gave other results than the first arm" % b)
    base = statistics.median(times[budgets[0]])
    print("%s, windows %s: %d chunks, %d leaf jobs" % (Path(a.capture).name, a.windows,
                                                     len(chunks), sum(len(c[1]) for c in chunks)))
    for b in budgets:
        med = statistics.median(times[b])
        print("  %-10s %.4f s/pass  %.3fx  compile %.3f s" % (
            "untiled" if b == 0 else "%d B" % b, med, med / base, arms[b][1]))
    print("peaks and middle outputs identical under every arm")


if __name__ == "__main__":
    main()
