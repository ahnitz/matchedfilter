# Vulkan fine stage on the Radeon 8060S (gfx1151): ceilings, accounting, coarse0

All numbers are on gravity-dev2. Clocks are calibrated in place: the micro-harness runs a
fixed `v_pk_fma_f16` probe before each timed dispatch in the same command buffer and derives
the clock from it. The sysfs `pp_dpm_sclk` reading lags by tens of ms and misreported short
runs by up to 2x. The GPU was shared with other agents' runs throughout, so treat end-to-end
numbers as noisy. Micro-benchmark cycles per pair are stable to about 5%.

## 1. Measured ceilings (wave64, RADV/ACO, Mesa 25.3)

16 independent chains per thread, 40960 waves, 20000 iterations, about 2.8 GHz:

| op | wave64 instr / clk / SIMD | lane-ops / clk / CU | GFLOP/s |
|---|---|---|---|
| v_pk_fma_f16 | 0.50 | 64 (x2 halves) | 28 200 |
| v_pk_add_f16 | 0.50 | 64 (x2) | 14 400 |
| v_fma_f32 | ~0.8-1.0 | ~103-128 | 22 100 |
| v_add_f32 | ~0.8-1.0 | ~105-128 | 11 900 |

**The usable fp16 peak equals the fp32 peak, about 29 TFLOP/s at 2.9 GHz, not the
spec-sheet 59.** In wave64 a packed-fp16 instruction takes two passes on the SIMD32. An fp32
FMA uses the dual ALU and issues in one pass. Per clock, packing fp16 gives no more
arithmetic than fp32. It saves only registers, LDS and bytes. An FFT is mostly adds, so even
with zero overhead it reaches about 55-60% of FMA-counted peak. The user's 50% target is
therefore close to the ceiling for this kernel class.

Memory: LPDDR5X-8000 on a 256-bit bus gives 256 GB/s peak (not re-measured here; the
existing `tools/gpu_roofline.py` probe is Metal-only).

## 2. Fine-segment shape (one realistic segment, captured)

There are 162 hierarchical dispatches and 4.58M (block, template) pairs at n=2048. The
autotuner chose chain (256, 1024) in this capture. 54 middle dispatches (nd 463-480,
nt 131-254) carry 95.5% of the pairs. 108 edge dispatches with nd ≤ 16 carry 4.5%. Tier-1
survivors were 187k (4.1%) and refines 674.

Template counts are odd in about half the middle dispatches. The coarse kernel then fell
back from the two-pairs-per-register build (`..._c16p4t2`) to `..._c16p4`: **52% of coarse
pairs ran the slow build.**

## 3. coarse0 (band 256, packed fp16): accounting

At nd=472 and nt=254, 120k pairs:

| build | VGPR | VALU / wave | LDS | CU-cycles / pair | % of pk-fp16 peak* |
|---|---|---|---|---|---|
| shipped p4t2 | 96 | 1274 | 4 KB | 209 | 23% |
| shipped p4 (odd nt) | | | | 237 | 20% |
| **new p4t2 (any nt)** | 120 | 715 | 5 KB | **92-96** | **~51%** |

\*Nominal flops: 5N log2 N + 8N = 12.3k per pair. At the peak of 256 flops/clk/CU that is
48 CU-cycles per pair.

The binding constraint was **VALU issue**. At 2 cycles per wave64 instruction, the 1274 VALU
of the shipped build explain about 88% of its measured time. Only 472 of those instructions
were the FFT's own packed math. I measured where the rest went by deleting one part at a
time; each deletion is bit-for-bit wrong, so these builds were only timed:

| deleted | cycles / pair |
|---|---|
| nothing | 209 |
| peak election (peakLane x2) | 145 |
| + the exchange | 95 |
| + the twiddles | 82 |

### What changed (all exact; same transform and same election)

1. **Wave-level peak election (`peakTwoWave`).** Each element gets the 32-bit key
   `(fp16 |v|^2 bits << 16) | (0xFFFF - slot)`. A shuffle-xor max over the pair's lanes,
   which ACO emits as DPP max with no LDS, then elects the same winner: the largest
   magnitude, with ties going to the lowest slot. The window test uses
   `slotToIndex(tid*R + i) = slotToIndex(tid*R) | slotToIndex(i)`. One lane fetches the
   winner's (re, im) through the stage. This replaces 32 LDS round trips, each behind a
   branch. It is Vulkan only for now (`MF_VULKAN`), because Metal and CUDA keep `peakLane`
   until they are measured.
2. **Exchange addressing.** The source (row, column) of register d is affine-separable in
   (tid, d) for every band and level. `tools/coarse_layout.py` checks this at build time. A
   thread computes its base address once, and all 16 reads become LDS immediates
   (`ds_load_2addr`).
3. **Bank-conflict-free stage padding.** With the stride-16 rows, every read was an 8-way
   bank conflict. An LDS bank model in `tools/coarse_layout.py` picks `XSTRIDE`/`XSLOT` for
   each (band, PPG). For band 256 / PPG 4 the model cost drops from 576 to 64, at a cost of
   1 KB of LDS.
4. **Twiddle table.** `W_len^(lane*k2)` is correctly rounded to fp16 and stored as shader
   constant data. It replaces a cos/sin plus an fp32 recurrence with conversions (about 96
   VALU per level).
5. **Ragged tiles.** A tiled build now handles any template count. The host passes the row
   count in the unused one-bin `binsize` push slot and dispatches
   ceil(rows·ceil(nt/T)/PPG) groups. The kernel clamps tail slots and makes them write
   nothing (`NOPAIR`). This moves the 52% of pairs that ran the untiled build to the 2.5x
   faster one. Accuracy matches the previously shipped tiled build bit for bit at even nt.

Weighted over the segment mix, coarse0 cycles per pair go from about 224 to about 95, a
**2.35x speedup**. In one clean busy measurement before contention, coarse0 went from 10.0
to 7.6 ms with only the epilogue and exchange changes. Later end-to-end runs were dominated
by other jobs on the GPU (clock 1.6-2.0 GHz, phases varying 3x between runs), so I have no
clean final end-to-end number.

## 4. Not done; findings for the next pass

- **refine (n=2048, one bin), coarse1 (band 512/1024, fp32 listed):** these use the same
  `peakLane`/fp32 `exchange` structure, but WG is 128 or 64 threads, so `peakTwoWave` does
  not apply. The same three levers (affine exchange offsets, padded stride, a twiddle
  table) carry over directly to `exchange()` in the fp32 path. Survivors are a few thousand
  per segment, so occupancy is the question (refine is 120+ VGPR at WG=128).
- **forward (3.6-3.9 ms):** not yet measured against bandwidth.
- **Edge dispatches:** 108 of 162 dispatches carry 4.5% of pairs, so their cost is mostly
  fixed per-dispatch overhead. A per-block-window dispatch would need host interface
  changes.
- **listed compact1** (the coordinator's suggestion): not done.
- Coarse at bands 64/128/512/1024 gets the same code (the layout model covers every band
  and PPG), but it was only benchmarked at 256.

## 5. Second pass: refine, coarse1, forward, listed compact1

All micro-benchmarks below use the interleaved clock calibration.

**Refine and coarse1 (listed fp32 refine, one bin).** The tier-1 stage of the cascade
(`_peak_file(band1, 1)`) and the n=2048 refine both run with a single bin. Below n=4096 they
still used the general multi-bin build, which has 181 branches. Two changes:

- One-bin builds now exist for n=256..2048 (`refine_N_onebin.spv`).
- The fp32 `exchange()` reads each register at a fixed offset from a per-thread base, as
  in the coarse fix, and its stage rows are padded by 2 complex elements (`XSTRIDE_F`,
  applied only where the stage stays within 32 KB).

Outputs are bit-identical. CU-cycles per pair, 4000 survivors:

| n | shipped | one-bin | + exchange | nominal-flop % of peak |
|---|---|---|---|---|
| 512 | 939 | 677 | 557 | 11% -> 19% |
| 1024 | 1700 | 1288 | 1030 | 12% -> 21% |
| 2048 | 3590 | 2851 | 2114 | 14% -> 24% |

The rest of the gap is fp32 VALU (about 1000 VALU per wave at n=2048, two waves per pair)
plus the per-pair launch. A fp32 twiddle table would remove the recurrence's 4 VALU per
register, about 64 of roughly 1000 per level. That is an estimated 5%, and it would make the
outputs no longer bit-identical, so I did not do it.

**Forward (n=2048) is at the bandwidth ceiling.** A float4 copy probe measured 198 GB/s
(read + write), which is 77% of the 256 GB/s LPDDR5X peak. `forward_2048` moves the same
bytes at 188-205 GB/s, which is 95-103% of the copy and 73-80% of theoretical. The ≥70%
target is met. The remaining lever is fewer bytes: fuse the band pack into the forward
write, or skip writing the bins no stage reads.

**Listed compact1.** A new `compactListed` entry gates tier 1 over the tier-0 survivor list
(count in `args_tier1`), so it no longer walks all pairs. The per-dispatch `cval1` clear
(pairs × 8 B) is gone.

**Busy fine segment, alternating main 3da7bce and this branch, about 2.1-2.2 GHz, shared
GPU:**

| | main | branch |
|---|---|---|
| wall median (ms) | 24.0 / 24.3 | 22.3 / 21.5 |
| device total (ms) | 14.7 / 16.0 | 13.2 / 13.3 |
| fill | 0.6 | 0.1 |
| pack | 1.0-1.8 | 0.7 |
| forward | 3.7-3.9 | 3.3-3.5 |
| coarse0 | 4.6-4.9 | 4.5-4.9 |
| coarse1 | 1.9-3.4 | (no second tier) |
| refine | 1.1-2.4 | 4.1 |

With the cheaper refine, the autotuner now picks the single-tier chain (256,) for these
dispatches. Coarse1 disappears and the n=2048 refine takes more survivors. The device total
goes down by 1.5-2.7 ms.

## 6. Third pass: pack fusion, other bands, refine twiddle table (falsified)

**Pack phase removed.** The coarse tiers now read their band directly from the fp32 spectra
the forward wrote. Specialization constant 75 (`mfDataStride`) carries the row stride n, and
the packed coarse role rounds to half in the kernel with the same round-to-nearest-even
`packCoarse` used. The forward still writes the full spectra, so the forward pass itself
moves the same bytes; what goes away is the pack phase that re-read and re-wrote the bands
(0.7-1.2 ms a segment of pack dispatches and band copies). The outputs are bit-identical,
and coarse0 costs the same 96-97 CU-cycles per pair reading fp32 as it did reading packed
fp16, because the data slice is loaded once per group and reused across 8 pairs.

**Coarse at every band** (CU-cycles per pair; % of the pk-fp16 peak by nominal flops):

| band | 0948b24 | now | % peak |
|---|---|---|---|
| 64 | 112 (p4) | 28 (p8t2/p16t2) | 34% |
| 128 | 120 | 48-51 | 42-45% |
| 256 | 209-237 | 92-96 | 51% |
| 512 | 633 | 211-214 | 50% |
| 1024 | 932 | 475 | 49% |

Band 64 lagged because it had no tiled build and the 4-pair cap left 48 of 64 lanes idle.
It now has a TILE_T=2 build. Tiled builds fill the whole subgroup
(`subgroup_size / (band/16)` pairs). The 4-pair cap stays on the untiled builds, whose LDS
atomic election is the one that hung. The p8/p16 tiled builds pass the FDR-transfer test,
the suite and `--check cpu`, with no ring resets.

**Refine twiddle table: falsified.** A correctly rounded fp32 table (constant data,
16 × 8 B per lane) made the one-bin refine 20-28% slower: 547 → 663, 1016 → 1292 and
2112 → 2708 CU-cycles per pair at n = 512, 1024, 2048. The table loads cost more than the
single-pass fp32 recurrence they replace. Not shipped. (The fp16 table does pay in coarse0,
because there the recurrence carried fp32↔fp16 conversions and the kernel is VALU-bound.)

## 7. What should transfer to Metal and CUDA

All of these depend on queried capabilities or geometry. None is specific to gfx1151.

- **Peak election with subgroup shuffles** (`peakTwoWave`). This applies wherever the pair's
  WG ≤ subgroup size (keyed on the subgroup size the API reports, here spec constant 74).
  Apple SIMD-groups of 32 and CUDA warps qualify at bands ≤ 512.
- **Affine-separable exchange addressing** (one base per thread, immediate offsets). This is
  pure index algebra and holds on every backend. `tools/coarse_layout.py` checks it.
- **Bank padding of the exchange stage.** The model assumes 32 four-byte banks, which
  matches CUDA shared memory and AMD LDS. Apple's threadgroup memory banking differs, so
  it would need re-measuring there.
- **fp16 twiddle table for the packed coarse role.** It pays wherever the coarse kernel is
  VALU-bound with fp16↔fp32 conversions in the recurrence.
- **Ragged tiles** (any template count keeps the two-pairs-per-register build). Host
  geometry only.
- **Reading the band from the spectra** (no pack pass). A stride parameter: a function
  constant on Metal, a kernel argument on CUDA.
- **One-bin refine builds and a listed compact for tier 1.** Backend-independent.
- **Not transferable:** the measured wave64 rates (pk-fp16 is two passes, fp32 FMA is
  one). Each device needs its own probe.

## 8. Fourth pass: one dispatch per fine call, device-limit geometry, clock reference

**`hier_peaks_grouped`.** A fine call's window groups (first block, interior, last block) used
to be separate `hier_peaks` recordings: three dispatches per stage. They are now one
recording.
- Each data row's `(lo, hi)` comes from a `gRowWin` binding, read when specialization
  constant 76 (`mfRowWindows`) is set: 1 = the raw window, 2 = the window mapped onto the
  kernel's coarse band, exactly as the host maps it.
- Every stage is one dispatch over all rows.
- The recordings are ordinary hier recordings, so fused batches and SegmentPlan replay
  traces work unchanged.
- Results are bit-identical to per-group `hier_peaks` (`tests/test_vk_hier_grouped.py`).
- Pipelined ladder with `--timing`, alternating with main: fine 0.25 → 0.18 s, segment
  0.84 → 0.71 s.

**Bindings follow the module.** `_build_pipeline` reflects the SPIR-V for its highest
binding. `_descriptor_set` fills declared but unused trailing bindings with a dummy buffer,
so callers that do not use per-row windows need no change.

**Subgroup size pinned.** With `VK_EXT_subgroup_size_control` (feature queried, extension
enabled, `requiredSubgroupSizeStages` covering compute, and the size within
[min, max] = [32, 64] here), every pipeline requires the queried subgroup size. That is the
size the kernels are specialized on (constant 74), so RADV can no longer choose wave32 for
a kernel built for wave64. `MF_VK_NO_SUBGROUP_PIN=1` disables it. Wave32 as a timed
candidate (VOPD dual issue for the fp32 refine) is a possible follow-up.

**Coarse geometry from queried limits.** Pairs per group = subgroup / (band/16), bounded by
`maxComputeWorkGroupInvocations` and `maxComputeSharedMemorySize` against the padded stage
size.
- The untiled builds keep the 4-pair cap. While a geometry bug (since fixed) briefly routed
  realistic calls to untiled 8- and 16-pair builds, the whole suite lost its detections. The
  same builds are bit-correct in the micro-bench at an even template count, so the hazard is
  workload-dependent and still unexplained.
- I did not add a timed pairs-per-group choice. The measured spread between filling
  candidates is ≤ 6% (band 128: p4 51 vs p8 48; band 64: p8 28 vs p16 29 CU-cycles), which
  does not pay for a per-device timing pass.
- Bank count has no query on Vulkan (or Metal; CUDA documents 32), so the padding stays a
  build-time model parameter.

**Clock reference: already active on Vulkan.** `calibrate_costs_gpu` takes every
measurement relative to `gatechain._ClockRef` for any GPU device. Measured here:
- The reference reads 35 µs warm and 155-178 µs after 2 s idle (4.4-5x).
- Three calibrations in one process with 3 s idle between agree within about 20% per tier
  (dense[512] 3.86 / 4.59 / 4.39 ns), against the 5x raw swing.
- No change needed. The review's note predates 70cb1e2.

## 9. Fifth pass: the untiled-builds hazard explained; wave32 for small refine groups

**The "untiled 8/16-pair hazard" was a binding bug, and it hit every PPG.** I reproduced it
with a realistic-call harness: the `test_hierarchical_matrix` series, under a real (closed)
autotuned gate, with the untiled builds forced.
- **Symptom:** hierarchical found 0 of 1307 peaks at PPG 1, 4 and 8 alike. With an open gate
  everything matched, which is why the earlier checks missed it: the coarse result does not
  matter when every pair passes. With grouped dispatch disabled, the untiled builds were
  exact at every PPG.
- **Cause:** the untiled builds never called `rowWindow`, so their modules declared no
  `gRowWin` binding. The grouped host bound a buffer one past the layout, and every pair was
  gated out.
- **Fix:** every coarse build now applies per-row windows, and `_descriptor_set` refuses
  more buffers than a layout declares.
- **Tests:** `tests/test_vk_hier_grouped.py` runs the grouped equivalence test on both build
  families, and checks every untiled PPG from 1 to 16 against the tiled result under a real
  gate. Both fail on the old kernels (8 cases).

**The 4-pair cap is removed.** It was containing the binding bug, not a hang. With the
untiled 16-pair builds forced, the realistic ladder `--check cpu` is exact in batched and
pipelined mode, and about 330 back-to-back fine segments ran with no ring reset or page
fault. The original 8/16-pair hang was reported on an older kernel (before the subgroup
election, padded exchange and ragged tiles) and does not reproduce. `coarse_tile.slang`
(the barrier-UB suspect) ships no selected kernel, since `_COARSE_TILE` is empty.

**Wave32 where the group is small.** `_build_pipeline(subgroup=...)` requires any size in the
device's range and specializes constant 74 to it. `_fit_subgroup(n)` picks the smallest
required size that holds a one-pair group of n/16 invocations, so a 16- or 32-invocation
group does not idle half of a wave64. Listed one-bin refine, CU-cycles per pair (outputs
bit-identical):

| n | wave64 | wave32 |
|---|---|---|
| 256 | 481 | 385 |
| 512 | 620 | 552 |
| 1024 | 1020 | 1157 |
| 2048 | 2113 | 2266 |
| 4096 | 4400 | 4921 |

Wave32 is applied at n ≤ 512 (the tier-1 stage at bands 256/512), where it wins by 11-20%.
Larger groups stay at wave64, where wave32 loses 7-15%. This is a rule from the queried
range and the workgroup size, backed by these measurements, not a per-device timing.
