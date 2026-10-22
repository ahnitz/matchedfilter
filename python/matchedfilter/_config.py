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
"""
from dataclasses import dataclass
from typing import Optional, Tuple

SECTIONS = (
    ("config", "Configuration"),
    ("diagnostic", "Diagnostics (output only)"),
    ("override", "Measurement overrides (change what runs)"),
)


@dataclass(frozen=True)
class Var:
    """One environment variable. ``usage`` is how the document names it (with its value
    when that is the point, e.g. ``MF_AUTOTUNE=0``); ``default`` is what unset means, as
    the document says it; ``side`` is ``py``, ``c`` or ``both``. ``row`` names the variable
    whose row of the document also covers this one (siblings documented together)."""
    name: str
    section: str
    side: str
    default: str = ""
    doc: str = ""
    usage: Optional[str] = None
    row: Optional[str] = None


VARS: Tuple[Var, ...] = (
    # Configuration
    Var("MF_DEVICE", "config", "py", "`cpu`",
        "Device for plans built without one (`device.parse(None)`)."),
    Var("MF_COST_FILE", "config", "py", "unset",
        "JSON file of measured cost models and trial locks, kept between processes. Unset: "
        "cold start, no trials kept. One writer per open contest: processes sharing a file "
        "while a trial is open overwrite each other's samples (said once per contest)."),
    Var("MF_EXECUTION_POLICY", "config", "py", "the shipped `execution-policy.json`",
        "Another execution-policy table."),
    Var("MF_ISA", "config", "both", "best the CPU supports",
        "SIMD target (also `matchedfilter.set_target`)."),
    # Diagnostics
    Var("MF_AUTOTUNE_LOG", "diagnostic", "py", "", "Log block-size, chain and trial decisions.",
        usage="MF_AUTOTUNE_LOG=1"),
    Var("MF_HMF_PROF", "diagnostic", "c", "", "Per-tier CPU tick counters in hierarchical plans.",
        usage="MF_HMF_PROF=1"),
    Var("MF_HMF_TRACE", "diagnostic", "c", "", "Trace hierarchical plan runs to stderr.",
        usage="MF_HMF_TRACE=1"),
    Var("MF_HMF_DUMP", "diagnostic", "c", "", "Dump coarse-pass data for the GPU mirror tests.",
        usage="MF_HMF_DUMP=<file>"),
    Var("MF_GATE16_DEBUG", "diagnostic", "c", "",
        "FP16 gate error data for tools/gate16_error.py.",
        usage="MF_GATE16_DEBUG`, `MF_GATE16_DEBUG_MAX"),
    Var("MF_GATE16_DEBUG_MAX", "diagnostic", "c", row="MF_GATE16_DEBUG"),
    Var("MF_GPU_TIMING", "diagnostic", "py", "", "Device-time collection across GPU contexts.",
        usage="MF_GPU_TIMING=1"),
    Var("MF_GPU_PROFILE", "diagnostic", "py", "", "Phase timestamps in recorded Vulkan plans.",
        usage="MF_GPU_PROFILE=1"),
    Var("MF_ROOFLINE_DATAPATH", "diagnostic", "py", "",
        "SIMD datapath width for `_roofline` where detection is wrong (e.g. 256 on Strix "
        "Point).", usage="MF_ROOFLINE_DATAPATH=<bits>"),
    Var("MF_VK_SUBGROUP_MEASURING", "diagnostic", "py", "",
        "Internal: marks the subprocess that measures Vulkan subgroup sizes."),
    # Measurement overrides
    Var("MF_AUTOTUNE", "override", "py", "on", "No timed trials: the model's choices stand.",
        usage="MF_AUTOTUNE=0"),
    Var("MF_CHAIN_FORCE", "override", "py", "unset",
        "Pin the gate chain (cross-device comparisons; results depend on the chain).",
        usage="MF_CHAIN_FORCE=b1,b2` or `n:b1,b2;..."),
    Var("MF_CHAIN_MARGIN", "override", "py", "built-in",
        "Chain shortlist margin; batches per chain trial.",
        usage="MF_CHAIN_MARGIN`, `MF_CHAIN_TRIALS"),
    Var("MF_CHAIN_TRIALS", "override", "py", row="MF_CHAIN_MARGIN"),
    Var("MF_BLOCK_TRIALS", "override", "py", "built-in", "Samples per block-size trial."),
    Var("MF_DIRECT_REFINE", "override", "py", "on",
        "CPU refines by transform only (no direct correlation).", usage="MF_DIRECT_REFINE=0"),
    Var("MF_GATE16", "override", "c", "on where built", "No FP16 first gate on the CPU.",
        usage="MF_GATE16=0"),
    Var("MF_DGROUP", "override", "c", "the plan's series group",
        "Blocks per hierarchical series batch.", usage="MF_DGROUP=<n>"),
    Var("MF_PBMAX", "override", "c", "built-in",
        "Largest n run as pair-batched transforms.", usage="MF_PBMAX=<n>"),
    Var("MF_GMAJOR", "override", "c", "1", "Unfused product path (cross-check).",
        usage="MF_GMAJOR=0"),
    Var("MF_ILAY", "override", "c", "1",
        "Strided intermediate layout. Slower on Zen 3 and Zen 5, faster on the M2 at "
        "n >= 2^18 (4-9%); to become a measured candidate.", usage="MF_ILAY=0"),
    Var("MF_CORR_NO_STREAM", "override", "c", "off",
        "No non-temporal stores in continuous correlation.", usage="MF_CORR_NO_STREAM=1"),
    Var("MF_BAND_FORWARD", "override", "py", "measured", "GPU band forward off/on.",
        usage="MF_BAND_FORWARD=0/1"),
    Var("MF_COARSE_LAYOUT", "override", "py", "measured", "Force GPU coarse layouts by label.",
        usage="MF_COARSE_LAYOUT=<labels>"),
    Var("MF_VK_COARSE_PPG", "override", "py", "measured", "Fix a Vulkan coarse layout field.",
        usage="MF_VK_COARSE_PPG`, `_TILE`, `_SUBGROUP`, `_TWT"),
    Var("MF_VK_COARSE_TILE", "override", "py", row="MF_VK_COARSE_PPG"),
    Var("MF_VK_COARSE_SUBGROUP", "override", "py", row="MF_VK_COARSE_PPG"),
    Var("MF_VK_COARSE_TWT", "override", "py", row="MF_VK_COARSE_PPG"),
    Var("MF_METAL_COARSE_PPG", "override", "py", "measured", "Fix a Metal coarse layout field.",
        usage="MF_METAL_COARSE_PPG"),
    Var("MF_VK_SUBGROUP", "override", "py", "measured", "Force a Vulkan subgroup size.",
        usage="MF_VK_SUBGROUP=<size>"),
    Var("MF_VK_C16_BOUND", "override", "py", "1",
        "Electing coarse kernel instead of the bound-only one.", usage="MF_VK_C16_BOUND=0"),
    Var("MF_METAL_IEEE", "override", "py", "per kernel",
        "IEEE math for all or no Metal kernels.", usage="MF_METAL_IEEE=all/none"),
    Var("MF_GPU_FUSE_INTERLEAVE", "override", "py", "measured",
        "Fixed Vulkan fusion interleave depth.", usage="MF_GPU_FUSE_INTERLEAVE=<n>"),
    Var("MF_GPU_ITEMS", "override", "py", "on",
        "Single-template GPU jobs of a batch run one by one.", usage="MF_GPU_ITEMS=0"),
    Var("MF_GPU_QUEUE_AHEAD", "override", "py", "8", "GPU submissions in flight.",
        usage="MF_GPU_QUEUE_AHEAD=<n>"),
    Var("MF_DEVICE_FOLLOWUPS", "override", "py", "on",
        "Threshold-0 follow-ups per group rather than in one device submission.",
        usage="MF_DEVICE_FOLLOWUPS=0"),
    Var("MF_SINGLE_DEVICE", "override", "py", "auto",
        "Keep every call on the bank's device (the pure-GPU ladder).",
        usage="MF_SINGLE_DEVICE=bank"),
)

#: Names in the code that are not environment variables: Metal shader macros the package
#: defines when it compiles a kernel.
SHADER_MACROS = frozenset({"MF_C16_RAW", "MF_COARSE_TWT", "MF_DATA_SCALE_BITS",
                           "MF_DATA_STRIDE", "MF_ROW_WINDOWS"})

#: Removed variables and why (the document lists them; setting one changes nothing).
REMOVED = (
    ("2026-10-17", "switches no tool, test or CI job used were removed (their defaults kept)",
     ("MF_BLOCK_TRIAL_RANKS", "MF_CUDA_BLOCKING_SYNC", "MF_CUDA_GRAPHS", "MF_CUDA_PREFETCH",
      "MF_DIRECT_TRACE", "MF_FUSE", "MF_GATE16_ELECT", "MF_GBLK", "MF_GPU_FUSE",
      "MF_GPU_FUSE_CACHE", "MF_GPU_FUSE_CHUNK", "MF_MFTILE", "MF_N1", "MF_NOSTORE",
      "MF_SERPAD", "MF_SRPROD", "MF_VK_NO_SUBGROUP_PIN")),
    ("2026-10-22", "a stored trial lock is final; the steady re-check it switched on could "
     "make processes sharing a cost file choose differently", ("MF_TRIAL_RECHECK",)),
    ("2026-10-22", "stage-B blocking measured slower at every length on Zen 3, Zen 5 and "
     "the M2", ("MF_BBLK",)),
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
