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
