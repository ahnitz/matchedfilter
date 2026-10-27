"""Every tunable dimension the library measures, and the settings in force.

A dimension is declared once (DIMS): its name, how its values read and print, its default and
its scope. An arm of a trial is a label: DEFAULT, every dimension at its default, or the dimensions it
moves, "<dim>=<value>[,<dim>=<value>...]" in DIMS order (compose, moves). A trial's first
pass offers DEFAULT and arms that move one dimension; when it locks another arm, the next
pass offers that arm and the arm with each remaining dimension moved (around), until a pass
keeps its base (_trial.current_pass). One grammar for every trial:

  * "subject" dimensions are resolved by each instance a trial runs on -- a bank's block size
    "n" (its layouts), a plan's screen "q15" -- through its arm_config / use_arm / lock_arm;
  * "batch" dimensions are in force for a run, read here by the code they steer: a GPU
    batch's fusion "fuse", its interleave depth "interleave", where its follow-ups run
    "single", where a lone single-template call runs "side", and the kernels' slots
    "kern:<what>:<band>" (coarse layout, gate way, sparse read: their values are labels, the
    default and alternative each call registers, slot).

The store (setting) answers for a batch dimension: the arm a running trial plays (running),
else the lock of a device set holding the device, else the default. It sits below the GPU host
layer and the backends, which read it; the trials that decide it are above (time_domain,
_trial).
"""
from contextlib import contextmanager
from typing import Dict, Optional

#: The arm with every dimension at its default: a trial's preference.
DEFAULT = "default"


class Dim:
    """A tunable dimension: parse(text) -> value, show(value) -> text, its default value (None:
    the instance's model, or the slot's registered default), scope "subject" or "batch"."""
    __slots__ = ("name", "parse", "show", "default", "scope", "doc")

    def __init__(self, name, parse, show=str, default=None, scope="batch", doc=""):
        self.name, self.parse, self.show = name, parse, show
        self.default, self.scope, self.doc = default, scope, doc


def _flag(v):
    if v not in ("0", "1"):
        raise ValueError(v)
    return v == "1"


def _side(v):
    if v not in ("gpu", "cpu"):
        raise ValueError(v)
    return v


def _show_flag(b):
    return str(int(bool(b)))


DIMS: Dict[str, Dim] = {d.name: d for d in (
    Dim("n", lambda v: "model" if v == "model" else int(v), scope="subject",
        doc="a bank's block size: every block at n, or the model's priced layout"),
    Dim("q15", _flag, _show_flag, scope="subject",
        doc="the Q15 screen as a plan's first tier, where its first band has one"),
    Dim("fuse", _flag, _show_flag, default=True,
        doc="a GPU batch's submissions fused into shared command buffers (_gpuexec.fused): "
            "+16% on an M2, -3 to -6% on an 8060S, nothing on a RENOIR (2026-10-19)"),
    Dim("interleave", int, default=0,
        doc="a fused Vulkan batch's interleave depth: 0 lockstep, 3 the second half's "
            "forward beside the first half's coarse0"),
    Dim("single", _side, default="gpu",
        doc="where a GPU batch's single-template (follow-up) jobs run"),
    Dim("side", _side, default="gpu",
        doc="where a lone single-template call on a GPU bank runs (per call shape)"),
)}
#: Kernel slots are dimensions "kern:<what>:<band>"; their values are the labels each call
#: registers (slot).
KERNEL = "kern:"


def dim(name) -> Dim:
    """The dimension `name` (a kernel slot's made on the fly)."""
    if name in DIMS:
        return DIMS[name]
    if str(name).startswith(KERNEL) and str(name).count(":") == 2:
        return Dim(name, str)
    raise ValueError("not a tunable dimension: %r" % (name,))


def _order(name):
    # declared dimensions in DIMS order, then kernel slots by name: one spelling per arm
    names = list(DIMS)
    return (0, names.index(name), "") if name in DIMS else (1, 0, str(name))


def compose(moved: Dict[str, object]) -> str:
    """The arm moving each dimension in `moved` to its value (DEFAULT when none)."""
    if not moved:
        return DEFAULT
    return ",".join("%s=%s" % (d, dim(d).show(moved[d])) for d in sorted(moved, key=_order))


def arm(name, value) -> str:
    """The arm moving one dimension to value."""
    return compose({name: value})


def moves(label) -> Dict[str, object]:
    """{dimension: value} the arm moves (empty for DEFAULT). Raises ValueError for a label
    that names no arm."""
    s = str(label)
    if s == DEFAULT:
        return {}
    out = {}
    for part in s.split(","):
        name, eq, v = part.partition("=")
        if not eq or name in out:
            raise ValueError("not a trial arm: %r" % s)
        try:
            out[name] = dim(name).parse(v)
        except (TypeError, ValueError):
            raise ValueError("not a trial arm: %r" % s)
    if compose(out) != s:
        raise ValueError("not a trial arm (not in canonical order): %r" % s)
    return out


def valid(label) -> Optional[str]:
    """label when it names an arm, else None (a stored value of another build)."""
    try:
        moves(label)
    except ValueError:
        return None
    return str(label)


def around(base, proposals) -> list:
    """A coordinate pass's arms: base, then base with each proposal (an arm) applied whose
    dimensions base has not moved -- the dimensions a previous pass decided stay put."""
    held = moves(base)
    out = [str(base)]
    for p in proposals:
        mv = moves(p)
        if mv and not set(mv) & set(held):
            a = compose(dict(held, **mv))
            if a not in out:
                out.append(a)
    return out


# ---- the store ------------------------------------------------------------------------------
#: The batch settings a running trial plays (running), {dimension: value}.
_IN_FORCE: Dict[str, object] = {}
#: Each device set's locks: a tuple of "<device> <name>" strings -> {dimension: value}.
_LOCKS: Dict[tuple, Dict[str, object]] = {}
#: Kernel slots per device name: {dimension: (default, alternative)} (slot).
_SLOTS: Dict[str, Dict[str, tuple]] = {}
#: (device name, dimension) consulted since cleared: which slots a batch exercised.
_SEEN = set()


def _holds(devs, device):
    return any(d.startswith(str(device) + " ") or d.endswith(" " + str(device)) for d in devs)


def setting(name, device=None, default=None):
    """A batch dimension's value now: the running trial's arm, else the lock of a device set
    holding `device` (a "gpu:0" spec or a device name; any set when None), else `default`,
    else the dimension's."""
    if name in _IN_FORCE:
        return _IN_FORCE[name]
    for devs, held in _LOCKS.items():
        if name in held and (device is None or _holds(devs, device)):
            return held[name]
    return dim(name).default if default is None else default


def slot(device, what, band, default, alternative):
    """A call on device (its name) consults kernel slot kern:<what>:<band>, whose two labels
    it registers; returns the label to run (setting)."""
    name = "%s%s:%s" % (KERNEL, what, band)
    _SLOTS.setdefault(device, {})[name] = (default, alternative)
    _SEEN.add((device, name))
    return setting(name, device, default)


@contextmanager
def running(settings: Dict[str, object]):
    """Run with these batch settings in force (a trial's arm over the locks)."""
    saved = dict(_IN_FORCE)
    _IN_FORCE.clear()
    _IN_FORCE.update(settings)
    try:
        yield
    finally:
        _IN_FORCE.clear()
        _IN_FORCE.update(saved)


def fingerprint():
    """The settings in force, as a key: a recorded call plan is kept per configuration, so the
    arms a trial plays do not overwrite one another's (and the default's) plans."""
    return tuple(sorted(_IN_FORCE.items(), key=lambda kv: kv[0]))


def locks(devs) -> Dict[str, object]:
    """The device set's locks (the trials fill it)."""
    return _LOCKS.setdefault(devs, {})


def slots(names) -> Dict[str, tuple]:
    """{dimension: (default, alternative)} of the kernel slots registered on these devices."""
    out = {}
    for nm in names:
        out.update(_SLOTS.get(nm, {}))
    return out


def clear() -> None:
    """Forget every lock, slot and record of use (clear_autotune_cache)."""
    _IN_FORCE.clear()
    _LOCKS.clear()
    _SLOTS.clear()
    _SEEN.clear()
