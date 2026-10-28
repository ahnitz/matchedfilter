"""Every environment variable matchedfilter reads, in one table.

Each entry says what kind of value the variable takes, its default, which side reads it
(the Python package, the C extension, or both), the section of docs/environment.md it
belongs to, and what it does. docs/environment.md is generated from this table
(tools/gen_environment_doc.py), and tests/test_config_registry.py checks that every
``MF_*`` name the code reads is here, that everything here is read, and that the
document is current.

Sections:

- ``config``: configuration a user may set.
- ``diagnostic``: output only; results never depend on one.
- ``override``: changes what runs (and so, for the statistical gates, which peaks a chain
  dismisses); for measurement and tests.
- ``tools``: read by tools/, the builds or the tests, never by the package (side
  ``tools``); each parses its own, so the package only knows the names.
"""
import difflib
import os
import warnings
from dataclasses import dataclass
from typing import Any, Optional, Tuple

SECTIONS = (
    ("config", "Configuration"),
    ("diagnostic", "Diagnostics (output only)"),
    ("override", "Measurement overrides (change what runs)"),
    ("tools", "Tools, builds and tests (read outside the package)"),
)


@dataclass(frozen=True)
class Var:
    """One environment variable. ``usage`` is how the document names it (with its value
    when that is the point, e.g. ``MF_AUTOTUNE=0``); ``default`` is what unset means, as
    the document says it; ``side`` is ``py``, ``c``, ``both`` or ``tools``. ``row`` names the variable
    whose row of the document also covers this one (siblings documented together).

    ``kind`` is how a value parses (``get``): ``flag``, ``int``, ``float``, ``choice``
    (one of ``choices``) or ``text`` (checked by its reader); ``value`` is what unset or
    empty gives (None: the reader's own built-in or measured choice)."""
    name: str
    section: str
    side: str
    default: str = ""
    doc: str = ""
    usage: Optional[str] = None
    row: Optional[str] = None
    kind: str = "text"
    value: Any = None
    choices: Tuple[str, ...] = ()


VARS: Tuple[Var, ...] = (
    # Configuration
    Var("MF_DEVICE", "config", "py", "`cpu`",
        "Device for plans built without one (`device.parse(None)`).", kind="text", value="cpu"),
    Var("MF_COST_FILE", "config", "py", "unset",
        "JSON file of measured cost models and trial locks, kept between processes. Unset: "
        "cold start, no trials kept. One writer per open contest: processes sharing a file "
        "while a trial is open overwrite each other's samples (said once per contest).", kind="text"),
    Var("MF_EXECUTION_POLICY", "config", "py", "the shipped `execution-policy.json`",
        "Another execution-policy table.", kind="text"),
    Var("MF_ISA", "config", "both", "best the CPU supports",
        "SIMD target (also `matchedfilter.set_target`).", kind="text"),
    Var("MF_DIRECT_REFINE", "config", "py", "on",
        "CPU refines by transform only (no direct correlation): exact bin maxima for the "
        "pairs that pass the gates.", usage="MF_DIRECT_REFINE=0", kind="flag", value=True),
    # Diagnostics
    Var("MF_AUTOTUNE_LOG", "diagnostic", "py", "", "Log block-size, chain and trial decisions.",
        usage="MF_AUTOTUNE_LOG=1", kind="flag", value=False),
    Var("MF_HMF_PROF", "diagnostic", "c", "", "Per-tier CPU tick counters in hierarchical plans.",
        usage="MF_HMF_PROF=1", kind="flag", value=False),
    Var("MF_HMF_TRACE", "diagnostic", "c", "", "Trace hierarchical plan runs to stderr.",
        usage="MF_HMF_TRACE=1", kind="flag", value=False),
    Var("MF_HMF_DUMP", "diagnostic", "c", "", "Dump coarse-pass data for the GPU mirror tests.",
        usage="MF_HMF_DUMP=<file>", kind="text"),
    Var("MF_GATE16_DEBUG", "diagnostic", "c", "",
        "FP16 gate error data for tools/gate16_error.py.",
        usage="MF_GATE16_DEBUG`, `MF_GATE16_DEBUG_MAX", kind="flag", value=False),
    Var("MF_GATE16_DEBUG_MAX", "diagnostic", "c", row="MF_GATE16_DEBUG", kind="flag", value=False),
    Var("MF_GPU_TIMING", "diagnostic", "py", "", "Device-time collection across GPU contexts.",
        usage="MF_GPU_TIMING=1", kind="flag", value=False),
    Var("MF_GPU_PROFILE", "diagnostic", "py", "", "Phase timestamps in recorded Vulkan plans.",
        usage="MF_GPU_PROFILE=1", kind="flag", value=False),
    Var("MF_ROOFLINE_DATAPATH", "diagnostic", "py", "",
        "SIMD datapath width for `_roofline` where detection is wrong (e.g. 256 on Strix "
        "Point).", usage="MF_ROOFLINE_DATAPATH=<bits>", kind="int"),
    Var("MF_VK_SUBGROUP_MEASURING", "diagnostic", "py", "",
        "Internal: marks the subprocess that measures Vulkan subgroup sizes.", kind="flag", value=False),
    # Measurement overrides
    Var("MF_AUTOTUNE", "override", "py", "on", "No timed trials: the model's choices stand.",
        usage="MF_AUTOTUNE=0", kind="flag", value=True),
    Var("MF_CHAIN_FORCE", "override", "py", "unset",
        "Pin the gate chain (cross-device comparisons; results depend on the chain).",
        usage="MF_CHAIN_FORCE=b1,b2` or `n:b1,b2;...", kind="text"),
    Var("MF_TRIAL_ROUNDS", "override", "py", "5",
        "Paired rounds before a joint trial decides (it takes up to twice as many).", kind="int"),
    Var("MF_GATE16", "override", "c", "on where built", "No FP16 first gate on the CPU.",
        usage="MF_GATE16=0", kind="flag", value=True),
    Var("MF_DGROUP", "override", "c", "the plan's series group",
        "Blocks per hierarchical series batch.", usage="MF_DGROUP=<n>", kind="int"),
    Var("MF_PBMAX", "override", "c", "built-in",
        "Largest n run as pair-batched transforms.", usage="MF_PBMAX=<n>", kind="int"),
    Var("MF_ILAY", "override", "c", "1",
        "Strided intermediate layout. Slower on Zen 3 and Zen 5, faster on the M2 at "
        "n >= 2^18 (4-9%); to become a measured candidate.", usage="MF_ILAY=0", kind="flag", value=True),
    Var("MF_CORR_NO_STREAM", "override", "c", "off",
        "No non-temporal stores in continuous correlation.", usage="MF_CORR_NO_STREAM=1", kind="flag", value=False),
    Var("MF_BAND_FORWARD", "override", "py", "measured", "GPU band forward off/on.",
        usage="MF_BAND_FORWARD=0/1", kind="flag"),
    Var("MF_COARSE_LAYOUT", "override", "py", "measured", "Force GPU coarse layouts by label.",
        usage="MF_COARSE_LAYOUT=<labels>", kind="text"),
    Var("MF_VK_SUBGROUP", "override", "py", "measured", "Force a Vulkan subgroup size.",
        usage="MF_VK_SUBGROUP=<size>", kind="text"),
    Var("MF_COARSE_RAW", "override", "py", "0",
        "The fp16 coarse tier reports its raw maximum instead of an upper bound (every GPU "
        "backend; the physics tests and tools/c16_sigma.py).",
        usage="MF_COARSE_RAW=1", kind="flag", value=False),
    Var("MF_GPU_FUSE_INTERLEAVE", "override", "py", "measured",
        "Fixed Vulkan fusion interleave depth.", usage="MF_GPU_FUSE_INTERLEAVE=<n>", kind="int"),
    Var("MF_GPU_ITEMS", "override", "py", "on",
        "Single-template GPU jobs of a batch run one by one.", usage="MF_GPU_ITEMS=0", kind="flag", value=True),
    Var("MF_GPU_QUEUE_AHEAD", "override", "py", "8", "GPU submissions in flight.",
        usage="MF_GPU_QUEUE_AHEAD=<n>", kind="int", value=8),
    Var("MF_DEVICE_FOLLOWUPS", "override", "py", "on",
        "Threshold-0 follow-ups per group rather than in one device submission.",
        usage="MF_DEVICE_FOLLOWUPS=0", kind="flag", value=True),
    Var("MF_SINGLE_DEVICE", "override", "py", "auto",
        "Keep every call on the bank's device (the pure-GPU ladder).",
        usage="MF_SINGLE_DEVICE=bank", kind="choice", choices=("auto", "bank")),
    # Tools, builds and tests
    Var("MF_SLANGC", "tools", "tools", "`slangc` on PATH",
        "The Slang compiler tools/build_spirv.py and build_ptx.py use."),
    Var("MF_SLANGC_ANY_VERSION", "tools", "tools", "0",
        "Build with a slangc other than the pinned version (experiments only).",
        usage="MF_SLANGC_ANY_VERSION=1"),
    Var("MF_NVRTC", "tools", "tools", "`libnvrtc.so.12`", "NVRTC library for the PTX build."),
    Var("MF_CUDA_PATH", "tools", "tools", "found", "CUDA installation for the PTX build."),
    Var("MF_GATE_BANK", "tools", "tools", "unset",
        "Template bank for tools/gate.py's end-to-end checks (also `--bank`).",
        usage="MF_GATE_BANK`, `MF_GATE_PROFILES"),
    Var("MF_GATE_PROFILES", "tools", "tools", row="MF_GATE_BANK"),
    Var("MF_TEASER_N", "tools", "tools", "4096, 16, 512",
        "Shape of tools/teaser_figure.py's run.",
        usage="MF_TEASER_N`, `MF_TEASER_NDATA`, `MF_TEASER_NTMPL"),
    Var("MF_TEASER_NDATA", "tools", "tools", row="MF_TEASER_N"),
    Var("MF_TEASER_NTMPL", "tools", "tools", row="MF_TEASER_N"),
)

#: Names in the code that are not environment variables: Metal shader macros the package
#: defines when it compiles a kernel.
SHADER_MACROS = frozenset({"MF_C16_RAW", "MF_COARSE_TWT", "MF_DATA_SCALE_BITS",
                           "MF_DATA_STRIDE", "MF_ROW_WINDOWS"})

#: Removed variables and why (the document lists them; setting one changes nothing).
REMOVED = (
    ("2026-10-27", "the pycbc capture hook that read it, writing tools/hier_bench.py "
     "fixtures, is gone; tools/setup_capture.py captures a job's calls", ("MF_CAPTURE",)),
    ("2026-10-27", "the tensor-core coarse bound is built from the sigma measured by "
     "tools/cuda_tc_sigma.py; a hand-set constant is not a bound, and nothing set it",
     ("MF_TC_KAPPA",)),
    ("2026-10-27", "no tool, test or CI job set it; Metal keeps fast math except in the "
     "survivor compaction, which is IEEE because it must list a NaN coarse value",
     ("MF_METAL_IEEE",)),
    ("2026-10-26", "block sizes and the Q15 screen are one joint trial of paired rounds, "
     "and the chain is the model's; MF_TRIAL_ROUNDS sets its rounds",
     ("MF_BLOCK_TRIALS", "MF_CHAIN_TRIALS")),
    ("2026-10-26", "the gate chain is the cost model's, never a trial arm (MF_CHAIN_FORCE "
     "pins one for measurement)", ("MF_CHAIN_MARGIN",)),
    ("2026-10-17", "switches no tool, test or CI job used were removed (their defaults kept)",
     ("MF_BLOCK_TRIAL_RANKS", "MF_CUDA_BLOCKING_SYNC", "MF_CUDA_GRAPHS", "MF_CUDA_PREFETCH",
      "MF_DIRECT_TRACE", "MF_FUSE", "MF_GATE16_ELECT", "MF_GBLK", "MF_GPU_FUSE",
      "MF_GPU_FUSE_CACHE", "MF_GPU_FUSE_CHUNK", "MF_MFTILE", "MF_N1", "MF_NOSTORE",
      "MF_SERPAD", "MF_SRPROD", "MF_VK_NO_SUBGROUP_PIN")),
    ("2026-10-22", "a stored trial lock is final; the steady re-check it switched on could "
     "make processes sharing a cost file choose differently", ("MF_TRIAL_RECHECK",)),
    ("2026-10-22", "stage-B blocking measured slower at every length on Zen 3, Zen 5 and "
     "the M2", ("MF_BBLK",)),
    ("2026-10-22", "the unfused stage-A product it forced measured slower at every length "
     "on Zen 3, Zen 5 and the M2", ("MF_GMAJOR",)),
    ("2026-10-22", "per-backend coarse layout fields; MF_COARSE_LAYOUT forces a whole "
     "layout by name on every backend", ("MF_VK_COARSE_PPG", "MF_VK_COARSE_TILE",
                                        "MF_VK_COARSE_SUBGROUP", "MF_VK_COARSE_TWT",
                                        "MF_METAL_COARSE_PPG", "MF_METAL_COARSE_TILE",
                                        "MF_METAL_COARSE_TWT")),
    ("2026-10-22", "renamed MF_COARSE_RAW (MF_COARSE_RAW=1 is what MF_VK_C16_BOUND=0 did, "
     "on every GPU backend)", ("MF_VK_C16_BOUND",)),
    ("2026-10-07", "the gate-model simulation cache it located went with the cost tables; "
     "chain thresholds are drawn in each process, and MF_COST_FILE keeps measured costs",
     ("MF_GATE_CACHE_FILE",)),
)

BY_NAME = {v.name: v for v in VARS}


def markdown() -> str:
    """docs/environment.md, rendered from this table."""
    import textwrap
    wrap = lambda text: textwrap.fill(text, 88, break_on_hyphens=False)   # noqa: E731
    out = ["# Environment variables", "",
           wrap("Every environment variable matchedfilter reads, by kind. None is needed for "
                "normal use: unset, each gives the library's default behaviour. Results never "
                "depend on a diagnostic; the overrides change what runs (and so, for the "
                "statistical gates, which peaks a chain dismisses), and exist for measurement "
                "and tests."), "",
           wrap("Generated from `python/matchedfilter/_config.py` by "
                "`tools/gen_environment_doc.py`; edit the table there."), ""]
    for when, why, names in REMOVED:
        out += [wrap("Removed %s: %s: %s." % (when, why, ", ".join(names))), ""]
    out += [wrap("Older notes in docs/ that mention a removed variable describe past "
                 "studies."), ""]
    for key, title in SECTIONS:
        rows = [v for v in VARS if v.section == key and v.row is None]
        with_default = key != "diagnostic"
        out += ["## " + title, ""]
        out += ["| Variable | Default | Effect |", "|---|---|---|"] if with_default \
            else ["| Variable | Effect |", "|---|---|"]
        for v in rows:
            cell = "`%s`" % (v.usage or v.name)
            out.append("| %s | %s | %s |" % (cell, v.default, v.doc) if with_default
                       else "| %s | %s |" % (cell, v.doc))
        out.append("")
    return "\n".join(out)


#: The one rule for a flag's value (any case, surrounding space ignored); unset or empty
#: gives the variable's default.
TRUE = ("1", "true", "yes", "on")
FALSE = ("0", "false", "no", "off")


def parse(var: Var, raw: str):
    """A variable's value from its text: the default when the text is empty, else as its
    kind says; ValueError naming the variable and what it accepts otherwise."""
    s = raw.strip()
    if not s:
        return var.value
    if var.kind == "flag":
        if s.lower() in TRUE:
            return True
        if s.lower() in FALSE:
            return False
        accepts = "/".join(FALSE[:1] + TRUE[:1]) + ", false/true, no/yes or off/on"
    elif var.kind in ("int", "float"):
        try:
            return int(s) if var.kind == "int" else float(s)
        except ValueError:
            accepts = "an integer" if var.kind == "int" else "a number"
    elif var.kind == "choice":
        if s.lower() in var.choices:
            return s.lower()
        accepts = "one of " + ", ".join(var.choices)
    else:
        return s
    raise ValueError("%s=%s: %s takes %s (unset or empty: the default)"
                     % (var.name, raw, var.name, accepts))


def get(name: str, builtin=None):
    """The value of a registered variable in this process's environment, read now; a
    variable whose default is the reader's own (value None) gives builtin when unset."""
    v = parse(BY_NAME[name], os.environ.get(name, ""))
    return builtin if v is None else v


_REMOVED = {n: (when, why) for when, why, group in REMOVED for n in group}


def check_environment(environ=None):
    """At import: every registered MF_* variable set must parse (ValueError otherwise, so a
    typo in a value is not silently the default); a removed or unknown MF_* name warns,
    with the reason or the nearest registered name."""
    environ = os.environ if environ is None else environ
    for name in sorted(k for k in environ if k.startswith("MF_")):
        if name in BY_NAME:
            parse(BY_NAME[name], environ[name])
        elif name in _REMOVED:
            when, why = _REMOVED[name]
            warnings.warn("%s was removed on %s (%s); it has no effect" % (name, when, why),
                          RuntimeWarning, stacklevel=2)
        elif name not in SHADER_MACROS:
            near = difflib.get_close_matches(name, BY_NAME, 1, 0.8)
            warnings.warn("%s is not a matchedfilter variable%s; it has no effect"
                          % (name, "; did you mean %s?" % near[0] if near else ""),
                          RuntimeWarning, stacklevel=2)
