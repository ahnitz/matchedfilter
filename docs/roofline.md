# Fraction of theoretical throughput (the roofline report)

`tools/search_bench.py --roofline` and `tools/ladder.py --roofline` report how close a run
comes to what the hardware could do at most:

    fraction = roofline time / measured wall time

The roofline time is the sum over stages of max(flops / peak flops at the stage's precision,
bytes / peak bandwidth). The model is `python/matchedfilter/_roofline.py` (its docstring has
every rule); `group_work` holds the fine stage's arithmetic and `tests/test_roofline.py`
pins it on recorded counts. The same model is applied to every device, so a CPU fraction and
a GPU fraction can be compared.

## What is counted

The counts are what the run did, read from the engine's own counters, not modelled:

- **root** (a hierarchical search): per block and channel, the band product and one real
  inverse of length n (6 flops a band bin + 2.5 n log2 n); bytes are the band of the block's
  spectrum and of the root's (its inputs) and the n-sample real series (4 n B). The series is
  the stage's result, which the middle stage reads, charged as the middle's own output is;
  the intermediate half-length spectrum is not (rule 2).
- **middle**: one transform per block, one product and inverse per (block, template) pair;
  bytes are the input windows, template spectra and requested output.
- **forward**: one transform per fine block; bytes are the block's input only.
- **tier i**: each coarse tier at its band, on what the engine ran it on. Tier 0 runs over
  every block against the templates, or against the **shared screeners** where it uses them,
  so its pairs are blocks x screeners. A later tier runs on the previous tier's survivors, or
  on the (block, sub-screener) pairs the CPU's tier-1 sub-screeners map them to.
- **refine**: one full-length pair per survivor of the last tier.
- **followups**: one transform and one full pair per block of each single-template call.

## Assumptions

1. **The Q15 screen is tier 0.** Where the CPU runs its int16 screen, the screen is the first
   tier's gate (no float pass of that tier follows, `src/hmf.c`). It is one int16 stage on
   tier 0's inputs.
2. **Transform outputs are not charged.** A transform's output spectrum (middle, forward,
   follow-ups) can be read where it is made: the CPU's fused path keeps it in cache. Writing
   it out is not minimum traffic, so a device that writes it pays for that in measured time,
   not in the roofline.
3. **One flop convention.** Every length-n transform is charged 5 n log2 n, and every pair
   6 n + 5 n log2 n + 3 n, whatever algorithm and precision computes it. The Q15 screen's
   split-radix four-step does fewer operations than that; the convention is kept identical on
   every device rather than tuned per kernel.
4. **Precision as executed.** A stage is compared with the peak of the precision it runs in:
   int16 for the Q15 screen, fp16 for a packed half-precision tier, else fp32.
5. **Theoretical peaks.** Peaks come from the device's own properties and a stated formula
   (`_peaks`). The one measured peak is a CPU core's streaming bandwidth (one core cannot
   reach the socket's). A peak that cannot be derived is reported unknown: the stage's time
   and the fraction are then NaN, and the report prints `ROOFLINE INCOMPLETE`. A missing
   peak never decides a stage's bound.
6. **Implementation work is not roofline work.** Zeroing, padding, packing, host work and
   fills appear only as measured time.

The fraction can still exceed 100% where a stage does less work than the convention
charges, for example a transform algorithm cheaper than 5 n log2 n. That is a property of
the convention, and it is the same on every device.
