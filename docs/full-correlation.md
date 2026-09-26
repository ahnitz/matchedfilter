# Full correlation and the cost of keeping lags

The library now has three answers to the same spectral pair calculation. With
`CorrelationFilter`, the answer is every complex lag. With `MatchedFilter`, it
is one complex value and its index per output bin. With `HierarchicalFilter`,
a coarse gate first decides which pairs need the full peak transform. Each
choice makes a stronger assumption about what the caller will use.

The full-output mode computes the unnormalised circular inverse transform of
`D * conj(H)`. It does not allocate a separate product array. The CPU's stage-A
loader forms that product as it reads the stored spectra; the GPU's first
transform stage does the same. The last transform stage writes natural-order
complex lags rather than scanning for a maximum. The full mode thus preserves
the product fusion, input layout and bank reuse that a separate product plus
general FFT cannot use. It gives up the peak-only mode's saving from omitting
the full result array.

At lengths 2^10–2^16, the GPU computes one pair per workgroup. From 2^17
through 2^22, it uses two dispatches: the first writes a transposed intermediate
array, and the second completes the inverse transform and writes ordered lags.
Large `run_series` blocks use the same two-stage decomposition for their
forward FFT. Those large transforms are supported, but the intermediate array
and full output each need eight bytes per lag per pair. At 2^22, one pair
therefore needs about 64 MiB of scratch plus output, before its input spectra.

The class accepts the same device selection, bank setters, pair selectors and
`run_series` block convention as the peak-only class. It returns a fresh
`complex64` result by default. An `out` argument gives callers control over
storage and permits repeated runs without another result allocation. GPU
`empty_shared()` output avoids an extra device-to-host copy. Large banks can
be processed through selectors; automatic allocation stops at 512 MiB.

The [overview figure](../README.md#performance) measures all four stages on
one bank. The FFTW and rocFFT references time the inverse transform alone;
the filter modes also form the spectral product. A full-output bar uses a
reused result array and a peak-only bar returns only the peaks. This reflects
the costs of the requested answers, including the memory traffic of all lags,
rather than claiming the modes perform identical work.

Correctness tests compare every output sample with an independent NumPy FFT
from 2^10 through 2^22 on CPU and the available GPU. They also cover phase,
lag order, selectors, output ownership, zero-padded series blocks and the
CPU's alternate pair-batch layout. Metal artifacts are built from the same
Slang source and tested in the macOS CI job; local Radeon measurements do not
substitute for Metal performance data.
