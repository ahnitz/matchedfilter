"""matchedfilter - batched correlation with full or peak-only output.

Correlate D data segments against T templates and report, for each pair, the
loudest sample in each bin of a search window:

    >>> import matchedfilter as mf
    >>> filt = mf.MatchedFilter(1 << 14, ndata=16, ntemplates=16)
    >>> filt.set_data(data_spectra)       # (16, 16384) complex64, ALREADY FFT'd
    >>> filt.set_templates(template_spectra)
    >>> peaks = filt.run(binsize=1024, threshold=t, window=(a, b))
    >>> peaks["index"], peaks["value"]

Produce the spectra with whatever you already use - numpy, MKL, FFTW.  matchedfilter
does not need to own that step, and there is no plan object to manage: the
MatchedFilter is built once and reused for every pair.

Inputs are FREQUENCY-DOMAIN: the unnormalised forward transform of each segment,
in natural order.  Ingest only rearranges - templates are conjugated and both
sides are stored in the layout the correlation loop walks - which measures at
2-4% of total and shrinks as the number of templates grows.

Peak-only lengths are powers of two from 64 to 1048576 on CPU and 64 to 65536
on GPU. Full-output lengths are 1024 to 4194304 on either device, subject to
device limits. Hierarchical calibration coverage is separate from transform support.
"""
import hashlib
import math
from types import SimpleNamespace
from typing import NamedTuple, Optional
import operator
import os
import sys
import threading
import time
import warnings

import numpy as np
from . import _config
_config.check_environment()   # before _core reads any of it
from . import _core
from . import gatechain as _gatechain
from . import _chains, _choice, _prices
from ._choice import _AUTOTUNE_LOCK, _autotune_enabled, _log_autotune  # noqa: F401
from ._results import PEAK_DTYPE, _Deferred, _SparsePeaks  # noqa: F401  (public, and root names)

try:
    from importlib.metadata import version as _version, PackageNotFoundError
    __version__ = _version("matchedfilter")
except (ImportError, PackageNotFoundError):  # running from a source tree
    __version__ = "0.0.0.dev0"


__all__ = ["MatchedFilter", "CorrelationFilter", "HierarchicalFilter", "PEAK_DTYPE", "backend",
           "targets", "set_target", "devices", "Device", "__version__",
           "get_autotune_state", "clear_autotune_cache",
           "TimeDomainFilterBank", "FilterResults", "taps_to_spectra",
           "template_spectra", "template_valid", "include_dir", "UnsupportedSize"]

from .time_domain import TimeDomainFilterBank, FilterResults, template_spectra, template_valid

# The filters live in _filter and _hierarchical; the package is their public home. Their
# private names stay importable from here for the modules and tools that reach them so.
from ._filter import (MatchedFilter, CorrelationFilter, _GPU_SIZES, _CORR_PFFT,  # noqa: F401
                      _DLPACK_HOST, _DLPACK_NAMES, _from_any, _check_threshold, _as_c64,
                      _unpack_half, _compute_module, _SeriesOutput, _format_result,
                      _valid_series_window, _automatic_series_layout, _absolute_peak_indices,
                      _SCRATCH, _scratch_counts, _host_copy)
from ._hierarchical import (HierarchicalFilter, _Resolved, _uncovered_message,  # noqa: F401
                            _band_features, _BEFF_MIN, _uncovered_reference, _normalize_chain,
                            _Q15_BANDS, _q15_available, _CPU_TRIAL_WORK, _record_cpu_trial,
                            _direct_refine_enabled)
for _cls in (MatchedFilter, CorrelationFilter, HierarchicalFilter):
    _cls.__module__ = __name__       # public names, reprs and pickle paths stay matchedfilter.*
del _cls


def taps_to_spectra(taps, counts, n, max_taps=None, out=None):
    """Convert time-domain FIR filter taps to frequency-domain spectra in C.

    Vectorized implementation with AVX-512 SIMD and circular center-tap roll alignment.
    Releases the Python GIL during transformation.

    Parameters:
        taps: 2D array of shape (n_templates, max_taps) float32
        counts: 1D array of tap counts (int64 or int32)
        n: FFT block size (int)
        max_taps: Optional maximum taps (defaults to taps.shape[1])
        out: Optional output array of shape (n_templates, n) complex64

    Returns:
        Complex64 array of shape (n_templates, n) with forward FFT spectra.
    """
    taps_arr = np.ascontiguousarray(taps, dtype=np.float32)
    if taps_arr.ndim != 2:
        raise ValueError("taps must be a 2D array of shape (n_templates, max_taps)")
    n_templates, default_max = taps_arr.shape
    m_taps = default_max if max_taps is None else int(max_taps)
    counts_arr = np.ascontiguousarray(counts, dtype=np.int64)
    if counts_arr.ndim != 1 or len(counts_arr) != n_templates:
        raise ValueError("counts must be a 1D array matching n_templates")
    if out is None:
        out_spec = np.empty((n_templates, int(n)), dtype=np.complex64)
    else:
        out_spec = np.ascontiguousarray(out, dtype=np.complex64)
        if out_spec.shape != (n_templates, int(n)):
            raise ValueError(f"out shape {out_spec.shape} must match ({n_templates}, {n})")

    _core.taps_to_spectra(taps_arr, counts_arr, int(n), m_taps, out_spec)
    return out_spec


def backend():
    """Name of the SIMD target selected for this CPU, e.g. ``"AVX2"``.

    Which one runs depends on the host, so a benchmark number is not
    interpretable without it.  ``MF_ISA`` forces one from the environment and
    :func:`set_target` does the same inside a running process.
    """
    return _core.backend()


def targets():
    """SIMD targets this build contains that this CPU can run, widest first -- only
    ``MF_ISA``'s target when it is set, since ``MF_ISA`` restricts the process to it.

    What a build contains is decided by the compiler, not by matchedfilter, so
    this is the only reliable list -- a machine without AVX-512 will not
    report ``AVX3`` however the wheel was built.
    """
    return _core.targets()


def set_target(name):
    """Narrow the choice to one of :func:`targets`, or restore the default with ``None``
    (``MF_ISA``'s target when it is set, else the hardware's choice).

    For comparing targets in one process.  Plans already created keep the kernel they
    were built with, so create the plan after setting this.  Raises ValueError for a
    target that is not in :func:`targets`, and then changes nothing.
    """
    _core.set_target(name)


def devices():
    """Every device this build can dispatch to.  See :mod:`matchedfilter.device`."""
    from .device import devices as _devices
    return _devices()


from ._errors import UnsupportedSize      # noqa: E402


def include_dir():
    """Directory holding matchedfilter.h, for building C code against this package.

    Direct C use is not the main path - the Python class is - but linking is
    cheap to support::

        cc myprog.c $(python -c "import matchedfilter; print('-I'+matchedfilter.include_dir())") ...

    The C interface is the same ten functions the class wraps; see matchedfilter.h.
    """
    import os
    return os.path.dirname(os.path.abspath(__file__))


def choose_threshold(power, n, snr, fd, band):
    """The single-tier gate at `band` for this reference and budget (gatemodel.gate_for)."""
    from .gatemodel import gate_for
    return gate_for(power, n, int(band), snr, fd)


def get_autotune_state():
    """Snapshot of the process's chain choices and measured trials."""
    with _AUTOTUNE_LOCK:
        return {"choices": dict(_chains._CHAIN_CHOICE),
                "trials": {k: {"winner": v.winner, "samples": {c: list(s) for c, s in v.samples.items()}}
                           for k, v in _chains._CHAIN_TRIALS.items()}}


def clear_autotune_cache():
    """Forget every workload choice and trial this process made: chain choices and their
    trials, Q15 trials and the model's Q15 shortlist, block-size trials, the single-device,
    single-batch and fused-batch device choices, and the CPU forward, Q15 tier-0 and direct-refine
    prices.
    The next use starts afresh from MF_COST_FILE. Machine state is kept: cost models
    (gatechain._COSTS), correlation prices and the kernel choices a GPU device holds."""
    from . import time_domain as _td
    with _AUTOTUNE_LOCK:
        _chains._CHAIN_CHOICE.clear()
        _chains._CHAIN_TRIALS.clear()
        _chains._Q15_TRIALS.clear()
        _chains._Q15_MODEL.clear()
        _prices._CPU_FWD_PFFT.clear()
        _prices._Q15_TIER0.clear()
        _prices._DIRECT_LAGTAP.clear()
    _td._BLOCK_TRIALS.state.clear()
    _choice.reset(scope="workload")


def __getattr__(name):
    """Expose ``Device`` without enumerating hardware at import time.

    Listing devices creates a Vulkan instance, which is far too much work to
    do on ``import matchedfilter`` for the majority of callers who will only
    ever use the CPU.
    """
    if name == "Device":
        from .device import Device
        return Device
    if name == "device":
        import importlib
        return importlib.import_module(".device", __name__)
    raise AttributeError(name)
