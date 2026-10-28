"""Test-session setup.

GPU capability probes and performance-test options live here, along with
an import-order workaround for optional development tooling.

slangpy must be imported before numpy. Importing numpy first makes Vulkan
device creation fail with "No adapters found" -- a symbol clash between
numpy's bundled libraries and the LLVM that Mesa uses to compile shaders.
pytest imports every test module during collection, most of which import
numpy, so by the time tests/test_gpu.py asks for a device it is far too
late: the GPU tests skip on a machine that has a perfectly good GPU, and
report "no Vulkan device", which looks like a missing driver rather than a
self-inflicted wound.

Doing it here means it happens before any test module is imported.

This is spike-only. The shipped backend will dlopen Vulkan itself with no
C++ runtime of its own, and a direct ctypes probe behaves identically with
and without numpy loaded -- so the clash is slangpy's bundled runtime
against numpy's, not Vulkan against numpy.
"""
try:
    import slangpy            # noqa: F401  -- before numpy, deliberately
except Exception:
    pass                      # absent is fine; the GPU tests will say so


# --- a size this device cannot run is not a failure ------------------------
import pytest                                          # noqa: E402


# --- which CPU kernels this session runs -------------------------------------
def _cpu_target():
    """(requested MF_ISA or None, the backend running, the build's targets)."""
    import os
    import matchedfilter as mf
    return os.environ.get("MF_ISA") or None, mf.backend(), tuple(mf.targets())


def pytest_report_header(config):
    import numpy as np
    import matchedfilter as mf
    want, have, targets = _cpu_target()
    return ["matchedfilter CPU: backend %s, targets %s, MF_ISA %s; numpy %s" % (
                have, ",".join(targets), want or "unset", np.__version__),
            "matchedfilter devices: %s" % ", ".join(str(d) for d in mf.devices()),
            "MF_* environment: removed %s; kept %s" % (
                ",".join(_SCRUBBED["removed"]) or "none", ",".join(_SCRUBBED["kept"]) or "none")]


def pytest_sessionstart(session):
    """A forced target (MF_ISA) that is not the backend at session start fails the
    session: the run would test a different kernel than the job claims. On Actions
    the session also names its target in a notice, readable without a signed-in
    log download."""
    import os
    want, have, targets = _cpu_target()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::notice title=CPU target::backend %s (MF_ISA %s; targets %s)"
              % (have, want or "unset", ",".join(targets)))
    if want is not None and want != have:
        raise pytest.UsageError("MF_ISA=%s requested, but the backend is %s" % (want, have))


# --- time limits in a slow environment ---------------------------------------
def scaled(seconds):
    """A subprocess time limit, scaled by TEST_TIMEOUT_SCALE (default 1): tools/sanitize.sh
    sets 10, since ASan slows Python-heavy work about that much. The same test runs; only
    its patience changes."""
    import os
    return seconds * float(os.environ.get("TEST_TIMEOUT_SCALE") or 1)


# --- kernel files an install for another platform carries -------------------
def kernel_dir(name):
    """The directory of ahead-of-time kernels `name` (spirv, ptx, metal): the install's,
    or for one this platform's install leaves out (matchedfilter._kernel_dirs) the
    checkout's, so the static checks of every backend's committed kernels still run off
    their platform. Skips when neither has it."""
    from pathlib import Path
    import matchedfilter as mf
    own = Path(mf.__file__).resolve().parent / name
    if own.is_dir():
        return own
    repo = Path(__file__).resolve().parents[1] / "python" / "matchedfilter" / name
    if repo.is_dir():
        return repo
    pytest.skip("no %s/ kernels in this install or a checkout beside it" % name)


@pytest.fixture(autouse=True, scope="session")
def _metal_sources_off_macos():
    """Metal's static checks read _mtlcompute._METAL_DIR; off macOS an install carries no
    Metal, so they read the checkout's (kernel_dir)."""
    from matchedfilter import _mtlcompute
    if not _mtlcompute._METAL_DIR.is_dir():
        from pathlib import Path
        repo = Path(__file__).resolve().parents[1] / "python" / "matchedfilter" / "metal"
        if repo.is_dir():
            _mtlcompute._METAL_DIR = repo
    yield


# --- a slice of a production FIR bank, for tests that need real taps --------
def bank_subset():
    """Real FIR taps without the 110 MB bank or h5py: tests/data/bank_subset_opt501_v2.npz,
    written by tools/make_bank_subset.py from fir_three_level_opt501_v2.hdf (fine group 0's
    first 128 templates; top template 0's middle filters, ids and sigmas)."""
    import numpy as np
    from pathlib import Path
    with np.load(Path(__file__).parent / "data" / "bank_subset_opt501_v2.npz") as z:
        return {k: z[k] for k in z.files}


@pytest.fixture(autouse=True)
def _restore_sys_path():
    """A test that changes sys.path (a tool's main() run in-process) changes it for itself
    only. Until 2026-10-22 tools/migrate_cost_file.py's main() left the source tree on it,
    and every spawned process a later test started imported that unbuilt tree and died:
    in the reverse-order run only, and only where the tree has no built extension (CI)."""
    import sys
    saved = list(sys.path)
    yield
    sys.path[:] = saved


@pytest.fixture(autouse=True)
def _clean_autotune_cache():
    """Every test starts without the workload choices an earlier test made."""
    import matchedfilter as mf
    mf.clear_autotune_cache()
    yield
    mf.clear_autotune_cache()


# --- the session leaves the developer's environment alone -------------------
#: MF_* variables the suite keeps from the environment: the forced CPU target MF_ISA (CI's
#: per-target jobs) and the registry's "tools" section, the tool locations and inputs that
#: some tests read (the MF_TEASER_ names by prefix; tests/test_config_registry.py checks the
#: set). Every other MF_* variable would change what the library does under test (a
#: developer's MF_COST_FILE, a forced chain), so it is removed before collection;
#: --keep-mf-env NAME keeps one deliberately.
_KEPT_MF = {"MF_ISA", "MF_SLANGC", "MF_SLANGC_ANY_VERSION", "MF_NVRTC", "MF_CUDA_PATH",
            "MF_GATE_BANK", "MF_GATE_PROFILES"}
_SCRUBBED = {"removed": [], "kept": []}


def pytest_configure(config):
    import os
    keep = _KEPT_MF | set(config.getoption("--keep-mf-env") or ())
    for name in sorted(n for n in os.environ if n.startswith("MF_")):
        if name in keep or name.startswith("MF_TEASER_"):
            _SCRUBBED["kept"].append(name)
        else:
            _SCRUBBED["removed"].append(name)
            del os.environ[name]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Turn UnsupportedSize into a skip, and nothing else.

    n=16384 needs a 1024-thread threadgroup. The Apple Paravirtual device
    allows this kernel 576, so that length is out of reach there -- a fact
    about the hardware, not a fault, and one no amount of fixing will
    change. Every other size runs and agrees with the CPU.

    The narrow exception type is the point. Catching the backend's general
    error here would also swallow a kernel that failed to compile, which is
    exactly the failure these tests exist to catch.
    """
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is None:
        return
    from matchedfilter import UnsupportedSize
    if call.excinfo.errisinstance(UnsupportedSize):
        if (item.config.getoption('--require-coarse-gpu') and
                item.path.name == 'test_coarse_fdr.py'):
            return  # this CI job promises the complete coarse test matrix
        report.outcome = "skipped"
        report.longrepr = (__file__, 0, "unsupported on this device: %s"
                           % call.excinfo.value)
        # Do NOT set report.wasxfail, even to None: pytest tests for the
        # attribute's presence, so assigning it reports an xfail instead of
        # a skip -- which reads as "expected to be broken" rather than
        # "this device cannot do it".


# --- a GPU that enumerates is not a GPU that works -------------------------
_USABLE = "unset"


def usable_gpu():
    """A GPU device string this machine can actually RUN, or None.

    Enumeration is not availability. A Mesa driver that cannot allocate its
    shared memory -- "Failed to create anonymous file for memory
    allocations" -- still enumerates the adapter, so mf.devices() lists a
    GPU and then every attempt to open it raises "no gpu with index 0". On
    such a machine, gating the GPU tests on enumeration alone produced
    dozens of failures that read like defects in this library and were
    nothing of the sort.

    So the probe filters. Opening a context is not enough either, because
    the allocation that fails is the one the first dispatch needs; the
    cheapest honest question is whether a 1024-point filter returns an
    answer. Asked once per session and cached.
    """
    global _USABLE
    if _USABLE != "unset":
        return _USABLE
    _USABLE = None
    _PROBE_FAILURES.clear()
    try:
        import numpy as np
        import matchedfilter as mf
    except Exception:
        return _USABLE
    for d in mf.devices():
        if d.kind != "gpu" or d.is_software:
            continue
        try:
            f = mf.MatchedFilter(1024, 1, 1, device=str(d))
            z = np.zeros((1, 1024), dtype=np.complex64)
            z[0, 0] = 1.0
            f.set_data(z)
            f.set_templates(z)
            f.run(binsize=1024, threshold=0.0)
        except Exception as e:
            _PROBE_FAILURES.append("%s failed its probe: %s: %s"
                                   % (d, type(e).__name__, str(e).splitlines()[0][:120] if str(e) else ""))
            continue
        _USABLE = str(d)
        break
    return _USABLE


#: Why each enumerated GPU was rejected by usable_gpu's probe, in order.
_PROBE_FAILURES = []


def gpu_backend():
    """The backend ("vulkan", "metal", "cuda") of this machine's usable GPU; skips without one."""
    import pytest
    import matchedfilter as mf
    dev = usable_gpu()
    if dev is None:
        pytest.skip(usable_gpu_reason())
    return next(d for d in mf.devices() if str(d) == dev).backend


def forced_coarse_layouts(ctx, bands, keep):
    """An MF_COARSE_LAYOUT value naming, at each band, the first of the device's own coarse
    layouts (ctx.coarse_layouts) whose fields (_coarse.parse_label: band, ppg, tile, twt,
    subgroup) keep accepts; a band with none is left to its measured choice. A layout is
    forced by name on every backend, so a test never asks for one the device lacks."""
    from matchedfilter._coarse import parse_label
    names = []
    for band in bands:
        hit = [s for s in ctx.coarse_layouts(band)
               if parse_label(s) is not None and keep(parse_label(s))]
        if hit:
            names.append(hit[0])
    return ",".join(names)


def gpu_context(backend):
    """A fresh low-level context (device 0) of the backend; skips an unknown one."""
    import pytest
    if backend == "vulkan":
        from matchedfilter import _vkcompute as M
    elif backend == "metal":
        from matchedfilter import _mtlcompute as M
    elif backend == "cuda":
        from matchedfilter import _cudacompute as M
    else:
        pytest.skip("backend %s" % backend)
    return M.Context(0)


def usable_gpu_reason():
    """Why there is no usable GPU, phrased so it does not mislead: a GPU that enumerated and
    failed the probe is named with its error, apart from there being no GPU at all."""
    usable_gpu()
    if _PROBE_FAILURES:
        return "no usable GPU: " + "; ".join(_PROBE_FAILURES)
    try:
        from matchedfilter import _vulkan
        ok, why = _vulkan.available()
    except Exception as e:                      # pragma: no cover
        return "could not ask for a GPU: %s" % e
    if ok:
        return ("a GPU enumerates but cannot run a filter on this machine "
                "(driver or environment, not the transform length)")
    return why or "no usable GPU"


_VK = "unset"


def vulkan_runs():
    """``(ok, reason)`` -- can a Vulkan CONTEXT actually be opened here?

    _vulkan.available() answers a different question: whether a non-software
    adapter enumerates. That is necessary and not sufficient. A driver that
    cannot allocate its shared memory enumerates fine and raises on context
    creation, so gates built on availability alone let the test body run and
    then report a driver fault as a failure of this library.

    Cached: opening a context is not free, and several modules ask.
    """
    global _VK
    if _VK != "unset":
        return _VK
    try:
        from matchedfilter import _vulkan
        ok, why = _vulkan.available()
    except Exception as e:                      # pragma: no cover
        _VK = (False, "could not ask for Vulkan: %s" % e)
        return _VK
    if not ok:
        _VK = (False, why or "no Vulkan device")
        return _VK
    try:
        from matchedfilter import _vkcompute
        c = _vkcompute.Context(0)
        c.destroy()
    except Exception as e:
        _VK = (False, "a Vulkan device enumerates but will not open here: %s"
                      % str(e).strip().splitlines()[0][:120])
        return _VK
    _VK = (True, None)
    return _VK


def pytest_addoption(parser):
    parser.addoption('--require-coarse-gpu', action='store_true', default=False,
                     help='Fail rather than skip missing coarse-calibration GPU coverage')

    parser.addoption('--keep-mf-env', action='append', metavar='NAME',
                     help='keep this MF_* variable from the environment (repeatable); the '
                          'session removes every other one but MF_ISA and the tool paths')
    parser.addoption('--reverse-modules', action='store_true', default=False,
                     help='run the test modules in reverse order (finds order dependence)')
    parser.addoption('--shard', metavar='K/N',
                     help='run the K-th of N parts of the suite (whole modules, dealt in turn '
                          'by name), so a slow run (the sanitizers) splits across jobs')
    parser.addoption('--run-performance', action='store_true', default=False,
                     help='Run opt-in performance regression checks on an idle machine')
    parser.addoption('--performance-baseline', help='Compare timings with a saved same-host JSON baseline')
    parser.addoption('--performance-record', help='Save timings after a successful performance run')


def shard_modules(modules, k, n):
    """The modules of the k-th (1-based) of n shards: sorted by name and dealt in turn, so
    each module is in exactly one shard and the shards differ by at most one module."""
    if not (n >= 1 and 1 <= k <= n):
        raise pytest.UsageError('--shard K/N needs 1 <= K <= N')
    return set(sorted(set(modules))[k - 1::n])


def pytest_collection_modifyitems(config, items):
    shard = config.getoption('--shard')
    if shard:
        try:
            k, n = (int(x) for x in shard.split('/'))
        except ValueError:
            raise pytest.UsageError('--shard takes K/N, e.g. 2/4: %r' % shard)
        keep = shard_modules((item.module.__name__ for item in items), k, n)
        dropped = [item for item in items if item.module.__name__ not in keep]
        items[:] = [item for item in items if item.module.__name__ in keep]
        config.hook.pytest_deselected(items=dropped)
    if config.getoption('--reverse-modules'):
        order = list(dict.fromkeys(item.module.__name__ for item in items))[::-1]
        rank = {m: i for i, m in enumerate(order)}
        items.sort(key=lambda item: rank[item.module.__name__])     # stable within a module
    baseline = config.getoption('--performance-baseline')
    output = config.getoption('--performance-record')
    if baseline and output:
        from pathlib import Path
        if Path(baseline).resolve() == Path(output).resolve():
            raise pytest.UsageError('Compare and record paths must differ; preserve the trusted baseline')
    if not config.getoption('--run-performance'):
        if config.getoption('--performance-baseline') or config.getoption('--performance-record'):
            raise pytest.UsageError('Performance baseline/record options require --run-performance')
        skip = pytest.mark.skip(reason='opt-in timing test; use --run-performance on an idle machine')
        for item in items:
            if 'performance' in item.keywords:
                item.add_marker(skip)


def interleaved_speedup(slow, fast, reps=15):
    """Speedup of fast() over slow(), robust to a shared host's load.

    Timing all of one then all of the other lets load that comes and goes between the
    two blocks move the ratio (both replica speedup tests failed that way at load 20-60
    and passed alone). Here the two alternate, and the speedup is the MEDIAN OF PAIRED
    RATIOS: each slow run is divided by the fast run timed right beside it, so both
    members of a pair see the same load, and the median ignores pairs a load spike hit.
    (A ratio of per-side minima still drifted 1.56-2.24x at load ~25: the two minima
    could come from different moments.) Returns (speedup, t_slow, t_fast) with the
    per-side medians for reporting."""
    import time
    import statistics
    slow(), fast()                                   # warm both
    ratios, ts, tf = [], [], []
    for i in range(reps):
        order = ((slow, 0), (fast, 1)) if i % 2 == 0 else ((fast, 1), (slow, 0))
        pair = {}
        for fn, which in order:
            t0 = time.perf_counter()
            fn()
            pair[which] = time.perf_counter() - t0
        ratios.append(pair[0] / pair[1])
        ts.append(pair[0])
        tf.append(pair[1])
    return statistics.median(ratios), statistics.median(ts), statistics.median(tf)


# --- say which test failed where the public CI API can read it ---------------
def pytest_terminal_summary(terminalreporter):
    """On GitHub Actions, emit one ::error annotation per failed test.

    A run's logs need a signed-in download, but its check-run annotations are
    public. Without this a failing job says only "exit code 1" there; with it,
    the failing test and the last lines of its message are readable by anyone
    looking at the run. Annotations are capped per step, so only the first
    few failures are named -- enough to start from.
    """
    import os
    import collections
    skips = collections.Counter()
    for rep in terminalreporter.stats.get("skipped", []):
        reason = rep.longrepr[2] if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
        skips[reason.replace("Skipped: ", "")[:120]] += 1
    if skips:
        terminalreporter.write_sep("-", "skips by reason")
        for reason, n in skips.most_common():
            terminalreporter.write_line("%5d  %s" % (n, reason))
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    if skips:
        lines = "%0A".join("%d  %s" % (n, r.replace("%", "%25")) for r, n in skips.most_common(15))
        terminalreporter.write_line("::notice title=Skips (%d)::%s" % (sum(skips.values()), lines))
    reports = (terminalreporter.stats.get("failed", []) +
               terminalreporter.stats.get("error", []))
    for rep in reports[:10]:
        text = str(getattr(rep, "longreprtext", "") or rep.longrepr or "")
        tail = "\n".join(text.strip().splitlines()[-12:])
        tail = tail.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
        title = rep.nodeid.replace(",", ";").replace("::", " ")[:200]
        terminalreporter.write_line("::error title=%s::%s" % (title, tail[:3000]))
