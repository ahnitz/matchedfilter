# Cross-platform review: what is common, what transfers, what to unify

Reviewed at main c28daf1 (2026-10-09). This covers the Vulkan kernel pass 2 (one-bin builds below
n=4096, padded fp32 exchange, listed compact1) and the x86 Q15 screen pricing.

Branches read: `parity/cuda`, `parity/cuda-warp`, `parity/cuda-feed`, `parity/metal`,
`cpu/x86-gate`. Implemented pieces are on `review/unify`; see §8.

The organising question for every row is what the API can tell us. A technique generalises
across hardware when the property that decides it can be queried at run time. It stays
per-machine when it is keyed on a vendor id, a device name, or a constant someone measured on one
box.

## 1. Technique x backend matrix

Key:
- **Y**: has it.
- **A**: applicable but missing.
- **N/A**: not applicable (the reason follows).
- **?**: unknown, needs a measurement.

| Technique | Vulkan (8060S) | CUDA (L40S) | Metal (M2) | CPU | Deciding property (queryable?) |
|---|---|---|---|---|---|
| fp16 coarse inputs (`pack_half2`) | Y | Y | Y | Y (NEON fp16 gate) / A (x86: Q15 instead) | VK `shaderFloat16` (`VkPhysicalDeviceShaderFloat16Int8Features`); CUDA cc>=5.3; Metal always; CPU Highway `HWY_HAVE_FLOAT16` |
| fp16 twiddle table | Y | A | A | N/A (exact codelets) | same as above; benefit depends on LDS/constant bandwidth versus ALU |
| Wave-level peak election (shuffle, `WaveActiveMax/Min`) | Y | A (the warp coarse gate exists, not merged) | A (falsified once as a SIMD-group *barrier*, not a shuffle; see §2) | N/A | subgroup size and supported ops: VK `VkPhysicalDeviceSubgroupProperties.supportedOperations` & ARITHMETIC/BALLOT; CUDA warpSize; Metal `threadExecutionWidth` |
| Pairs-per-group packing to fill a wave | Y (queried subgroup) | Y (timed candidates) | Y (constant 32) | N/A | subgroup size; max workgroup invocations |
| Fixed-offset exchange addressing | Y | ? (CUDA copy of tierb predates it) | ? | N/A | none; this is a pure code transformation, so port it via the shared Slang source |
| Bank-conflict padding from a build-time bank model | Y (wave64, 32 banks x 4 B) | A | A | N/A | bank count/width: not exposed by VK/Metal; CUDA 32x4 B fixed. Key the model on subgroup size and arch keys, not the device name |
| Padded fp32 exchange (pass 2) | Y | A | A | N/A | same bank model |
| One-bin builds | Y (n<4096, pass 2) | Y (`one_bin` in the PTX manifest) | Y (n=256-1024) | N/A | threshold range is a cost-model choice; keep every one-bin build as a candidate |
| Ragged tiles (TILE_T, clamped last tile) | Y | A (needs `nt % TILE_T == 0`, else pads) | A | N/A | none: exactness is structural |
| Listed compact1 (indirect dispatch of survivors) | Y (pass 2) | Y (`compactPeaks`) | A | Y (pooled refine) | VK indirect dispatch (core); Metal `dispatchThreadgroupsWithIndirectBuffer` (core) |
| Sparse survivor readback (`_SparsePeaks`) | Y | Y | Y | Y | none |
| `peaks_items` (one submission for many series) | Y | Y | Y | N/A | none |
| Fused batches / CUDA graphs (record once, replay) | Y (fused recordings) | Y (graphs) | A (MTLIndirectCommandBuffer) | N/A | Metal `supportsFamily(MTLGPUFamilyApple3+)` for ICB compute |
| Device-side zeroing | Y | Y (memsetAsync) | Y (blit fill) | N/A | none |
| `wait=False` / async completion | Y (fence) | Y (events) | Y (command-buffer completion) | N/A | none |
| In-place row views (descriptor offset) | Y | Y (pointer offset) | A | N/A | **VK `minStorageBufferOffsetAlignment`** (now queried, §4); Metal `setBuffer:offset:` needs 4 B (256 B for constant buffers on macOS) |
| Forced unrolls / no local arrays | Y (Slang SPIR-V) | Y (CUDA copy) | ? (MSL from the same Slang, never checked for spills) | N/A | register file per thread: CUDA `CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_BLOCK`; VK/Metal: not exposed, read from compiler stats |
| Clock-reference calibration (`_ClockRef`) | A | A | Y | N/A (CPU uses steady clocks) | any GPU with DVFS: all three. See [GPU idle-latency trap] and [APU shared power] |
| Span-sized calibration | A | A | Y | Y | none |
| Coarse variant chosen by timing | partial (PPG from rule, tile from table) | Y | partial (PPG rule) | Y (chain trials) | none, it is a measurement |
| Narrow first tier with float re-check | fp16 coarse (no host-side error bound) | same | same | Q15 screen (x86), fp16 gate (NEON) | see §6 |

## 2. Transfers, with expected benefit and the deciding property

1. **Wave-shuffle peak election to Metal and CUDA.** On Vulkan it replaced a
   shared-memory atomic max per lane with one `WaveActiveMax` + `WaveActiveMin` per wave.
   - The Metal failure was a `simdgroup_barrier`, which is a different primitive (it orders
     memory; it does not reduce). `simd_max`/`simd_min` are the direct equivalents and need no
     barrier at all.
   - The CUDA warp gate regressed end to end because it shifted the chain choice, not because
     the kernel was slower. That is an autotune and cost-model problem: re-price the chain, do
     not drop the kernel.
   - Expected benefit: the peak tail of the coarse kernel, ~5-15% of coarse0 on Vulkan.
   - Deciding property: subgroup size >= threads per pair (`WG <= mfSubgroupSize`, already a
     specialization constant in `tierb.slang`) and support for subgroup arithmetic ops.
2. **Fixed-offset exchange + bank-model padding + padded fp32 exchange to the CUDA and Metal
   copies.** These are pure index transformations in `tierb.slang`.
   - Because Metal is compiled from the same Slang (`build_spirv.py` emits `-target metal`),
     Metal already inherits them where it uses the shared source. Recheck its build list.
   - CUDA uses a forked copy (forced unrolls). It inherits nothing until the fork is folded
     back (§3.3).
   - Deciding property: bank geometry. NVIDIA and Apple are 32 banks x 4 B; RDNA is 32 x 4 B
     per half-wave on wave64. Make the bank model a function of (subgroup size, banks=32),
     not of the device.
3. **Ragged tiles to CUDA and Metal.** On Vulkan, odd template counts went to the untiled build:
   52% of coarse pairs at 2.5x the cycles. CUDA pads to whole groups instead. Padding is correct
   but costs up to `PPG*TILE_T - 1` wasted pairs per row.
   - Expected benefit: largest at small nt (follow-ups, asym).
   - Deciding property: none (structural, exact).
4. **Clock-reference calibration from Metal to Vulkan and CUDA.** The memory notes on the GPU
   idle-latency trap and the APU shared power cap show the Radeon at 600 MHz versus 2.9 GHz.
   Calibration on Vulkan currently prices a cold clock.
   - `_ClockRef` lives in `gatechain` and is backend-neutral already. It only needs the
     backends to call it.
   - Deciding property: DVFS, which is all of them.
5. **CUDA graphs ↔ Vulkan fused recordings ↔ Metal ICB.** These are the same idea: record once,
   replay with new offsets.
   - Metal is the one backend without it. Its host Python is a smaller share of the time (the
     device is 94% busy), so the expected benefit is low there.
   - Recommendation: keep it as a candidate only.
6. **Listed compact1 to Metal.** This removes the cval1 dense fill and its readback.
   - Metal has `compact_*.metal` for tier 0 only.
   - Deciding property: indirect dispatch, which is core on every API.
7. **fp16 twiddles to CUDA and Metal.** This helps only where the twiddle load is an LDS or
   constant-cache cost.
   - The cost model, not a vendor list, should decide it. Build both variants and let the
     timing choice (CUDA already does this) pick.

## 3. Duplicated code and unification proposals

Measured by AST over the three `_*compute.py` files (3008 + 1919 + 1603 lines):

| Function | Vulkan | CUDA | Metal | State |
|---|---|---|---|---|
| `_sparse_from_dense`, `_sparsified` | Y | - | Y | identical: **moved to `_shared` (commit 2)** |
| `_pack_half2` | Y | Y (slower, same bits) | Y | **moved to `_shared` (commit 2)** |
| `_manifest` | Y | Y | Y | CUDA = Metal; Vulkan adds a path. Can share with a `dir` argument |
| `_radix`, `_use_c16`, `_shift` | Y | Y | Y | each a slightly different table. The radix table belongs in the build manifest |
| `_coarse_span`, `_full_tile`, `_tierc_tile`, `_forward_tierc`, `_peaks` | Y | Y | Y | same algorithm, different launch calls |
| `hier_peaks` (142/124/132 lines) | Y | Y | Y | the largest duplicate: plan, pack, coarse, compact, refine, readback |
| `peaks_items` (85/52/40), `peaks_grouped`, `zero_columns(_done)`, `correlate_continuous`, `forward`, `clear_cache`, `_evict_record` | Y | Y | Y | same protocol, three hand-written copies |

### 3.1 A host layer over a minimal backend interface

The proposal is `_gpuhost.py`. Each backend implements only these primitives:
- `alloc`;
- `upload`;
- `pipeline(stem, spec)` -> handle with `.threads`;
- `launch(handle, groups, buffers, push, offsets)`;
- `launch_indirect`;
- `fill`;
- `copy`;
- `submit(wait)` -> pending;
- `timestamp`.

The shared layer then owns these once:
- the `hier_peaks` sequence;
- the `peaks_items` protocol (item packing at `storage_offset_alignment`, one submission, sparse
  results);
- sparse/zeroing conventions (sparse callers skip the dense clear on every backend);
- tier-C tiling;
- eviction.

Backends keep their recording and replay mechanism (fused recordings, graphs, ICB) behind
`submit`.

Expected result:
- ~1500 fewer lines;
- one place for the bugs fixed tonight (the cache-key and use-after-free classes recur per
  backend).

This is a large refactor that touches the CUDA agent's active host path. Leave it as a proposal
and do it after `parity/cuda-*` merges.

### 3.2 One dispatch-geometry policy keyed on queried limits

Today the coarse pairs-per-group policy differs per backend:
- **Vulkan:** `subgroup_size // (band/16)`, capped at 4 by a hard-coded hang workaround.
- **Metal:** a fixed `TARGET_THREADS = 32`.
- **CUDA:** times `ppg in 1..16`, under a fixed `band//16*ppg <= 1024`.

Replace the three with `coarse_candidates(band, limits, shipped)`:
- it takes `limits = DeviceLimits(subgroup, max_threads, max_shared, offset_align, regs_per_block)`;
- it returns every shipped (ppg, tile) that fits the limits;
- the choice is the CUDA rule, by timing, with the subgroup-filling one as the prior.

`coarse_launch` (Vulkan, l.67) is already backend-neutral; move it into the same module.

### 3.3 Shared Slang modules with capability-driven specialization

`tierb.slang` is compiled to SPIR-V and Metal. CUDA keeps a fork (`coarse_warp.cu` and the
unrolled copy) because of the 288 B/thread local arrays.

The unrolls are expressible in Slang (`[ForceUnroll]`). Fold them back so CUDA builds
`-target ptx` from the same file. CUDA then inherits the exchange and padding work.

Turn the remaining per-target `#if` choices into specialization constants or `-D` driven by a
capability record emitted at build time:
- `MF_VULKAN`;
- the subgroup size;
- the bank count;
- `HAS_SUBGROUP_ARITH`;
- `HAS_FP16`.

Keep one manifest schema across `spirv/`, `metal/` and `ptx/`: today `build_ptx.py` and
`build_spirv.py` write similar but not identical manifests.

## 4. Hard-coded device constants that should be API queries

| Constant (where) | Assumes | Vulkan query | Metal query | CUDA query |
|---|---|---|---|---|
| 256 B item/group offsets, `shared_view(align=256)` (`_vkcompute` items/grouped, `_shared`) | AMD's max | `VkPhysicalDeviceLimits.minStorageBufferOffsetAlignment` (**done, commit 1**; RADV reports 4) | 4 B for device buffers | 256 B `cudaMalloc` base, else none |
| Subgroup fallback `32` when Properties2 is missing | wave32 | `VkPhysicalDeviceSubgroupProperties.subgroupSize`; on RDNA also `VkPhysicalDeviceSubgroupSizeControlProperties.{min,max}SubgroupSize` + `requiredSubgroupSize` at pipeline creation. RADV may run compute at wave32 or wave64, so pin it, since the kernels assume it | `[pso threadExecutionWidth]` | `CU_DEVICE_ATTRIBUTE_WARP_SIZE` (10; defined in `_cuda.py`, never read) |
| Metal `TARGET_THREADS = 32` (`_mtlcompute` l.121) | Apple SIMD width | - | `threadExecutionWidth` of the coarse PSO | - |
| CUDA register cap `65536 // wg` (`_cudacompute` l.730) | 64K regs/block | - | - | `CU_DEVICE_ATTRIBUTE_MAX_REGISTERS_PER_BLOCK` (12) |
| CUDA `band//16*ppg > 1024` (l.1312) | 1024 threads/block | `maxComputeWorkGroupInvocations` (already read) and `maxComputeWorkGroupSize[0]` (**now read, commit 1**) | `maxTotalThreadsPerThreadgroup` (already read per PSO) | `CU_DEVICE_ATTRIBUTE_MAX_THREADS_PER_BLOCK` (1; defined, never read) |
| CUDA shared memory per block | 48 KB default | `maxComputeSharedMemorySize` (read) | `maxThreadgroupMemoryLength` (read) | `CU_DEVICE_ATTRIBUTE_MAX_SHARED_MEMORY_PER_BLOCK_OPTIN` (97) + `cuFuncSetAttribute(MAX_DYNAMIC_SHARED_SIZE_BYTES)` |
| Vulkan fill/clear kernels `numthreads(256)` and `(x+255)//256` (l.1470-1679) | 256 fits | fine everywhere (min guaranteed 128 invocations, so 256 can fail on minimal devices); derive from `maxComputeWorkGroupInvocations` / subgroup multiple | ok | ok |
| `_accurate_trig = vendorID == 0x8086` | Intel trig is inaccurate | no query; the honest fix is a build-time accuracy self-test at context creation (one FFT against float64) that selects the accurate twiddles | same | N/A |
| Vulkan coarse PPG cap 4 ("8/16 hung gfx1151") | one driver's hang | none. Keep the cap only where reproduced, keyed on arch key `gfx1151`, with a test that retries | - | - |
| Metal page size 16 KiB for no-copy buffers | Apple silicon | - | `getpagesize()` / `vm_page_size` | - |
| Unified-memory assumptions (host-visible staging) | APU / Apple | `VkMemoryPropertyFlags` DEVICE_LOCAL\|HOST_VISIBLE on one heap (`mem_props` is read; use it to pick zero-copy versus staging) | `hasUnifiedMemory` | `CU_DEVICE_ATTRIBUTE_INTEGRATED` (18) / `CAN_MAP_HOST_MEMORY` |
| Queue count (single compute queue used) | one queue | `VkQueueFamilyProperties.queueCount` (`queues` exists; overlap transfer with compute on a second queue/transfer family) | one queue, multiple command buffers | streams (already used) |
| fp16 arithmetic | always | `shaderFloat16` + `storageBuffer16BitAccess` (not checked; `pack_half2` avoids the storage feature, but the arithmetic still needs `shaderFloat16`) | always | cc >= 5.3 (major/minor read) |

## 5. Dead code and disabled paths

- **`_vkcompute._COARSE_TILE = {}`.** This is kept "so the selection point stays visible". It is
  dead. Delete the dict and its lookup. The `coarse_N.spv`/`coarse_N.metal` fp32 tiled kernels
  it selected are shipped but unused (`metal/coarse_{256,512,1024}.metal` are still in the
  package).
- **Vulkan tiled coarse "built and validated for 512 and 1024, deliberately not selected"** (the
  comment block at l.93). This is a hard-coded exclusion. Make it a timed candidate like CUDA's.
- **Vulkan PPG cap of 4 (`MF_VK_COARSE_PPG`).** This is a disabled path justified by a hang.
  Either reproduce the hang and fix it (a likely suspect is the shared-memory size at PPG 8/16
  over `max_shared_memory`, which is now checkable) or key the exclusion on `gfx1151`
  explicitly.
- **`MF_SEGMENT_REPLAY` (off by default, parked) and `MF_REPLAY_DEBUG`.** This is a parked
  feature with its own code path in all backends.
- **`_cuda.py` attribute constants WARP_SIZE / MAX_THREADS / MAX_SHARED.** They are defined and
  never queried.
- **CUDA `_pack_half2` slow copy.** Removed (commit 2).
- **`MF_GATE16=0` and the Q15 autotune.** These are live switches, not dead code. They are kept
  as measured candidates.
- **Non-c16 coarse branches and `fused=`.** These were listed as dead in `gpu-parity-plan.md`
  §8 and are still present.
- **Unmerged `parity/cuda-warp`.** This should go back through chain re-pricing, not be deleted
  (§2.1).

## 6. The two CPU narrow-gate designs

| | x86 Q15 screen (`q15-inl.h`) | NEON fp16 gate (`gate16.cc`) |
|---|---|---|
| Arithmetic | int16 Q15, saturating; 2x float lanes | fp16 FMA; 2x float lanes |
| Scaling | block/template quantisation so `|d||t|/2^15 + 1.5N <= 30000` (deterministic overflow bound) | power-of-two scale, max component < 1 (deterministic overflow bound) |
| Dismissal margin | **statistical**: 5 sqrt(N) Q = ~10.7 rms, from a measured rms of 0.46 sqrt(N) | **half proven**: lag choice (1+3u) proven; transform error kappa·u·rms(y), kappa = 16, measured tail |
| Recheck | float tier re-runs survivors | float refine of survivors; the chosen lag value is re-read in fp32 |
| Selection | autotune alternation per (n, snr, fd, chain); priced in the cost model by `excess` (c28daf1) | `MF_GATE16`, plus the gate kind in the cost-cache keys |
| Tests | no float-passing pair rejected; bit-identical hierarchical results | the bound against a float reference, including loud transients |

Both are a screen with a float recheck, and both make the same kind of claim: survivors are a
superset of the float gate's, except with a measured tail probability. Neither is fully proven:
- Q15's rms model assumes independent roundings;
- fp16's kappa term is fitted to a tail.

The fp16 design has one thing Q15 lacks: it separates the peak-proportional error (proven) from
the noise-proportional error (measured). That is exactly what defends against the "loud
transient" case. The fp16 doc measured e = -15.1 for loud transients when the peak term was
omitted. Q15 has no peak-proportional term, and its Q15 rounding of a loud peak is proportional
to the peak. Measure the Q15 screen on the gate16 loud-transient inputs before trusting it on
glitches.

**Recommendation: one validation approach for both, and for the GPU c16 coarse.**
1. Write the margin as `proven(peak) + k * modeled_rms(N, scale)`, where k is derived and not
   swept. Keep any fitted constant explicit and named.
2. Use one shared harness (generalise `tools/gate16_error.py`) that reports max(error / margin)
   over:
   - ladder-profile noise;
   - injections;
   - loud transients/glitches;
   - adversarial near-full-scale inputs.

   Report it per N, per backend, with the pass criterion max < 0.5 (2x headroom).
3. Keep the existing exactness test: no float-passing pair dismissed, bit-identical
   hierarchical output.
4. Select by the cost model with the screen's measured excess (the Q15 pricing on main). Do not
   use an env switch. Give the fp16 gate the same `excess` pricing, so the CPU chain choice
   treats both uniformly.

The GPU fp16 coarse (`c16`) has no host-side error margin today. It relies on the refine chain's
slack. It is the third instance of the same lever and should go through the same harness.

### 6.1 The harness: `tools/gate_margin.py` (first results, 2026-10-09, 8060S + Zen 5)

The harness works from each gate's pass/reject decisions only, so one method covers the CPU
screen and the GPU kernel.
- Every pair's exact float64 maximum is scaled to K.
- A threshold grid thr = K(1 + delta) is swept, with delta = 0 on the grid.
- **slack** = thr_max/ref - 1, where thr_max is the largest grid threshold at which the pair
  still passes. A negative slack is a dismissal the gate added.
- **margin use** applies where the gate exposes its statistic s. It is
  (ref - s)/(thr_max - s), and the criterion is < 0.5.
- The families are noise, profile-shaped, injection, loud transient, and full scale
  (K = 3e4).
- `--loud` adds an end-to-end CPU-versus-GPU check with one loud injection.

Results:
- **x86 Q15 screen** (N = 128-1024, 256 pairs per family per N): 0 dismissals; minimum slack
  +0.1% to +2.5%.
  - The largest margin use is **0.49**, on the loud transient at N=128; 0.47 at N=256.
    Elsewhere it is 0.32-0.45.
  - The statistical margin holds, but the transient family sits at the 2x-headroom line, as §6
    predicted. Do not lower the 5 sqrt(N) margin.
- **GPU first tier through `hier_peaks`, ordinary scale** (N = 128-1024): about 55-65% of
  pairs whose exact maximum equals the threshold are rejected. The gate value sits up to 0.14%
  below the exact one, with no margin.
  - This is a symmetric-error gate. The effective threshold rises by up to ~0.14%, an
    unbudgeted but small change to the false-dismissal rate.
  - Fix: lower the tier's raw threshold by a derived bound (the NEON gate's (1 + 3u) +
    kappa u rms form), or fail open by ~2 ulp of fp16.
- **GPU at large coarse values: a correctness bug, not a margin question.**
  - The gate grid rejects every pair once the coarse maximum is above ~1e3 (100 passes, 1000
    fails), at every band 128-1024.
  - End to end (`--loud`, HierarchicalFilter at n=4096, threshold 6 sigma), one injection
    at SNR >= 2500 makes the GPU return **0 peaks for the whole batch**, against 62 on the
    CPU. At SNR 2000 the two agree.
  - It also fails with `chain=(2048,)`, which is an fp32 coarse tier, so the cause is not
    only fp16 coarse inputs.
  - Loud glitches at these SNRs occur in detector data. Every other trigger in the same call
    is lost with them.
  - Owner: the Vulkan kernel track (compaction, peak packing, or refine value range). CUDA
    and Metal should run `python tools/gate_margin.py --gate gpu-c16 --loud` once their
    adapter exists (the GPU adapter currently drives `_vkcompute`).

## 7. Top recommendations (impact x breadth)

1. **Shared host layer (`_gpuhost`) over a primitive backend interface** (§3.1). Every bug class
   fixed this week (cache keys, use-after-free, sparse/zeroing, row views) was fixed per
   backend. The layer halves the GPU host code. All GPU backends benefit.
2. **One Slang source for all three GPU targets with capability specialization** (§3.3). Fold
   the CUDA fork back. Every Vulkan kernel win (exchange, padding, wave election, ragged tiles,
   listed compact1) then reaches CUDA and Metal by rebuild.
3. **DeviceLimits record + one geometry policy keyed on it** (§3.2, §4). Remove
   `TARGET_THREADS`, the 65536 register and 1024 thread assumptions, and the 256 B alignment
   (done). Pin the RDNA subgroup size with `requiredSubgroupSize`.
4. **Clock-reference calibration on Vulkan and CUDA** (§2.4). The APU's clock swings 5x under
   load. The cost model prices cold clocks there today. The code exists in `gatechain`.
5. **One narrow-gate validation harness and the cost-model `excess` pricing for Q15, NEON fp16
   and GPU c16** (§6). This removes `MF_GATE16`, makes all three first tiers comparable, and
   closes the loud-transient gap in Q15.

## 8. Commits on `review/unify`

1. `vulkan: query minStorageBufferOffsetAlignment and maxComputeWorkGroupSize`.
   - Item and grouped sub-result offsets, and `shared_view`'s default alignment, now come from
     the device instead of an assumed 256 B. RADV on the 8060S reports 4, so results pack
     densely.
   - `max_workgroup_size` is exposed for the geometry policy.
   - Validation: `ladder --check cpu` exact (0/0 one-sided) on both `--pure` and `--pipeline`;
     full suite green.
2. `gpu: share pack_half2 and the sparse-result helpers across backends`.
   - This removes three copies of `_pack_half2` (the CUDA one bit-identical but slower) and two
     copies of `_sparse_from_dense`/`_sparsified`.
