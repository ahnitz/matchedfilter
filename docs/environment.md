# Environment variables

Every environment variable matchedfilter reads, by kind. None is needed for normal use:
unset, each gives the library's default behaviour. Results never depend on a diagnostic;
the overrides change what runs (and so, for the statistical gates, which peaks a chain
dismisses), and exist for measurement and tests.

Generated from `python/matchedfilter/_config.py` by `tools/gen_environment_doc.py`; edit
the table there.

Removed 2026-10-26: block sizes, chains and the Q15 screen are one joint trial of paired
rounds; MF_TRIAL_ROUNDS sets its rounds: MF_BLOCK_TRIALS, MF_CHAIN_TRIALS.

Removed 2026-10-26: the gate chain is the cost model's, never a trial arm
(MF_CHAIN_FORCE pins one for measurement): MF_CHAIN_MARGIN.

Removed 2026-10-17: switches no tool, test or CI job used were removed (their defaults
kept): MF_BLOCK_TRIAL_RANKS, MF_CUDA_BLOCKING_SYNC, MF_CUDA_GRAPHS, MF_CUDA_PREFETCH,
MF_DIRECT_TRACE, MF_FUSE, MF_GATE16_ELECT, MF_GBLK, MF_GPU_FUSE, MF_GPU_FUSE_CACHE,
MF_GPU_FUSE_CHUNK, MF_MFTILE, MF_N1, MF_NOSTORE, MF_SERPAD, MF_SRPROD,
MF_VK_NO_SUBGROUP_PIN.

Removed 2026-10-22: a stored trial lock is final; the steady re-check it switched on
could make processes sharing a cost file choose differently: MF_TRIAL_RECHECK.

Removed 2026-10-22: stage-B blocking measured slower at every length on Zen 3, Zen 5 and
the M2: MF_BBLK.

Removed 2026-10-22: the unfused stage-A product it forced measured slower at every
length on Zen 3, Zen 5 and the M2: MF_GMAJOR.

Removed 2026-10-22: per-backend coarse layout fields; MF_COARSE_LAYOUT forces a whole
layout by name on every backend: MF_VK_COARSE_PPG, MF_VK_COARSE_TILE,
MF_VK_COARSE_SUBGROUP, MF_VK_COARSE_TWT, MF_METAL_COARSE_PPG, MF_METAL_COARSE_TILE,
MF_METAL_COARSE_TWT.

Removed 2026-10-22: renamed MF_COARSE_RAW (MF_COARSE_RAW=1 is what MF_VK_C16_BOUND=0
did, on every GPU backend): MF_VK_C16_BOUND.

Older notes in docs/ that mention a removed variable describe past studies.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `MF_DEVICE` | `cpu` | Device for plans built without one (`device.parse(None)`). |
| `MF_COST_FILE` | unset | JSON file of measured cost models and trial locks, kept between processes. Unset: cold start, no trials kept. One writer per open contest: processes sharing a file while a trial is open overwrite each other's samples (said once per contest). |
| `MF_EXECUTION_POLICY` | the shipped `execution-policy.json` | Another execution-policy table. |
| `MF_ISA` | best the CPU supports | SIMD target (also `matchedfilter.set_target`). |

## Diagnostics (output only)

| Variable | Effect |
|---|---|
| `MF_AUTOTUNE_LOG=1` | Log block-size, chain and trial decisions. |
| `MF_HMF_PROF=1` | Per-tier CPU tick counters in hierarchical plans. |
| `MF_HMF_TRACE=1` | Trace hierarchical plan runs to stderr. |
| `MF_HMF_DUMP=<file>` | Dump coarse-pass data for the GPU mirror tests. |
| `MF_GATE16_DEBUG`, `MF_GATE16_DEBUG_MAX` | FP16 gate error data for tools/gate16_error.py. |
| `MF_GPU_TIMING=1` | Device-time collection across GPU contexts. |
| `MF_GPU_PROFILE=1` | Phase timestamps in recorded Vulkan plans. |
| `MF_ROOFLINE_DATAPATH=<bits>` | SIMD datapath width for `_roofline` where detection is wrong (e.g. 256 on Strix Point). |
| `MF_VK_SUBGROUP_MEASURING` | Internal: marks the subprocess that measures Vulkan subgroup sizes. |

## Measurement overrides (change what runs)

| Variable | Default | Effect |
|---|---|---|
| `MF_AUTOTUNE=0` | on | No timed trials: the model's choices stand. |
| `MF_CHAIN_FORCE=b1,b2` or `n:b1,b2;...` | unset | Pin the gate chain (cross-device comparisons; results depend on the chain). |
| `MF_TRIAL_ROUNDS` | 5 | Paired rounds before a joint trial decides (it takes up to twice as many). |
| `MF_DIRECT_REFINE=0` | on | CPU refines by transform only (no direct correlation). |
| `MF_GATE16=0` | on where built | No FP16 first gate on the CPU. |
| `MF_DGROUP=<n>` | the plan's series group | Blocks per hierarchical series batch. |
| `MF_PBMAX=<n>` | built-in | Largest n run as pair-batched transforms. |
| `MF_ILAY=0` | 1 | Strided intermediate layout. Slower on Zen 3 and Zen 5, faster on the M2 at n >= 2^18 (4-9%); to become a measured candidate. |
| `MF_CORR_NO_STREAM=1` | off | No non-temporal stores in continuous correlation. |
| `MF_BAND_FORWARD=0/1` | measured | GPU band forward off/on. |
| `MF_COARSE_LAYOUT=<labels>` | measured | Force GPU coarse layouts by label. |
| `MF_VK_SUBGROUP=<size>` | measured | Force a Vulkan subgroup size. |
| `MF_COARSE_RAW=1` | 0 | The fp16 coarse tier reports its raw maximum instead of an upper bound (every GPU backend; the physics tests and tools/c16_sigma.py). |
| `MF_METAL_IEEE=all/none` | per kernel | IEEE math for all or no Metal kernels. |
| `MF_GPU_FUSE_INTERLEAVE=<n>` | measured | Fixed Vulkan fusion interleave depth. |
| `MF_GPU_ITEMS=0` | on | Single-template GPU jobs of a batch run one by one. |
| `MF_GPU_QUEUE_AHEAD=<n>` | 8 | GPU submissions in flight. |
| `MF_DEVICE_FOLLOWUPS=0` | on | Threshold-0 follow-ups per group rather than in one device submission. |
| `MF_SINGLE_DEVICE=bank` | auto | Keep every call on the bank's device (the pure-GPU ladder). |

## Tools, builds and tests (read outside the package)

| Variable | Default | Effect |
|---|---|---|
| `MF_SLANGC` | `slangc` on PATH | The Slang compiler tools/build_spirv.py and build_ptx.py use. |
| `MF_SLANGC_ANY_VERSION=1` | 0 | Build with a slangc other than the pinned version (experiments only). |
| `MF_NVRTC` | `libnvrtc.so.12` | NVRTC library for the PTX build. |
| `MF_CUDA_PATH` | found | CUDA installation for the PTX build. |
| `MF_TC_KAPPA` | from the measured sigma | Tensor-core coarse bound constant for tools/build_ptx.py. |
| `MF_GATE_BANK`, `MF_GATE_PROFILES` | unset | Template bank for tools/gate.py's end-to-end checks (also `--bank`). |
| `MF_CAPTURE` | unset | Directory a pycbc run captures filter calls into, for tools/hier_bench.py replays. |
| `MF_TEASER_N`, `MF_TEASER_NDATA`, `MF_TEASER_NTMPL` | 4096, 16, 512 | Shape of tools/teaser_figure.py's run. |
