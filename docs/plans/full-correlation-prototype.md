# Full-correlation output prototype

Decision pending. This branch adds internal CPU and Vulkan proof-of-concept paths for
`ifft(data * conj(template)) * n`, returned as every complex64 lag in natural
order. The existing peak-only paths are unchanged. It does not expose a public
`MatchedFilter` method: the performance tradeoff should be accepted first.

On the Ryzen AI MAX+ 395 (AVX3) and Radeon 8060S, with 16 data spectra × 32
templates and precomputed complex64 spectra:

| n | Output | CPU full | GPU full | FFTW full | CPU peak | GPU peak |
|---:|---:|---:|---:|---:|---:|---:|
| 2048 | 8 MiB | 0.74 ms | 0.34 ms | 1.03 ms | 0.78 ms | 0.10 ms |
| 4096 | 16 MiB | 1.82 ms | 0.75 ms | 4.74 ms | 1.59 ms | 0.16 ms |
| 8192 | 32 MiB | 4.39 ms | 4.43 ms | 10.38 ms | 3.20 ms | 0.29 ms |

Times are end-to-end calls, with a median of five timed repetitions and at
least 80 ms of iterations per repetition. FFTW uses one thread,
`FFTW_MEASURE`, batched single-precision inverse transforms, and includes the
spectrum product in each timed call. Its plan and matchedfilter ingest are
excluded. The GPU call includes input upload, queue completion, and copying
all lags back to a NumPy array. Times are host wall time, not shader-only time.
The 8192 GPU result is at parity with this optimized CPU path; it still beats
the FFTW product-plus-inverse path by about 2.3×. At 2048 and 4096 the GPU
full path beats FFTW by about 3.0× and 6.3×. It is 3–15× slower than the GPU
peak path because full output moves 8–32 MiB per call where the peak path
returns only one value per pair.

A separate 8192 GPU measurement isolated ~0.29 ms for submit/completion and
~2.0 ms for copying the 32 MiB mapped output to NumPy. That points to output
movement, rather than the fused transform, as the largest remaining cost.

`tests/test_full_correlation_prototype.py` checks CPU and Radeon Vulkan
against NumPy's independent complex inverse FFT at 2048, 4096 and 8192;
all six tests pass. The maximum relative errors in the timed batches were
below 2e-7 on CPU and 1.3e-6 on GPU. The prototype only builds GPU kernels
for those three sizes, and its CPU path currently assumes the balanced
fused-product layout. A public feature would need all supported sizes,
robust bounded GPU output batching, Metal support, cache integration, and a
stable array ownership contract.
