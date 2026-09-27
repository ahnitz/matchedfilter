# Coarse-stage kernel plan: instruction-level, Haswell-weighted

Target: **1.5x on the coarse stage**. The fleet measurement
(`docs/measurements/pycbc-alpha6-fleet-20260927/`) is what makes that worth
doing, and it is a bigger prize than the coarse stage has been priced at
before.

## Why the coarse stage, and how much it is worth

The fleet run puts the lower hierarchical kernel at 78-86% of the steady
search loop and its coarse pass at 81-92% of that kernel's cycles. So the
coarse pass is:

    dev1     86% x 91% = 79% of the steady search
    dev2     78% x 81% = 63%
    dev3     84% x 91% = 76%
    dev4     86% x 92% = 79%
    sugwg    83% x 90% = 74%
    haswell  84% x 90% = 76%

**70-79% on five of six hosts.** Earlier work in this repo priced coarse
changes against a ~45% share taken from synthetic operating points; the
real search escalates rarely, so refinement almost never runs and coarse
dominates far more. At a 76% share:

    coarse 1.2x -> 1.15x end to end        coarse 1.5x -> 1.34x
    coarse 1.3x -> 1.22x                   coarse 2.0x -> 1.61x

That roughly doubles the end-to-end value of every item below relative to
how they were priced before.

## What the kernel actually executes

The fleet ran band 1024 with eight taps on every lower group. `efactor(1024)`
gives 32x32, so the pair-batched coarse transform is

    pass 1:  32 x codelet_prod(32)
    pass 2:  32 x codelet_tw(32)

On AVX2 -- which is five of the six hosts, Haswell among them -- those
resolve to `fft32_prod` and `fftsr32_tw`. Disassembled from the shipped
build:

    codelet        total   loads  stores  outputs  stores/output
    fft16_prod       688     198      80       32      2.50
    fft32_prod      1591     419     170       64      2.65
    fft64_prod      3706     910     376      128      2.93
    fftsr16_tw       522     171      66       32      2.06
    fftsr32_tw      1450     438     181       64      2.82

Per 8 pairs at band 1024: 32 x (1591 + 1450) = **97,312 instructions, or
12,164 per pair**.

### The binding constraint is the front end, not a port

For one (pass1 + pass2) call pair, 3041 instructions, on Haswell:

    front end   4 uops/cycle                  760 cycles   <-- BINDING
    port 1      vaddps, 1/cycle               684 cycles
    ports 0+1   vmulps/vfma, 2/cycle          172 cycles
    load        2/cycle                       428 cycles
    store       1/cycle                       351 cycles

Two things follow, and they set the whole strategy.

**1. Cut instructions, not port pressure.** The kernel is issue-bound.
Rebalancing work across ports buys nothing until the instruction count comes
down.

**2. Port 1 is only 76 cycles behind the front end.** Haswell issues
`vaddps` on port 1 alone (Skylake later added port 0), and these codelets
are 68% adds -- 684 of 1006 arithmetic ops. Any change that cuts total
instructions without cutting adds will hit the port-1 wall almost
immediately. **On Haswell the two limits must be attacked together.** That
is a Haswell-specific hazard: on every other host in the table FP add issues
on two ports and this does not arise.

### Where the instructions go: spilling

`stores/output` should be 1.0 for a register-resident split-radix codelet
and 2.0 for a two-pass Stockham one that stages through scratch. Measured,
every AVX2 codelet is well above its floor:

    fftsr32_tw   181 stores for 64 outputs, floor 64    -> ~117 spill stores
    fft32_prod   170 stores for 64 outputs, floor 128   ->  ~42 spill stores
    fftsr32_tw   438 loads; inputs + twiddles ~126      -> ~312 reloads

A size-m complex codelet holds 2m vectors live at its peak. At m=32 that is
64 YMM registers and **Haswell has 16**. The DAG cannot fit, by a factor of
four, so the compiler spills. Excess memory traffic is about **23% of all
instructions** in the two codelets.

This is already known here for m=64 -- `codelet()` gates `fftsr64` to
AP_W >= 16 because "AVX2 has 16 ymm and it spills catastrophically" -- but
the same arithmetic says m=32 and m=16 spill too, just less. Nothing has
acted on that.

## The plan

Four items, ordered by measured value per unit of risk. Each states what it
is worth and how to falsify it.

### 1. Confirm band 1024 reaches the pair-batched path (free, do first)

`pairbatch_size()` caps the pair path at N <= 128 by default, so band 1024
reaches it only through `allow_pair_alt`, the adaptive alternate added in
`d2735f7`, which requires `ntmpl >= 16` and an x86 target. The fleet ran
6,519,377 pair-calls across 143,876 filter blocks -- about 45 pairs a block
-- and 68 lower groups.

**Check whether the alternate actually fires at the real batch shape.** The
pair-batched path measured 1.61x faster than the balanced split at band 1024
(nd=8, nt=64) in this repo's own A/B. If the real search is falling back to
the balanced path, that 1.61x is available with no new code, and every item
below should be measured on top of it rather than instead of it.

Cost: an hour with `MF_HMF_PROF` and a pinned run. Falsified if the profile
shows the pair path already in use.

### 2. Q15 int16 coarse transform (the main lever, ~1.3-1.5x)

Two separate wins on Haswell, and they attack both limits from the previous
section at once.

**Instruction count.** AVX2 holds 16 int16 lanes against 8 float lanes, so
the same pair count needs half the vector operations. Against the measured
mix (341 adds, ~40 complex multiplies per `fft32_prod`):

    float32   499 ops for  8 pairs = 62.4 ops/pair
    Q15       341 adds + 40 x 6 = 581 ops for 16 pairs = 36.3 ops/pair

about **1.7x fewer instructions per pair**. Complex multiply is worse in
Q15 -- 6 ops (2 `vpmulhrsw` + 1 add/sub per component) against 4 with FMA --
but the codelets are add-dominated, so the add saving dominates.

**Port pressure.** `vpaddw` issues on ports 1 and 5 on Haswell, 2/cycle,
against `vpaddps` at 1/cycle on port 1 alone. Combined with 16 lanes that is
**4x the add throughput**, which is exactly the constraint sitting 76 cycles
behind the front end.

Do not expect the full 1.7x. This repo's own width test -- vary `AP_CAP`
alone within one ISA -- found the last doubling of lanes bought 1.24-1.51x
on the pair-batched path, not 2x, because roughly half the kernel does not
scale with lane count. **Budget 1.3-1.5x and measure.**

Precision is settled and is not the blocker: `tools/coarse_precision.py`
puts int16 at 0.01% low on captured pycbc pairs with every butterfly
rounded, against threshold headroom of about 4%. That was measured against
the old table and should be re-confirmed against `gatemodel.py`, but the
margin is three orders of magnitude and will not vanish.

Scope: a Q15 codelet family in `gen.py` (the generator makes this tractable
-- it already emits four variants), a per-stage scaling policy, and a scan
widened to int32. `vpmaddwd` computes `re*re + im*im` in one instruction,
so the magnitude is nearly free.

### 3. Stop the spilling (~1.2-1.3x, and it compounds with Q15)

The m=32 DAG needs 64 live vectors and Haswell has 16. Two routes:

**(a) Smaller codelets on narrow targets.** Add a three-level element
transform so 1024 decomposes as 32x32 into smaller pieces, or choose the
outer split so AVX2 lands on m=8/m=16 where the live set is 16-32 vectors
rather than 64. `esupported`/`efactor` are two-level today; this is the
structural change.

**(b) Explicit memory-staged small-radix passes on AVX2.** A radix-4
butterfly holds 8 vectors live and always fits. More explicit memory
traffic, but spilling *is* memory traffic -- chosen by the register
allocator, to the stack, without the layout control a staged pass has.

(a) is cleaner and reuses the existing codelet machinery. (b) is the
classic answer and is more predictable on a 16-register machine. Prototype
(a) first; it is a change to `efactor` plus a third loop level.

Note this is a **narrow-target** change. dev2 at AP_W=16 holds 64 vectors
in 32 ZMM -- still over, but by 2x rather than 4x -- and measured
`fftsr32_prod` 1.075x FASTER than the Stockham form, which is why m=32/64
split-radix is gated to AP_W >= 16 today. Do not regress that gate.

### 4. Haswell port-1 relief, only after 2 and 3 (~1.1x, conditional)

Once the instruction count comes down, port 1 becomes binding at 684
cycles. An `a + b` can be issued as `fmadd(a, 1.0, b)`, which runs on ports
0 and 1. Balancing the two ports moves the arithmetic bound from 684 to
about 250 cycles.

It costs one register for the 1.0 and raises latency from 3 to 5 cycles, so
it pays only where there is enough independent work to hide it -- which
these codelets have, being 8 lanes wide across many independent butterflies.

**Haswell-only.** Skylake and later, Zen 2 and later all issue FP add on two
ports, so this is dead weight or a small loss elsewhere. Gate it on the
target, and measure on dev1 (Zen 3) and dev4 (Raptor Lake) before shipping
to confirm it is neutral there.

## Adding up to 1.5x

    item                         coarse        confidence
    1. pair path at band 1024    1.0 or 1.6x   measured A/B, applicability unverified
    2. Q15 int16                 1.3-1.5x      width test bounds it; precision settled
    3. spill removal             1.2-1.3x      arithmetic from register counts
    4. port-1 relief             1.0-1.1x      Haswell only, conditional on 2 and 3

2 and 3 overlap -- Q15 halves the spill traffic as well -- so they do not
multiply. **2 and 3 together should reach 1.5x on the coarse stage, which is
1.34x end to end at a 76% share.** Item 1, if it applies, is additional and
comes first because it is free.

## How to measure it

  * Interleave A/B in one build. This machine drifts 18% between runs, and a
    sequential sweep once put a 5.4% change at 11.8%.
  * Quote no spread without its noise floor: `audit_threshold.py --repeat N`
    gives 1.0-1.3% for the bisection; a kernel A/B wants the same treatment.
  * Escalation-rate measurements need PURE NOISE data. A signal in every
    block escalates everything and reads 90-100% at any threshold.
  * Ablations must be compile-time. A plan-field branch in the hot loop
    measures its own branch -- an ablation of the corner turn came out
    SLOWER than the real thing until it was moved to `#if`.
  * Haswell and dev2 are the two hosts that matter for generalisation: they
    bracket the register file (16 vs 32) and the FP-add port count (1 vs 2).
    dev2 is the fleet's only full-rate AVX-512 host.
