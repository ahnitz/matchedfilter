"""The shipped GPU kernels of each backend, as its build recorded them.

tools/kernel_variants.py writes one manifest per backend (spirv/, metal/, ptx/), every
kernel a record under its artifact's stem: the file, the entry point the host loads, the
facts it was built with (n, cap, ppg, tile, ...) and those read back from the artifact
(local size, workgroup memory; for SPIR-V its descriptors and push-constant bytes). The
hosts take kernel facts from here and restate none of them.

Stems follow one scheme on every backend: <role>_<n>[_<variant>][_lds32], where the _lds32
build is the same kernel staged in 32 KB of workgroup memory for a device that offers less
than the first build asks (runnable).
"""
import json
import pathlib
from functools import lru_cache

from ._kernel_id import BACKENDS

_PACKAGE = pathlib.Path(__file__).resolve().parent
#: A backend's folder where it is not the package's (set_folder): the tests' static checks
#: of a backend an install leaves out read the checkout's.
_FOLDERS = {}


def folder(backend):
    """The package folder holding a backend's artifacts and manifest."""
    return _FOLDERS.get(backend) or _PACKAGE / BACKENDS[backend][0]


def set_folder(backend, path):
    """Read a backend's artifacts and manifest from `path` (None: the package's own)."""
    if path is None:
        _FOLDERS.pop(backend, None)
    else:
        _FOLDERS[backend] = pathlib.Path(path)
    clear()


@lru_cache(maxsize=None)
def manifest(backend):
    """A backend's manifest ({} for an install without one)."""
    try:
        return json.loads((folder(backend) / "manifest.json").read_text())
    except (OSError, ValueError):
        return {}


def record(backend, stem):
    """The manifest record of one kernel, or None where it did not ship."""
    return manifest(backend).get("kernels", {}).get(stem)


def shipped(backend, stem):
    """Whether a kernel shipped."""
    return record(backend, stem) is not None


def runnable(backend, stem, max_shared):
    """The record of the build of `stem` a device with max_shared bytes of workgroup memory
    can run: stem's own, or its 32 KB build (stem + "_lds32") where stem asks for more or did
    not ship. None when neither ships or fits."""
    for name in (stem, stem + "_lds32"):
        rec = record(backend, name)
        if rec is not None and rec.get("lds_bytes", 0) <= max_shared:
            return rec
    return None


def two_stage(backend, n):
    """(n1, n2), the two-stage split of the full correlation at length n, or None where the
    two-stage kernels were not built for n."""
    split = manifest(backend).get("two_stage", {}).get(str(n))
    return None if split is None else (split["n1"], split["n2"])


def clear():
    """Forget the manifests read and the records resolved from them (a test that rebuilds
    an install)."""
    manifest.cache_clear()
    _RESOLVED.clear()


# ---- kernel roles: one table every driver resolves through ---------------------------------

#: The limits a kernel's resolution reads, all fields of the device's properties record
#: (_gpuhost.DeviceProps, ctx.props): artifact_family (the manifest whose kernels it runs),
#: max_group_memory (workgroup memory one group may use), max_threads (threads one group may
#: have) and load_time_constants (whether a kernel's build-time constants are set when its
#: artifact is loaded, so one artifact serves every value; where not, a value that changes
#: the code is an artifact of its own, the "w" coarse builds).
LIMIT_FIELDS = ("artifact_family", "max_group_memory", "max_threads", "load_time_constants")


#: Each role: the stems that serve it at length n, in order of preference (a later one
#: stands only where no earlier one ships or fits), and what else it needs. A stem's 32 KB
#: build (<stem>_lds32) serves it wherever the stem asks more workgroup memory than the
#: device offers (runnable). "two_stage": the role's kernels exist only at the lengths the
#: two-stage split was built for.
_ONE = {
    "peaks": ("tierb_{n}",), "gate": ("tierb_{n}",),
    "peaks1": ("tierb_{n}_onebin", "tierb_{n}"),
    "tier": ("refine_{n}",), "refine": ("refine_{n}",),
    "tier1": ("refine_{n}_onebin", "refine_{n}"), "refine1": ("refine_{n}_onebin", "refine_{n}"),
    "tier1_c16": ("refine_{n}_c16",), "items": ("items_{n}",), "refine_td": ("refine_td",),
    "compact": ("compact",), "compactc": ("compactc",), "compactl": ("compactl",),
    "mark": ("markblocks",), "pack": ("pack_coarse",), "compact_peaks": ("compact_peaks",),
    "forward": ("forward_{n}",), "fwd_tier0": ("forward_tier0_{n}",),
    "fwd_bands": ("forward_bands_{n}",), "fwd_listed": ("forward_listed_{n}",),
    "full": ("full_{n}",), "series": ("full_series_{n}",),
}
_TWO_STAGE = {"tc1": "corr1", "tc2": "corr2", "tcs2": "corr_series2", "tf1": "fwd1",
              "tf2": "fwd2", "root1": "root1", "root2": "root2"}
#: Every kernel role a driver's _x_kernel takes (_gpuexec's driver primitives).
ROLES = frozenset(_ONE) | frozenset(_TWO_STAGE) | {"coarse"}
#: Roles a one-bin build serves, whose gate-only variant (consts gate) is <stem>_gate.
_GATED = ("tier1", "refine1")
#: The names _x_has_kernel answers: an optional kernel (role, at n), served as resolve would.
_OPTIONAL = {"compactc": "compactc", "tier1": "tier1", "tier1_c16": "tier1_c16",
             "fwd_tier0": "fwd_tier0", "items": "items", "refine_td": "refine_td"}


def fits(rec, limits):
    """Whether a manifest record's build runs on a device with these limits (a DeviceProps,
    or any record with LIMIT_FIELDS)."""
    return (rec.get("lds_bytes", 0) <= limits.max_group_memory
            and int((rec.get("local_size") or [0])[0]) <= limits.max_threads)


def _runnable_stem(stem, limits):
    """The stem of stem's build that fits the device -- its own, else its 32 KB build -- or
    None (no record is copied: has_kernel asks this per follow-up batch)."""
    for name in (stem, stem + "_lds32"):
        rec = record(limits.artifact_family, name)
        if rec is not None and fits(rec, limits):
            return name
    return None


def _stems(role, n, consts, limits):
    """The stems that serve `role` at n with these constants, preferred first."""
    c = consts or {}
    if role == "coarse":
        from ._coarse import coarse_stem
        stem = coarse_stem(n, int(c["ppg"]), int(c["tile"]))
        if c.get("twt") and not limits.load_time_constants:
            stem += "w"                        # the twiddle table is an artifact of its own
        return (stem,)
    if role in _TWO_STAGE:
        if two_stage(limits.artifact_family, n) is None:
            return ()
        return ("tc_%s_%d" % (_TWO_STAGE[role], n),)
    if role not in _ONE:
        raise ValueError("no GPU kernel %r" % (role,))
    stems = tuple(s.format(n=n) for s in _ONE[role])
    if c.get("gate"):
        if role not in _GATED:
            raise ValueError("a gate-only build exists for %s only, not %r" % (_GATED, role))
        stems = (stems[0] + "_gate",)          # requested: not replaced by the full build
    return stems


def resolve(limits, role, n=0, consts=None):
    """The manifest record (with its "stem") of the build that serves kernel `role` at
    transform length n on a device with these limits: the first of the role's stems that
    ships, in its own build or its 32 KB one, and fits the device.

    Raises UnsupportedSize where none does -- a role the device cannot run is reported,
    never replaced by another kernel -- and ValueError for a role that is not a kernel."""
    stems = _stems(role, n, consts, limits)
    for stem in stems:
        name = _runnable_stem(stem, limits)
        if name is not None:
            return dict(record(limits.artifact_family, name), stem=name)
    from ._errors import UnsupportedSize
    shipped_ = [s for s in stems if record(limits.artifact_family, s) or record(limits.artifact_family, s + "_lds32")]
    if shipped_:
        rec = record(limits.artifact_family, shipped_[0]) or record(limits.artifact_family, shipped_[0] + "_lds32")
        raise UnsupportedSize(
            "%s (n=%d) needs %d KB of workgroup memory and %d threads; this device offers "
            "%d KB and %d" % (shipped_[0], n, rec.get("lds_bytes", 0) // 1024,
                              int((rec.get("local_size") or [0])[0]),
                              limits.max_group_memory // 1024, limits.max_threads))
    raise UnsupportedSize("no %s kernel for %s at n=%d" % (limits.artifact_family, role, n))


def has_kernel(limits, name, n):
    """Whether the optional kernel `name` (compactc, tier1: a one-bin refine build, tier1_c16,
    fwd_tier0, items, tier1gate: the one-bin refine's gate-only build, refine_td) has a build
    at n that this device runs -- its own stem, not a fallback to another kernel."""
    if name == "tier1gate":
        stem = _ONE["tier1"][0].format(n=n) + "_gate"
    elif name in _OPTIONAL:
        stem = _ONE[_OPTIONAL[name]][0].format(n=n)
    else:
        raise ValueError(name)
    return _runnable_stem(stem, limits) is not None


def has_coarse(limits, band):
    """Whether the fp16 coarse builds shipped at this band (its untiled one runs here)."""
    return _runnable_stem("tierb_%d_c16" % band, limits) is not None


#: Resolved records for the process (KernelRoles._kernel_record): key -> (the properties
#: record it was resolved under, held so its id cannot name another, the record).
_RESOLVED = {}
_NO_CONSTS = {}


class KernelRoles:
    """A driver Context's kernel resolution, written once (every driver inherits it): the
    role table above under the device's properties (ctx.props, LIMIT_FIELDS). A driver
    turns the record _kernel_record returns into its API's pipeline or function."""

    def _kernel_record(self, name, n, consts=None):
        """The manifest record (with "stem") serving kernel role `name` at n (resolve), kept
        for the process per (device properties, role, n, the constants that pick a build):
        a device's contexts -- one per plan, thousands in a search -- share one record per
        kernel instead of each resolving and copying it (that allocation, ~20,000 records in
        a pycbc job, drove extra collections of the cycle collector over its whole heap)."""
        props = self.props
        c = consts or _NO_CONSTS
        key = (id(props), name, n, c.get("ppg"), c.get("tile"), c.get("twt"), c.get("gate"))
        hit = _RESOLVED.get(key)
        if hit is None or hit[0] is not props:
            hit = _RESOLVED[key] = (props, resolve(
                props, name, n, {k: c[k] for k in ("ppg", "tile", "twt", "gate") if k in c}))
        return hit[1]

    def _x_has_kernel(self, name, n):
        """Whether the optional kernel `name` has a build this device runs at n: the driver
        primitive `_x_has_kernel` (_gpuexec; has_kernel lists the names)."""
        return has_kernel(self.props, name, n)

    def _x_has_c16(self, band):
        """Whether the fp16 coarse builds shipped at this band (has_coarse)."""
        return has_coarse(self.props, band)


def coarse_record(limits, band, ppg, tile, twt):
    """The manifest record of the fp16 coarse build (band, ppg, tile, twiddle source), or None
    where it did not ship: what a driver's coarse candidates are made of (_coarse.candidates
    holds them to the device's limits)."""
    stem = _stems("coarse", band, dict(ppg=ppg, tile=tile, twt=twt), limits)[0]
    return record(limits.artifact_family, stem)
