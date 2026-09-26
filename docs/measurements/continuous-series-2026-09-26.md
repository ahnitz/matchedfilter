# Continuous `run_series` output

`valid=(lo, hi)` on a filter defines the regular overlap-save layout. The
three filter classes derive block starts from the supplied series length.
Peak filters return block-major peaks; `CorrelationFilter` returns a reused
template-major continuous complex64 series. Explicit block layouts still use
the existing `run_series(series, starts, ...)` forms.

The CPU correlation loop copies only valid lags from its transform scratch
into the owned output. The GPU kernels write those lags directly at continuous
offsets. In particular, a Python/NumPy scatter from GPU block output was
measured at **216 ms** for the case below and was discarded. The GPU result
uses host-cached shared storage: GPU writes need no host copy, while NumPy
reads and in-place scaling remain practical. The buffers and GPU dispatch
records are reused across segments.

## 43-block, six-template case

Length 1,048,576; FFT length 32,768; six real 8,001-tap FIR spectra; valid
lags `[4000, 28768)`; 43 blocks. A cached plan and preallocated explicit
block output were compared against a cached plan's owned continuous output.
Eight distinct complex64 series were processed sequentially; the first was
warmup, and the table gives medians of the remaining seven. The assembly
column includes six per-template scale factors fused into the old copy. The
new path applies the same factors in place afterward. The maximum absolute
difference of the scaled results was zero in this run.

| Device | Old library call | Old assembly + scale | Continuous call | New in-place scale | Old total | New total |
|---|---:|---:|---:|---:|---:|---:|
| CPU (local host) | 11.91 ms | 3.03 ms | 10.86 ms | 1.68 ms | 14.94 ms | 12.53 ms |
| Radeon 8060S (Vulkan) | 19.81 ms | 2.90 ms | 3.83 ms | 1.51 ms | 22.70 ms | 5.34 ms |

These timings exclude plan and template setup. They are a library-level
comparison plus the caller's scale operation, not a PyCBC end-to-end run.
The PyCBC 5,000-second trigger-parity fixture still needs to be run after
its caller switches to the new method. Metal correctness and timing must be
checked by the macOS CI job; the local host has no Metal device.
