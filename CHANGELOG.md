# Changelog

Alpha releases may change the API. Pin a version for reproducible work.

## Unreleased

### Added

- `tools/golden.py` records every result the library hands a caller on fixed inputs (the
  capture tops, a search with follow-ups, one with split windows and one with an injection
  job's windows, and the low-level entry points), in the order it hands them, from a seeded
  cost file, and compares two records bitwise. Two fresh runs of one tree record identical
  results (19,868 arrays). It also records correlations of complex series on a bank whose
  block-size groups interleave (scales, gapped windows, selections across groups, outputs
  reused through `out_support`, several channels) and the tiled cascade's middle calls with
  each retain mode (20,039 arrays). Every case that tiles is recorded again under the other
  schedule (the injection-window capture case and the synthetic search untiled, the first
  capture top tiled, `correlate_and_filter_many`'s small and large cohorts and each retain
  mode of the cascade untiled; 24,593 arrays), and `golden.py schedules` checks that the two
  schedules of a record gave the same peaks, hook series and, where both wrote it, the same
  middle output. It records a search whose inner nodes have inner children (three inner
  levels: packed real pairs read through their real and imaginary lanes, complex rows of a
  real series, a real filter on the real part of a complex row, complex filters), with hooks
  that read every inner ancestor's series of each leaf (23,541 arrays; two runs from one seed
  identical). With `--device gpu:0` it records the same cases on a GPU,
  from a seed of that device's own; on a Radeon 8060S three fresh runs from one seed record
  identical results. `--digest-above` keeps large arrays whole, to see how two records differ.
- `tools/gpu_alloc_trace.py` runs a program with every Vulkan device allocation traced by
  role, whether a kernel or the host ever touched it, and the breakdown at the peak of live
  device memory; a search's arena shows as its blocks, with the largest lease's sections by
  role.

### Changed

- A search reads each root's profile once per channel: the first leaf bank it calibrates
  with a profile array is handed the search's own read-only copy, and so is every later bank
  of the root and channel. The reference cache keeps no snapshot of such a copy
  (`time_domain._OwnedReference`, which nothing can change) and does not compare it again,
  where every bank compared the caller's array with a snapshot (the PyCBC job's 4 MB
  fine-grid profile: 0.24 ms a bank, 1,994 times). A caller's array is still compared on
  every `set_reference`, and each bank still checks a reference against its block sizes. An
  edit of the root's array in place after the search has read it is seen by the next search.
  PyCBC CPU job: library setup 18.9 to 18.4 s (four alternated pairs); every plan's chain,
  thresholds and screeners, the triggers and the goldens identical.
- What follows from a reference profile alone is worked out once for every plan the
  reference reaches. `TimeDomainFilterBank.set_reference` makes one `ProfileClass` per
  reference and block size (`_gatedraws`: the normalised profile and its signature, the band
  offsets and usable bands, the gate features, whether the reference has a localised peak,
  and whether a result the similarity store holds for another profile stands for it) and
  hands it to each plan; the chain choice, the thresholds and the screeners read it, where
  every call normalised, hashed and compared the profile again (29,727 chain-choice calls in
  the PyCBC CPU job). Its identity is its content. `gatechain._OFFSET_CACHE`, the
  gate-feature memo and `_hierarchical._uncovered_reference` are gone; `_band_features` lives
  in `_gatedraws`. PyCBC CPU job: library setup 20.0 to 18.4 s, wall 69.2 to 67.1 s (four
  alternated pairs), every plan's chain, thresholds, reach, offsets and screeners identical,
  triggers and goldens identical; the Radeon 8060S job's setup 19.8 to 18.5 s.
- A GPU search takes its scratch from one arena per device: the buffers its plans'
  recordings own and their pipelining slots' spectra and starts are sections of the arena,
  laid out as the plans first ask. A search keeps the arena between its runs; the next search
  to run reuses the same memory, growing it only for what no earlier search needed, and what
  the previous search's plans built on it is released (deferred work dropped, recordings on it
  freed). A Vulkan PyCBC job makes 4,742 device buffers instead of 46,595. Where
  the host does not see device memory in place (CUDA), the arena holds device-only scratch,
  and buffers the host reads back or writes stay buffers of their own. Where the device orders
  work by allocation (`DeviceProps.allocation_hazards`: Metal's hazard tracking, per
  `MTLBuffer`), every section is a block of its own, recycled from search to search; packed
  sections of shared blocks made runs of different plans wait for each other there (an M2
  search 9.6% slower). Results are unchanged.

### Changed

- A GPU plan's chain choice is shared across template counts where the count cannot change
  it. A GPU's cost model prices a feed (a forward's per-block price spread over the template
  count), and every choice was kept per count, so plans of similar profiles shared nothing
  that a CPU's plans share. Where no chain's plan priced without the feed takes a priced
  forward, the feed adds nothing to any chain's plan at any count, and the choice is kept
  without the count and shared through the similarity store, as on a CPU; elsewhere it is
  still made per count. The Vulkan PyCBC job makes 12,769 chain evaluations instead of
  24,294 and its setup is about 3 s shorter; every plan's chain, thresholds and offsets and
  every trigger are unchanged.

### Fixed

- The Vulkan backend and the chain search leave no reference cycles for the collector. Each
  `ctypes.cast` of a structure or array to a pointer made one (the source and the keep-alive
  dictionary it shares with the result): in every descriptor set, pipeline and device query,
  holding SPIR-V copies, specialization data and query structures until a collection; so did
  ctypes array and structure types made per call, and the chain search's recursive helper,
  which referred to itself and held a copy of the noise columns, made on every search even
  where the C search ran. A GPU search built, run and dropped with the collector off now
  leaves nothing of the library's for it. Results are unchanged.
- A GPU process no longer ends with "Exception ignored in `_Allocation.__del__`" (four at the
  end of every Vulkan PyCBC job). The device root, which the library holds for the process,
  was freed while the interpreter cleared modules, and its buffers' destroy() called a backend
  function already cleared, so those destroys never ran. The device roots are now released at
  exit while every module is intact (their runs finished, then their recordings, buffers,
  outputs and context), and an allocation a caller still holds when the interpreter finalizes
  is left to the process's end, on every backend.
- A PyCBC CPU job's peak memory is back to 1.6 GB from 4.2 GB. The compiled leaf steps a
  bank keeps held every bank of their batch, the keeping bank among them, so each leaf bank
  sat in a reference cycle once its top was done and was freed only when the cyclic collector
  ran: 130 to 280 MB of dead banks a top, and up to about 2.5 GB at once. The steps now hold
  their banks by weak reference.
- The hierarchical gates no longer dismiss far more than their budget on a band that holds a
  small share of the signal. The gate model's signal law took the coarse lags it does not draw
  next to the signal as independent noise. A band whose power does not fill its bins has
  correlated lags, and the largest of their noise is much smaller (2.5 against 3.4 over 258
  lags of a band whose power fills 17 of its 512 bins), so where the band's noise rather than
  the signal sets the coarse maximum the thresholds came out too high. The law now reads that
  maximum from the gate model's noise simulation, the blocks its noise pass rates come from,
  and never takes it above the independent maximum, which bounds it. In a complex bank of
  two-lobe taps at n = 1024 (budget 0.01, signals at the calibration strength 5.5), the share
  of signals missed went from 1.8%, 17% and 38% to 0.4%, 0% and 0% with half, three quarters
  and nine tenths of the power at negative frequencies; such a bank now passes most pairs to
  the refine. Ordinary plans move little: of the single-tier thresholds of the 70 references
  the test suite plans with the signal law, 230 of 340 are unchanged, 110 are lower (16 by more
  than 1%, at most 8%) and none is higher. PyCBC's leaf plans (SNR 6, budget 0.001) are
  unchanged, except chains that start at band 64 at n = 2048, whose tiers pass at most 0.1
  percentage points more noise.
- GPU and CPU runs of a PyCBC job no longer differ in their triggers beyond a few near
  threshold. The GPU ran 2048-sample leaf blocks where the CPU runs 1024, and PyCBC's power
  chisq is computed over one leaf block, so its values and the triggers a chisq cut keeps
  differed.
- GPU (experimental): the screen that chooses a coarse kernel layout times the tiled
  variants of every untiled layout within 5% of the fastest, not of the two fastest alone,
  so a reshuffle of nearly equal untiled layouts no longer leaves the best tiled one
  untimed; and a feed cost that a calibration measured as negative is priced as zero.
- GPU (experimental): a hierarchical search whose device comes from `MF_DEVICE` now
  defers and fuses its leaf calls and keeps the middle rows on the device, as a search
  given the device by name always did; five places tested for a named device instead of
  resolving it. A finished fused batch no longer keeps its plans alive: the cache of fused
  recordings held about thirty top templates' plans and buffers (25 GB of device memory in
  a PyCBC job, now 6.9 GB). Together these take the warm 171,828-template job on a Radeon
  8060S from 64.6 s to 55.2 s with identical triggers.
- The roofline report takes a GPU's peaks from device properties instead of a pattern in
  the driver's device name, which a driver update had stopped matching: the compute peak
  came out halved and the bandwidth bound was silently dropped. A peak that cannot be
  derived is now reported as unknown, with a warning, on every backend.
- The roofline report counts the work the engines run: the int16 screen as the first tier
  itself, on the shared screeners it runs on, with no float pass behind it; each tier on
  its screener pairs; and a transform's input but not its output spectrum. The model had
  charged a float first tier over every template pair behind the screen, which put a CPU
  search at 117% of its roofline. The same rules apply to every device; `docs/roofline.md`
  states them. Fractions reported before this change are not comparable with those after.
- GPU (experimental): less host work per leaf call in a hierarchical search. A freed
  recording's descriptor sets serve the next recording; single-template follow-up calls
  keep their own block layout instead of replacing the bank's; device byte views and call
  arguments no longer create a ctypes array type per call (1.5 million objects in a PyCBC
  job that only the cycle collector could free); and the fp16 packing of coarse templates
  is done in C, bit for bit NumPy's cast.
- GPU (experimental): the middle stage of a hierarchical search uses about a third less
  device time (0.90 s against 1.30 s in the 171,828-template PyCBC job on a Radeon 8060S;
  0.048 s against 0.088 s a pass in `search_bench`). The correlation kernels and the series
  forward store their output in natural order, whole cache lines at a time, where each lane
  had written to a line of its own; a chunk's channels are correlated in one submission;
  and a GPU's correlation block-size prices are keyed on the kernels they timed, so a
  rebuilt kernel is priced again. The middle rows are bit for bit what they were.
- GPU (experimental), Metal: every coarse packing and one-bin tier build that Vulkan
  ships is now built for Metal too (a 256-thread cap and a table that stopped at 8192
  samples had left 25 of them out; they were not Apple limits), and the root stages have
  32 KB builds on every backend, so a device root exists at 2^22 and 2^23 samples where a
  device's group memory is 32 KB. The Metal sources are rebuilt with the pinned compiler:
  110 of them had differed from a fresh build in line directives only. A chunk's middle
  channels are fused into one call also when the device writes caller arrays in place,
  and the number of submissions a fused batch puts in one buffer is a measured device
  choice on every backend instead of a constant per driver.
- GPU (experimental): a GPU bank's middle block size is measured at each group's own
  rows and taps, by device time, among the cost model's pick and its neighbours. The model
  extrapolates from two small measurements and had priced 16384-sample blocks at 1.8 times
  their device time, so the 171,828-template PyCBC job ran its middle at 32768; it now runs
  at 16384 and the middle's device time falls from 0.88 s to 0.81 s. The prices are stored
  in the cost file per shape; a neighbour replaces the model's pick only beyond the tie.
- GPU (experimental): the three backends share more of their code, and state what they
  share. A recording is one backend-neutral command list (seven operations in one integer
  array, no API handles), with one per-binding instance cache and one plan for fusing a
  batch; Vulkan replays it through a C emitter and its private capture format is gone.
  What a submission leaves in flight is one contract (`_gpuexec`, "Work in flight, and
  its order"): a submission is a pending write when its caller says so, the device root
  and unslotted batches do, and a leaf call on a slot does not. Metal had registered every
  leaf call, which made other queues wait on it: its `search_bench` pass goes from 1.17 s
  to 0.85 s on an Apple M2. A driver conformance suite states 29 driver contracts once and
  runs each on a simulated driver (on any machine) and on the host's device.
- GPU (experimental): a dropped context is freed at once on every backend instead of at
  the next full garbage collection (its buffers held it in a reference cycle). The peak
  GPU memory of the 171,828-template PyCBC job falls from 6.3 GB to 3.5 GB on a Radeon
  8060S (Vulkan) and from 3.6 GB to 2.1 GB on a Quadro RTX 6000 (CUDA), and its
  garbage-collection time from 3.7 s to 2.6 s on the Radeon.
- GPU (experimental): two more pieces of the backends are written once. Each device has
  one properties record that its driver fills from what the API reports
  (`_gpuhost.DeviceProps`), and shared code reads it instead of asking which backend it is
  running on. And one table in `_kernels` resolves a kernel role to the build a device can
  run, from the manifests and the device's limits; a kernel the device cannot run is
  reported, where each driver had returned a different substitute or a file that did not
  exist. A kernel is resolved once per device for the process, not per context: resolving
  and copying its record in each plan's context left about 80,000 more objects for the
  cycle collector in the PyCBC job and made it about 1% slower.

### Performance

- A GPU leaf call's peaks are assembled in C, by the assembly the CPU step table uses, and a
  `filter_series_many` batch's jobs in one call: the device's readback buffers (the counts,
  the survivor rows' bins or the compacted list) are read where the device wrote them on
  Vulkan and Metal, and from the page-locked copy on CUDA, into one arena of peaks, in the
  order the Python assembly gave (layout order, bin counts, window-bin merges, whose
  out-of-order peaks are compared by magnitude as numpy's absolute value rounds it, not as
  `hypotf` does). Results are unchanged, to the bit and in order; where the device holds
  readback buffers in the search's arena they are read as sections at their offsets. On the Radeon 8060S the capture tops' steady pass took
  0.052-0.056 s against 0.058-0.064 s, with the device busy 83-85% of it against 76%; in the
  PyCBC job the Python collecting a leaf call went from 43 to 15 us (0.85 to 0.31 s a job),
  which the job's wall time does not resolve.
- A GPU plan makes the spectra and block starts of a pipelining slot when a call first uses
  the slot, not all eight at its first call. A search collects every leaf call before its next
  chunk, so its plans use slot 0 alone, and seven of every eight slots were never touched. On
  the 171,828-template PyCBC job (Radeon 8060S) the device memory the job holds at its peak
  (VRAM and GTT above idle) went from 3.29-3.34 GB to 1.17-1.25 GB, and its allocations from
  74,511 to 46,595. Results are unchanged, to the bit.
- Gated CPU leaf calls (`filter_series` and `filter_series_many` on a hierarchical CPU bank,
  and the leaves of a CPU search) run as compiled leaf steps: the steps of a call shape are
  laid out and configured once, and a call binds its series and runs them in one C call that
  also clusters them, assembles every call's peaks and merges their window bins. A window
  list given again as a new list reuses the steps. Results are unchanged, to the bit and in
  order. On the three capture tops (one Zen 5 core) a steady pass took 1.4-2.0% less time,
  and the leaf stage's Python went from 3.6% to 1.7% of it.
- `HierarchicalSearch.timings["leaf_compute"]`: of the leaf stage, the seconds the CPU leaf
  steps spent in the extension; `tools/search_bench.py` prints it as the leaf stage's compute
  fraction.
- Single-template CPU calls (`filter_series(template_index=...)`, a search's
  `PeaksContext.refilter`, and a batch's single-template jobs) run as single-template steps
  of the same step table as the gated leaf steps (`_core.HMFTable`), compiled once per
  template group; a call binds its template, series, windows, bin size and threshold. Each
  group keeps a store of template spectra in the extension (`_core.SpectrumStore`: up to 256
  slots, each allocated when a template first takes it), shared by every table compiled from
  it, in place of the per-group cache of taps and spectra that
  each call looked up in Python. `_core.td_followup_batch` is removed. Results are unchanged,
  to the bit and in order. A follow-up call runs about 7,000 fewer instructions (one Zen 5
  core: 0.8-1.6 us less Python a call, the extension's side unchanged).
- The other every-template CPU calls, a flat bank's (`engine="flat"`) and a hierarchical
  bank's below its threshold (or at threshold 0), run as flat steps of the same step table:
  each template group's blocks of one bin count on its ungated plan, run in the extension, a
  real series widened to complex there, the peaks assembled and their window bins merged in
  the same arena as the gated steps'. The Python loop over groups and bin counts and its
  assembly no longer run for them. Results are unchanged, to the bit and in order.
- CPU correlation calls run as correlation steps of the same step table: `correlate_series`
  in one C call for every template group, `correlate_series_channels` in one C call for every
  channel and group (it called `correlate_series` channel by channel), and the middle
  correlations `correlate_and_filter_many` does not tile in one C call for consecutive CPU
  jobs; the tiled cascade's per-chunk middle calls are the same steps, every detector of a
  template batch in one C call. A step is a template group's run of output rows over the blocks a window reaches; the
  samples outside the windows are zeroed and the rows scaled in the extension, where numpy did
  it per group. The steps of a call shape are compiled once; a call binds its series, outputs
  and scales. Results are unchanged, to the bit. The binary-pulsar dense pass (complex series,
  21 channels a call; one Zen 5 core) takes 25.3-26.0 ms against 29.1-30.5 ms in its 3D shape
  and 366-374 ms against 379-403 ms in its 5D shape, with 96-97.5% of its CPU time inside the
  extension against 87-91%.
- A CPU search chunk is one table: the inner correlations of the inner nodes whose children
  are leaves and the chunk's leaf searches are the steps of one `HMFTable`, run by one C call
  (correlation steps first, then the leaf steps that read their rows). The table is compiled
  the first time a chunk's shape is seen (series length, channels, every leaf's windows and
  the spans its parent holds, what each inner node's slots hold) and kept by the search, with
  the series and spans the hooks read, so a chunk of a known shape makes no walk and builds no
  job. `correlate_and_filter_many` runs its correlations and the leaf calls that read them as
  one table wherever it tiles no cohort. One compiler (`_batches._compile_steps`) makes every
  CPU table. Results are unchanged, to the bit and in order.
- A CPU search whose inner nodes have inner children runs as one table per chunk too: every
  inner correlation, at every level, and the leaf searches are the steps of one `HMFTable`,
  compiled once per chunk shape and kept by the search, run by one C call. An inner node
  reads its parent's complex row in place, and a real lane of it (a packed pair's real or
  imaginary part, the real part of a complex row) through a contiguous buffer per inner
  batch and channel that a lane copy of the table (`HMF_OP_LANE`, a schedule op) fills once
  the parent's row is written, over the spans the parent and the buffer hold; until now such
  searches were walked node by node every chunk, the walk copying each lane in NumPy. PyCBC's
  FIR search (one inner level) is unchanged. Results are unchanged, to the bit and in order;
  a 2^17-sample nested search makes 966 Python calls a pass against 4,125, and 1.0% fewer
  instructions.
- The tiled cascade of `correlate_and_filter_many` is a schedule of the step table: the
  ordering of the same correlation and leaf steps per time tile, with the scratch, output and
  carry slots it moves samples between (clearing, margins, copies, collars, and the copies
  around the leaf peaks with `retain_radius > 0`, whose spans the executor takes from the peaks
  it just found), run by the table's one C call with the untiled correlations and leaves of the
  same call. Its Python compiler and run loop (`_CohortPrep`, `_run_tiled_group`, the collar,
  margin, copy and stale-scratch helpers, `_assemble_leaf_results`, `HMFTable.run_slices`) are
  removed. Results are unchanged, to the bit and in order, under both schedules.
- `TimeDomainFilterBank.correlate_and_filter_many` runs untiled unless `tile_bytes` is
  given: the 4 MB cap that tiled a cohort whose middle output fitted it (in practice the
  injection-window chunks of a PyCBC injection job) and `TimeDomainFilterBank._TILE_BYTES` are
  removed, and a search never tiles. Measured on one Zen 5 core, tiling forced was 1.05-1.6x
  the untiled time on a PyCBC job's full-data chunks at every tile size and tied on its
  injection-window chunks: the tiles re-read every leaf bank's templates, while what they
  save, the leaves' read of the middle output from memory, is 2-3% of a full-data pass. The
  tiled schedule stays, as an explicit choice; `tools/schedule_bench.py` times both
  schedules on a capture's chunks, to repeat the measurement on other machines. The kernel's
  streaming mirror of a tiled step's rows (`ap_mf_set_corr_mirror`) is removed: the schedule
  copies the rows. Results are unchanged, to the bit and in order.
- `HierarchicalSearch.timings["inner_compute"]`: of the inner stage, the seconds the CPU
  correlation steps spent in the extension (in the walk and in `correlate_and_filter_many`);
  `tools/search_bench.py` prints it as the inner stage's compute fraction.
- `HierarchicalSearch.timings["hooks_compute"]`: of the hooks, the seconds the steps their
  refilter calls ran (single-template steps, and gated leaf steps for every template) spent in
  the extension; `tools/search_bench.py --followups` makes pycbc_inspiral_fir's follow-ups in
  its hooks (tools/golden.py's follow-up hook) and prints it as the hooks' compute fraction.
- A run of gated leaf steps records each step's batch time in its plan from the extension
  (a buffer the plan owns, folded into `performance_stats` when read, with the same counts,
  extremes and ring of the last 256 times), so it does no Python per step; and a GPU bank's
  single-template call that runs on the CPU goes straight to its group's single-template step.
- Accounting on a GPU: a plan's resolution in its first call (`_gpu_calibration`: chain, band
  fractions and thresholds; per-plan setup) is booked in `HierarchicalSearch.timings["setup"]`
  instead of `"leaf"`, as on the CPU; when it runs is unchanged. With `MF_GPU_TIMING=1` Vulkan
  records each submission's device interval, so `_gputime.busy` (the union over the device's
  queues) is no longer zero there. `tools/search_bench.py` reads it after collecting the
  contexts' logs (Vulkan resolves its timestamps there), prints the device compute fraction
  (device busy over steady wall) beside the submissions' summed device time, and prints the
  setup passes by stage, where the booking shows.
- The calls a consumer's hooks make back into a hierarchical search, per trigger, repeat less
  work: a single-template follow-up (`PeaksContext.refilter`) runs its one job through the
  batched follow-up path without building a batch around it, and on a GPU bank whose call
  shape is locked to the CPU goes there without laying its window out twice; a hook's series
  reads settle the inner rows once; a leaf bank handed out is not looked up again; the last
  filter spectrum `get_filter_f` made is kept (PyCBC's power chisq asks for each one twice)
  and `taps_to_spectra` keeps its transform per block length instead of making one a call.
  In the 171,828-template PyCBC job (H1 and L1, ten segments, one Zen 5 core, a reused cost
  file) the hooks took 4.60 s and now take 4.38 s (31.7 to 29.4 billion instructions), and
  with the leaves on the Radeon 8060S 4.94 s and now 4.46 s (33.8 to 29.9 billion); the
  triggers are identical. The rest of the hooks is PyCBC's own work (about 3 s) and the
  follow-up's filtering (1.1 s, its transforms).
- GPU (experimental): the root of a GPU hierarchical search runs on the device. Its
  transform (the band product merged for a half-length inverse, as the host's) is two
  dispatches that take adjacent columns of the decomposition per workgroup and read the
  products a merge needs once; its output stays in device memory, where the middle stage
  reads it. A block's spectrum is uploaded once, the first time a search reads it, and kept
  while the caller's array lives (checked by its XXH64 before each use, and uploaded again if
  the caller rewrote it in place); the outputs, the template's buffer and one recording per
  chunk are kept for the process, so the search a caller builds per root (PyCBC) uploads
  and records nothing. Where a search computes its roots is a measured choice
  (`root-place`): a run's two halves go to the host and the device, their wall times per
  unit of leaf work are a round, chunks in which setup ran are left out, and the device
  stands unless the host is clearly faster (on a tie too: it moves work off the host).
  Radeon 8060S: a root of 2^20 samples takes the device 88 us per block (45 us at its
  bandwidth bound) against 1.6 ms of a Zen 5 core; `tools/search_bench.py` on the three
  captured tops runs 322-335 M templates in real time against 216-232 M; the PyCBC job
  (H1 and L1, ten segments, the GPU through `MF_DEVICE`) takes 50.0 s against 51.7 s over
  three alternated pairs, its root host time 2.6 -> 0.6 s, and its triggers move only by
  float rounding (8 of 1.3 million swap places at SNR 3).
  The device root is verified on Vulkan (Radeon 8060S), Metal (Apple M2) and CUDA (Quadro
  RTX 6000). The wrong series first seen on Metal were a driver fault, not the kernels: a
  run submitted and left in flight was not registered as a pending write on Metal and CUDA,
  so readers and later work on other queues did not wait for it. On CUDA only a run
  without a slot is a pending write, as on Vulkan; registering leaf calls too had cost 17%
  of a steady pass there.
- Shared-screener clustering, the largest part of a hierarchical search's setup, does the
  same work in less time and gives the same screeners bit for bit. The pair scores stop
  summing a pair once it can no longer reach the score the matching reads, and keep twice
  as many sums in flight on AVX-512; the matching selects each row's best candidates from
  the scores that can be candidates; the screener synthesis fills its vector lanes with
  groups of every size; the Tier-1 pairing runs in C++. In a PyCBC job of the
  171,828-template BNS search (64 top templates, H1 and L1, one Zen 5 core, a reused cost
  file) clustering took 16.1 s and now takes 13.2 s (182 to 149 billion instructions), and
  the library's setup 26.0 s and now 23.1 s; the triggers are identical.
- The clustered tiers of the hierarchical engine list each data block's surviving templates
  from a bitmap instead of sorting them. The lists and the output order are unchanged. In the
  same PyCBC job the steady search time fell from 40.1 s to 37.7 s (5.9%), with identical
  triggers.
- GPU (experimental): a PyCBC job on a Vulkan device now runs at about the speed of one CPU
  core (the 171,828-template job on a Radeon 8060S: 112-128 s before, 78-80 s now, against
  74-75 s on one Zen 5 core). A GPU leaf bank may now choose 1024-sample blocks, as the CPU
  does; the trial that places single-template follow-up calls times each call's first run,
  which is what a search makes; a GPU plan's chain choice is priced in C like the CPU's; and
  Vulkan buffers reuse their allocations instead of creating about 76,000 in a job.
  Chain choices that differ only in their prices share the part of the search that
  depends on the draws alone, and a GPU bank's follow-up calls placed on the CPU take the
  CPU banks' batched path; with these the warm GPU job measured 64 s against 65 s on the
  CPU core in the same session. A job without a cost file is still about 8 s slower on the
  GPU, which times its cost calibration in every such process.

### Documentation

- The `TimeDomainFilterBank` docstring and the usage guide no longer read as if complex taps
  had to be quadrature filters on a real series. They state that every combination of real
  and complex series and taps works with the flat, dif and corr engines, and that the
  hierarchical gates place their bands in the lower half of the spectrum, so a signal with
  most of its power in the upper half is gated on little of it and runs slowly.
- The README points to the hierarchical search design notes for `HierarchicalSearch`,
  in place of a worked example the usage guide does not have.

## 0.1.0a10

Changes since 0.1.0a9, by what a user of the library sees. The development record behind
each entry (measurements, commits, studies) is in the repository history at the tag
`pre-release-history`.

### Added

- Several noise profiles over one set of templates. A `HierarchicalFilter` holds one
  calibration per profile (`use_profile(name)`) over a single copy of the templates, and a
  `TimeDomainFilterBank` takes a reference under a name (`set_reference(..., profile=name)`)
  and filters under one (`profile=name`, also per job of `filter_series_many` and
  `correlate_and_filter_many`).
- `search.Root(profile={channel: (w, delta_f)})`: one reference profile per channel, for
  channels whose noise spectra differ (two detectors). A single `(w, delta_f)` still gives
  one calibration for every channel. `HierarchicalSearch.leaf_bank(root, leaf, channel)`
  returns a channel's bank.
- Shared screeners: on a plan of four or more templates, the first tiers may screen on the
  aligned mean of up to 16 similar templates and pass survivors to the members. The gate
  model solves the thresholds for the screener's retention, so the false-dismissal budget
  still holds. CPU (FP32, FP16, Q15) and GPU.
- `TimeDomainFilterBank.correlate_and_filter_many`: the middle correlation and the leaf
  filtering of a hierarchical search in cache-sized cohorts.
- A direct time-domain refine on the GPU, and a multi-bin one on the CPU (up to four output
  bins), each used where it is priced below the transform refine.
- An AVX back end for CPUs with AVX but not AVX2 (Sandy and Ivy Bridge): the float kernels
  run at 8 lanes where they ran the 4-lane SSE4 kernels. `targets()` lists it as `AVX`.
- CPython 3.15 wheels (Linux x86-64 manylinux and musllinux, macOS arm64).
- Tools: `fdr_audit.py --bank NT --group G` (shared screeners against the flat filter),
  `bench_refilter.py` (replay of a search's single-template follow-up calls), and the
  `setup_*.py` tools (capture and replay of a job's setup).

### Changed

Results that change are stated; everything else returns what it returned before.

- One false-dismissal budget per plan, met by construction. A plan's structure (the split
  of `fd` between tiers and, on the CPU, the direct refine's window) is searched on half of
  the gate model's detections and its thresholds are fitted on the other half. Every plan
  dismisses `fd` on average and 5% of plans dismiss more than 1.25 `fd`. Thresholds change
  everywhere. A budget below `fd` 5.5e-5 is refused.
- Block size and the Q15 screen are decided by one joint trial on real calls, on the CPU and
  the GPU, in every run (not only with `MF_COST_FILE`). The gate chain is the cost model's
  choice and is no longer timed. `MF_TRIAL_ROUNDS` replaces `MF_BLOCK_TRIALS` and
  `MF_CHAIN_TRIALS`; `MF_CHAIN_MARGIN` is gone. `tools/migrate_cost_file.py` removes the
  superseded records from a cost file.
- Chains the model prices within 5% of the cheapest are a tie, and the tie goes to the chain
  with the fewest tiers. A plan's chain, thresholds and results change wherever such a tie
  existed.
- The reduced-precision first tiers (GPU fp16, ARM FP16) gate on their own statistic, as the
  x86 Q15 screen does, in place of an upper bound on the FP32 maximum. Against the flat
  filter by injection their chains dismiss 1.02-1.04x the budget; with the bound they
  dismissed as little as 0.15x of it and passed pairs no plan priced.
- The gate model's simulations draw from a counter-based generator that gives the same
  stream at any vector width, and the planner's signal table is drawn from the joint law of
  the samples it reads rather than simulated (`MF_SIGNAL_LAW=0` simulates as before).
  Thresholds differ from before within the simulation's own error.
- Cost calibration holds under changing machine load: quantities are timed round-robin and
  each keeps its minimum. On a loaded node calibrated costs spread up to 4.7x between
  processes before and under 1.2% now.
- A single-template call (`filter_series(template_index=k)`) and a lone single-template job
  of a batch take the batched follow-up path. A job returns the same peaks however it is
  submitted; values differ from the old one-template plan's in rounding.
- A GPU batch is always fused; the device trial that chose fusion is gone.
- `gatechain.calibrate_costs` is the calibration itself, with its defaults. A model measured
  with other calls is stored under its own key.
- One generator builds every GPU kernel (`tools/kernel_variants.py`), each backend's
  manifest has one schema, and CI checks the shipped kernels against the generator.

### Removed

- The platform FFT: macOS no longer transforms through Accelerate, and
  `MatchedFilter.set_platform_fft` and `HierarchicalMatchedFilter.set_platform_fft` are
  gone. Every platform runs the library's own transforms.
- Environment variables `MF_COARSE_RAW`, `MF_GPU_FUSE_INTERLEAVE`, `MF_ILAY`,
  `MF_METAL_IEEE`, `MF_TC_KAPPA`, `MF_CAPTURE`, the three `MF_TEASER_*` (the figure tool
  takes `--n`, `--data`, `--templates`), `MF_ROOFLINE_DATAPATH` (the roofline diagnostic
  reads the 256-bit Zen 5 parts from the CPU model), `MF_HMF_PROF` (`tools/hier_bench.py`
  prints its profile from the plan's counters), and the test levers `MF_CORR_NO_STREAM`,
  `MF_GPU_ITEMS` and `MF_DEVICE_FOLLOWUPS`. Setting a removed variable warns.
- The A/A diagnostic of the measured choices: `MF_TRIAL_AA_LOG`, the extra arm it ran, and
  `tools/trial_power.py`, which read its log.
- The FP16 gate's debug mode (`MF_GATE16_DEBUG`, `MF_GATE16_DEBUG_MAX`): the electing scan
  and the all-lag rms it reported, and `tools/gate16_error.py`, which read them.
- `gatechain.direct_halfwidth`: a plan carries its direct refine's half-width
  (`chain_thresholds(...)["halfwidth"]`).
- 52 shipped GPU kernels that nothing could run or nothing chose (14.7 MB), CUDA's
  tensor-core coarse gate among them.
- The package root's re-exports of private names, and `time_domain`'s re-exports from
  `_layout` and `_windows`. The public names are unchanged (`tests/test_public_api.py`).
- From the repository: the dated studies, audits, plans and measurement logs under `docs/`,
  and the tools that only reproduced them.

### Performance

- Setup of a hierarchical search. The gate planner's simulations, threshold searches,
  shared-screener clustering and plan pricing run in C and C++, reuse results between
  similar template groups and hold a profile's draws once. On the 171,828-template BNS
  search with a profile per detector (16 workers, Zen 5), leaf setup took 114 s and now
  takes 52 s, with about 1.3 GiB less memory across the workers.
- Follow-up calls. A single-template refilter call went from 1.01 to 0.21 ms on that search
  (Zen 5), and its steady loop took 12.7% less time.
- Shared screeners, the Q15 screen, the forward and middle correlation kernels and cache
  tiling: on a 27-top production job on one Zen 5 core the steady segments took 37% less
  time than before those changes.
- Two-tier chains where the model had tied them with three: fine-stage CPU 17-18% lower on
  Haswell and Ivy Bridge at SNR 6.0, 5% on Zen 5.
- AVX back end: a fine-stage call on an Ivy Bridge E5-2660 v2 runs 1.25-1.59x faster than
  on the SSE4 kernels, by length.
- Smaller kernel changes: a split-radix 64-point codelet from 8 lanes up, in-register
  16x16 transposes on AVX-512, twiddle tables that fit the L1 cache, and one copy of each
  block's spectrum into the plan's layout.

### Fixed

- A false-dismissal budget outside (0, 1) no longer makes plan setup run without end: a
  `TimeDomainFilterBank` or `HierarchicalFilter` given one raises `ValueError`. The bank
  also refuses, by name, an unknown `engine` (it ran as the flat engine), sample rates
  that are not positive, a negative `binsize`, `coarse_band_hz` or `first_stage_snr` (they
  were ignored), a `max_batch_size` below 1, and tap counts outside their templates.
- The chain search of a plan with four tiers (`max_tiers=4`) wrote one pointer past the end
  of an array. Results were unchanged.
- A bank refuses a reference that holds no power or is not finite when it is set, naming
  the profile. A detector with no data gave an all-zero reference and the job failed later
  with an unrelated message.
- The gate model's memory follows the signal draws it still holds. Derived results kept
  evicted draws alive; on the 16-worker search above, peak resident memory fell from
  56-58 GB to 47 GB.
- The continuous correlation's block-size costs could give a zero fixed cost per block on a
  loaded node, which put each filter in a group of its own with its own forward pass.
- The direct refine's last lags of a strided lane took a different kernel path, which
  rounds 1 ulp apart on arm64.
- The gate model's simulation read and rewrote past the end of its records arrays on ARM.
  Results were unchanged.
- The musllinux wheel builds again, and the macOS arm64 single-target build compiles.
- GPU cost calibration priced the same work 0.25-4x differently between processes on a
  Radeon 8060S, and under CPU load scaled a process's prices by an anchor timed on an idle
  device. Models stored by the old method are measured again.
- A `HierarchicalSearch` with a noise profile per channel failed on a GPU ("several profiles
  in one plan are not supported on a GPU"). On a GPU it keeps a leaf bank per profile.
- The CUDA kernels load on drivers older than CUDA 12.8, which refused them (error 222).
- `MF_GPU_PROFILE=1` could lose the Vulkan device on the first call of a profiled run.
- CPU cost calibration failed (`KeyError 'recheck'`) for a size calibrated after a smaller
  one on the same series group.
- Two plans of one layout could refine a pair near the direct-or-transform boundary
  differently, each from its own timed prices. The prices are timed once per size and
  kernel.

### Documentation

- The README, the site's front page and the usage guide link to the paper,
  arXiv:2611.17229, and the README gives its BibTeX entry and INSPIRE record.
- GPU execution is labelled experimental in the README and the usage guide: it passes the
  same tests as the CPU path but lags it in a search.
- The usage guide introduces `TimeDomainFilterBank` with an executed example, and states
  that a bank's peak bins are each analysis window's, whatever the block sizes.
  `docs/hierarchical-search-design.md` describes `search.HierarchicalSearch` as it is,
  with the unimplemented parts of the design listed as proposals.
- `docs/architecture.md` is the reference for the library as it is: the public API, the
  layers, the C engine, the GPU host layer, the gate model, the cost models and the
  measured choices. `docs/README.md` lists every page.

## 0.1.0a9

### Fixed

- Peak bins are the window's, on every engine, block size and device: a `binsize` (the
  call's or the bank's) numbers each analysis window's bins from the window's start,
  wherever the blocks fall. Before, each block numbered its bins from its own span, so a
  window of exactly 1000 bins of 61 samples (pycbc's asymmetric follow-up) came back as 1021
  peaks at block size 2048 and 1002 at 4096. The hierarchical bank picks its block size by
  a timed trial, so follow-up triggers changed from run to run and did not match the flat
  filter's. Every scan now takes a bin phase per block (CPU kernels, the Vulkan, CUDA and
  Metal shaders, the hierarchical refine), and a bin a block edge cuts comes back as two
  partial bins merged by largest |snr|, the earlier sample on a tie. Without a binsize a bin
  is still the block's span. `run_series` (flat and hierarchical) takes `bin_phase`; phase 0
  is the old behaviour, bit for bit. Flat CPU cost on pycbc's test27 job: follow-up level
  with 0.1.0a8, fine stage +1.5% (half its blocks scan and report two window bins).
- The CPU direct refine applies to a row whose window lies in one bin even when a bin phase
  pads the row with empty bins. Such rows used to take the whole-block transform, which
  differs by fp32 rounding (4e-7) and costs more.
- A coarse tier's window now reaches one coarse sample past the end of the caller's window,
  as it already did before the start, on the CPU (hmf.c), the GPUs (`_gpuhost.coarse_span`,
  `band_windows`) and in the gate model. Without it, a signal in a search window's last R lags
  had a coarse sample on one side only and kept as little as 0.47 of its SNR. With pycbc's
  per-block windows the production chain dismissed 1.40-1.44x its false-dismissal budget
  against the flat filter, and 0.75-0.85x with the fix. `tools/chain_fdr_vs_flat.py --window`
  measures it.
- The gate model no longer hands one profile another's plan. Its exact cache key was a 24-bin,
  1%-quantised signature, and its reuse took any profile within cosine 0.985. An A+ reference
  planned after an O4 one (cosine 0.995) took O4's thresholds and dismissed 2.3-4.6x its
  false-dismissal budget against the flat filter. The key is now the profile to float rounding.
  Reuse also requires every candidate band's signal response, sqrt(f_b) g_b, to agree within
  0.3% (`gatechain._similar_get`). A reference that changes between calls (per-segment PSDs)
  is planned anew more often: about 1-3 s each, then cached.

### Changed

- The CPU Q15 screen is now the first tier's gate: a pair passes when its int16 maximum
  reaches the tier's threshold, with no margin and no float run of the tier behind it
  ([reduced-precision-gates.md](docs/reduced-precision-gates.md)). The chain stays within
  its false-dismissal budget against the flat filter (measured by injection), and on the
  production replica tier 1 sees 25% fewer pairs. Results with the screen on are no longer
  bit-identical to the float first tier's; reported peaks are still exact. The late
  recheck order (`set_q15_recheck_late`, `gatechain.q15_recheck_order`) and the FP16
  tier 0 behind the screen (`set_q15_tier0`, `price_q15_tier0`) are removed: there is no
  recheck left to order or price.
- The tiers between the first and the last also gate on the Q15 screen, over their survivor
  lists (`ap_mf_q15_pairs`): each lane's data and template are looked up in prepacked vectors
  inside the transform, with no gather pass. On the production replica tier 1 costs 32% less
  and the gated stages 8.8% less. The last tier stays FP32 for the direct refine's lag.

- Every `MF_*` environment variable follows one rule (`docs/environment.md`, generated
  from `matchedfilter/_config.py`): unset or empty gives the default; a switch takes
  0/false/no/off or 1/true/yes/on (any case); a number must parse; anything else raises
  `ValueError` naming the variable when the package is imported. Before, each reader had
  its own rule, and some values meant the opposite of what they say:
  - `MF_HMF_PROF`, `MF_CORR_NO_STREAM`, `MF_GATE16_DEBUG` and `MF_GATE16_DEBUG_MAX` were
    on whenever set, `=0` included;
  - `MF_GATE16=abc` turned the FP16 gate off, and `MF_GMAJOR=2` or `MF_ILAY=2` counted as
    on;
  - `MF_AUTOTUNE_LOG=` (empty), `MF_GPU_TIMING=false` and `MF_GPU_PROFILE=no` counted as
    on, and `MF_DIRECT_REFINE`, `MF_GPU_ITEMS`, `MF_DEVICE_FOLLOWUPS` and
    `MF_VK_C16_BOUND` were off only for exactly `0`;
  - a C integer that did not parse (`MF_PBMAX=big`) read as 0.
- An `MF_*` name the package does not know warns at import, with the nearest known name;
  a removed one warns with when and why it was removed.

### Removed

- C entry points nothing called: `ap_binmax_prod`, `ap_interp_max`, `ap_series_buf`,
  `ap_series_stride`, `ap_mf_run_sel`, `ap_nbins`, `ap_root_merge`, `ap_real_split`,
  `ap_mf_ndata`, `ap_hmf_get_real_series`, `ap_hmf_get_hermitian` and
  `ap_hmf_price_q15_tier0`, with the backend series store and interpolated maximum only
  they reached.
- The per-backend coarse layout fields `MF_VK_COARSE_PPG`, `MF_VK_COARSE_TILE`,
  `MF_VK_COARSE_SUBGROUP`, `MF_VK_COARSE_TWT` and `MF_METAL_COARSE_PPG` (and the
  documented `MF_METAL_COARSE_TILE`/`_TWT`, which nothing read): `MF_COARSE_LAYOUT`
  forces a whole layout by name on every backend.
- `MF_VK_C16_BOUND` is renamed `MF_COARSE_RAW`: `MF_COARSE_RAW=1` is what
  `MF_VK_C16_BOUND=0` did, on every GPU backend.
- `tools/metal_c16_sigma.py` is `tools/c16_sigma.py --backend metal|vulkan|cuda`.
- `MF_BBLK` (stage-B blocking of the balanced transform): slower than the default at
  every length measured on Zen 3, Zen 5 and an Apple M2 (1-7%).
- `MF_TRIAL_RECHECK` and the steady-state re-check it switched on (`Choice.observe`,
  `gatechain.recheck_enabled`, `observe_steady`, `steady_disagrees`, `RECHECK_*`): off by
  default, it let one process's steady timing reopen a lock for every later process, so
  processes sharing a cost file could make different choices. A stored lock is final.
- Python 3.10 support: matchedfilter needs Python 3.11 or newer, and numpy 1.23.2 or
  newer (the first numpy with Python 3.11 wheels). Release wheels cover CPython
  3.11-3.14.

- `time_domain.SegmentPlan` (segment replay: Vulkan recorded submissions and CUDA segment
  graphs) and the CUDA device follow-up selection it drove (`src/gpu/followup.cu`). Nothing
  outside the library's own benchmark used it. `filter_series_many` is unchanged, including
  Vulkan's device follow-ups. `MF_SEGMENT_REPLAY`, `MF_CUDA_SEGMENT_GRAPH` and the ladder's
  `LADDER_REPLAY`, `LADDER_FOLD_TOPS` and `LADDER_INFLIGHT` modes are gone. The gate's
  replay step became `settled`: the same check after the trials have locked.
- `filter_series_many(followups=)`, `_gpuhost.FollowupSpec` and its alias
  `time_domain.FollowUp`: the follow-up selection rule that `SegmentPlan` ran on the device.
  Nothing else called them; a search selects its own follow-ups and passes them to
  `filter_series_many` as single-template calls, which run on the device as before.
  `MF_VK_DEVICE_FOLLOWUPS` is now `MF_DEVICE_FOLLOWUPS` (Vulkan and CUDA).

### Performance

- CUDA runs follow-ups (`filter_series_many` with threshold-0 single-template calls) on the
  device: one table upload, per template group a forward and one
  `refineItems` launch, and one readback, as Vulkan does. The batch layout and result
  assembly are shared (`_gpuhost.followup_layout`, `assemble_followups`); each backend keeps
  only its executor. L40S, test27 ladder, paired on settled seeds: pipelined 1.25x, batched
  1.03x; the follow-up stage fell from 0.05-0.06 s to 0.03 s per segment. Results equal the
  host path exactly. Metal keeps the host path: follow-ups are about 6% of its segment.
- Metal fp16 coarse builds carry the fp16 twiddle table, and the tile choice measures each
  tile with each twiddle source. On an Apple M2 the table was 5-6% faster in the untiled
  builds (its bands 128 and 1024) but slower in the tile-4 and tile-8 builds.
- Vulkan and CUDA tiled fp16 coarse builds report each pair's gate decision and bound
  without electing a lag (`peakTwoGate`, Metal's since its tier-0 study): nothing reads
  tier 0's index. Radeon 8060S, band 256, interleaved: 0.91x the time per pair at the
  tiled layouts. The tensor-core gate and untiled builds are unchanged.
- CPU Q15 and block-size trials compare identical workloads in interleaved rounds,
  persist complete rounds across processes, and bound ambiguous contests. The dev1
  ten-start study selected Q15 on 10/10 times; every second process had unchanged
  trial locks and zero CPU trial work after the steady boundary. Calibration is
  more expensive upfront. Forced-lock controls put median paired throughput about
  0.2% below baseline; Q15 on was 25.0% faster than off on this workload.
  Ladder reports now flag tuning in nominal steady windows,
  and `tools/cpu_trial_check.py` separates calibration from accepted measurements.
  See [trial policy and limitations](docs/gate-model.md#cpu-paired-trials-and-bounded-measurement-2026-10-15).
- CPU Q15 screening can defer its float256 recheck until after float512 when
  the scheduling model favors that order on AVX3 N2048 chains. The same gates
  and thresholds remain; the representative Zen 5 ladder uses 3.5% less fine-stage
  time and 2.9% less whole-segment time with identical outputs. Gate work counters
  now record actual inputs, including reordered execution. See
  [gate execution order](docs/cpu-gate-order.md).
- AVX-512 N256 Q15 screens fill partial template batches with independent data
  blocks. A longer paired Zen 5 ladder comparison reduced Q15 time 4.3%, fine-stage
  time 2.1%, and whole-segment time 1.8%, with identical outputs. Small data groups,
  complete template batches, and other CPU targets retain the existing kernel.
  See [Q15 tail packing](docs/cpu-q15-tail-packing.md) for controls and limits.
- CPU hierarchical series calls prepare later-tier data only for blocks with incoming
  survivors. In a paired Zen 5 ladder comparison, fine-stage time fell 3.7% and total
  segment time 3.1%, with identical outputs. A steady segment avoided 41.8% of band-512
  copies and 88.1% of band-1024 copies. Public spectral setters retain their eager copies.
  See [work avoidance and further experiments](docs/cpu-work-avoidance.md).
- CPU survivor processing reuses shared data and packed templates, fuses the N256
  Q15 window maximum when the cache/register policy permits, and skips rejected
  pairs in the subsequent float decision loop. On a pinned Zen 5 core, alternating
  representative ladder runs improved fine throughput 1.033x and whole-segment
  throughput 1.024x with identical outputs. Gains varied across shorter runs on the
  shared host. The Q15 margin and gate thresholds are unchanged. See
  [measurements and reproduction](docs/cpu-survivor-performance.md).
- Sparse analysis-window planning bounds block candidates to each window instead of
  constructing the remaining series for every window. In a local paired benchmark with
  512 narrow windows over 2^26 samples, planning was 3.3x faster with identical layouts;
  whole-series planning was unchanged within measurement noise.
- fp16 coarse tier, untiled builds (every band on an Intel Iris Xe; bands 128 and 1024 on an
  Apple M2): the peak election is one pass over the transform registers -- each thread keeps
  its in-window maximum, that maximum's lowest slot and the register -- instead of holding
  per-register magnitude arrays. A second pass that recomputed the magnitudes was folded back
  into the first by Intel's compiler and spilled just as the arrays did (46 spills, 148 fills
  at SIMD16). Band 256 on the Iris Xe, interleaved against 0.1.0a8 on the same device: at
  subgroup 8, 0.87x the time per pair; at subgroup 16 the spills are gone (2574 -> 1303
  instructions), and its best layout takes 0.71x the time of 0.1.0a8's best (subgroup 8),
  1.41x coarse throughput. The layout measurement now picks subgroup 16 at every coarse band
  there. Same results.
- Vulkan fp16 coarse tier, untiled builds with several pairs per workgroup: any pair count
  keeps the chosen packing (ragged last group; its spare slots compute and write nothing).
  The largest packing that divided the pair count ran every odd count -- 10 of 27 fine
  groups of a test27 segment -- at one pair per workgroup: 1.95x the time per pair on a
  Radeon 8060S (half-empty wave32s), 1.7x at subgroup 16 on an Iris Xe.
- Vulkan coarse tiers with per-row windows (every fine-stage call): the windows are mapped
  onto each coarse band on the host, once per storage set, instead of in the kernel. The
  in-kernel mapping made the band-256 kernel 1.47x slower at subgroup 16 on an Iris Xe (no
  effect at 8), so production never saw the subgroup-16 gain above.

- fp16 coarse tier, untiled builds: the inter-level twiddles come from the build's fp16
  table or from the fp32 recurrence, a measured per-device choice (Vulkan specialization
  constant 80, a fourth field of the coarse layout; CUDA's table "w" builds). The
  recurrence was 13-18% of the band-256 kernel on both a Radeon 8060S and an Iris Xe;
  the table was 7-9% faster on the 8060S and 8.7x slower on the Iris Xe, whose table loads
  are 64-bit global reads. The 8060S now takes the table (band 2048: 38.3 against 41.2 ns
  per pair); the Iris Xe keeps the recurrence. Metal keeps the recurrence.

### Changed

- `clear_autotune_cache()` forgets every workload choice the process made, as its
  docstring now lists: also block-size trials, the single-device, single-batch and
  fused-batch device choices and the model's Q15 shortlist. Machine state (cost models,
  correlation prices, a GPU's kernel choices) is kept.
- Every measured choice (chain, block-size and Q15 trials, the device and fusion choices,
  kernel layouts, subgroup size, interleave, sparse readback) follows one lifecycle,
  `_choice.Choice`, and ends by construction: an unclear contest samples up to a cap, and a
  trial whose samples do not come ends at its budget of attempts, the model's choice standing
  without a clear win. Open trials persist across processes, CPU chain trials included.
- Trial locks are kept in MF_COST_FILE as `choice|<key>` records. Older `block-trial|`,
  `chain-trial|` and `q15-trial|` records are not read: a machine runs those trials once more,
  or `python tools/migrate_cost_file.py costs.json` rewrites the locks.
- One coarse launch rule on every GPU backend (`_coarse.coarse_launch`): untiled builds with
  several pairs per group take ragged groups on CUDA and Metal too (the kernel's spare slots
  compute and write nothing), so neither host pads its data rows or outputs any more.

### Fixed

- CPU cost models are stored under the series group the plans run (after `MF_DGROUP` and
  the 4 MB cap at long transforms), not the one requested: a model calibrated under
  `MF_DGROUP` was stored under the default group's key and adopted at the default.
  Calibrations at n >= 65536, where the cap applies, are re-measured once.
- `MF_DEVICE` no longer moves the library's own CPU plans (a GPU group's CPU plan for
  single-template calls, the correlation price probe) to another device: a
  single-device lock stored under `MF_DEVICE=gpu...` timed a GPU against a GPU; such
  seeds should drop their `single-device` records.
- One filter object per thread: a call on an object while another thread's call on it is
  running raises `RuntimeError` ("use one filter per thread"); it used to corrupt the
  plan's buffers silently. Lazily allocated scratch (series spectra, the DIF forwards,
  the platform-FFT buffers) is allocated all-or-nothing: one failed allocation used to
  leave a half-set state that the next call took as ready and dereferenced.
- C entry points check caller ranges and sizes without overflow: a subrange near the
  int maximum, a tap stride or an output size whose product wrapped used to pass the check
  and read or write out of bounds. A NaN threshold raises `ValueError`; a filter object
  cannot be initialised twice; `_core.forward_cost` refuses a size the engine does not
  support (it returned 1e30 s) and reports a failed allocation as MemoryError.
- `HierarchicalFilter.set_data` (and C `ap_hmf_set_data`) copies the data, as the flat
  filter does: the refine ingests the full spectrum lazily, so a caller that reused its
  buffer after `set_data` changed what the refine read (a loud peak read as none). The
  Python layer also keeps a copy, not the caller's array, for replay into a rebuilt plan.
  Costs 8n bytes per data row and one copy per call.
- Shipped Metal sources no longer name the build machine's paths in `#line` directives,
  and a stray sync-conflict copy is gone. The Metal kernel identity changes once, so
  stored Metal choices are re-measured once.
- `MF_ISA` restricts the process to its target. An invalid value raises `ValueError` at
  import, naming the build's targets; it used to print an error and segfault at the next
  kernel call. `targets()` lists only that target from the start, `set_target(None)`
  restores it (it used to switch back to the widest target), and selecting another target
  raises. A failed `set_target` changes nothing (it used to leave the default selected).
- A plan keeps its kernel for every call: the sub-plans it builds lazily (the real-series
  half transform, the DIF forwards, the pair-batch alternate, the direct refine's
  correlation, the root merge) use the plan's own target, not the one selected when they
  are built.
- MF_COST_FILE never loses data. A damaged file (truncated, not JSON, not a JSON object)
  read as empty and the next write replaced it, losing every stored model and choice: it
  is now kept aside as `<path>.corrupt.<pid>` with a warning. A file that exists but cannot
  be read is never replaced. Cost models and one-shot prices are stored first-writer-wins:
  processes calibrating or pricing at once adopt the first stored result, so they choose
  the same chains and thresholds. A stored record that is not a cost model is reported and
  recalibrated; trial records in the format before 2026-10-21 are reported once, naming
  `tools/migrate_cost_file.py`, which now writes under the library's lock, atomically.
- A GPU chain trial spread over processes too short to take a sample never ended (macOS
  Metal CI): its batch count is kept every batch, and the spent budget keeps the model's
  chain.
- Vulkan and Metal async results own their output buffers until collected. A later call
  of the same shape reused the record and overwrote them, so the earlier result returned
  the later call's peaks; a call now collects the in-flight result first, as CUDA does.
- Segment replay covers ragged layouts. When a call's blocks have several bin counts, its
  result is split per count; the parts now carry the call's trace, and a replay splits the
  replayed result the same way. Before, such segments never replayed: at n=4096 on test27
  (the GPU block size a trial can lock on a Radeon 8060S) the gate's replay check found
  none. With the fix, 7 replays of 10 segments, exact against the CPU.
- Existing Q15 plans retain their SIMD backend after `set_target()`, including lazy
  scratch allocation. Switching to a wider target previously allowed its kernel to
  overwrite buffers sized for the original plan.
- Half-spectrum DIF refinement respects full-rate bin boundaries for odd bin widths
  and clipped windows, returns the correct flat-series output shape, and breaks exact
  peak ties at the earliest lag. Changing Hermitian mode re-ingests existing templates
  with the new normalization and layout.
- Reference caches include the data sample rate and observe in-place reference, template
  and PSD edits when their setter is called again. Weak references and bounded storage
  release retired inputs instead of retaining every PSD from a long search.
- CUDA asynchronous results, including submitted segment graphs, are materialized before
  their cached output buffers are reused or freed. Early collection preserves each
  dispatch's statistics; captured segment replays keep fresh result readers.
- Concurrent `MF_COST_FILE` writers lock the read/merge/replace operation, preserving
  unrelated records written by other processes or threads.
- Coarse layout measurement (Vulkan, CUDA, Metal) times its candidates in interleaved rounds
  and confirms the contenders against the fastest, paired, instead of timing each
  candidate's repetitions back to back. On a shared GPU one burst of other work during the
  untiled stage stored a tiled layout 4.3x slower on an Iris Xe, and MF_COST_FILE kept it.
- Measured GPU kernel choices in `MF_COST_FILE` (coarse layout, tile and subgroup on Vulkan,
  CUDA and Metal; the Vulkan pipeline subgroup and fused-batch interleave) are keyed by the
  compiled artifacts they timed (`gatechain.gpu_kernel_id`), separately for each backend,
  including CUDA-only kernels and compiled Metal libraries. Builders stamp these digests
  into the manifests so startup reads a small identity rather than scanning the kernels.
  A cost file written by another build was reused, so a kernel change that moves the best
  layout -- the Iris Xe's coarse subgroup above -- never reached a machine that already
  had one.

### Documentation

- Clarify that CPU direct refinement searches near the coarse maximum and can miss a
  stronger excursion elsewhere in its bin; `MF_DIRECT_REFINE=0` uses full-bin transform
  refinement for surviving pairs.

## 0.1.0a8

The `v0.1.0a7` tag was not published to PyPI: its macOS arm64 wheel job failed
`test_reproducible_choices[gpu:0]` (a block-size lock reopened with the re-check off; fixed
below), so the publish job did not run. This release includes the 0.1.0a7 changes.

### Performance

- Real-real-complex hierarchies (`pycbc_fir_bank --complex-taps`): `TimeDomainFilterBank`
  takes complex (quadrature) final taps -- the analytic version of each real filter -- and
  filters a REAL middle series with them, same correlation convention as real taps. A CPU
  hierarchical plan reads a real series itself, as a contiguous array or in place as one
  lane (real or imaginary part) of a complex array -- a packed pair of real middle series
  -- and transforms each block at half size into its exact full spectrum (SIMD split).
  test27 full-data job (pycbc_inspiral_fir, 100k BNS bank, complex against the same
  generator's all-real bank, paired): middle stage -40% (two real middle filters as one
  complex one, in pycbc), fine stage -4 to -13% (load noise), total -6 to -10%; injection
  SNRs agree to a median ratio 1.0000 +- 0.007 (5-95%) and the same injections are found.
- CPU direct refine (docs/cpu-direct-refine.md): with one bin per pair, a survivor is
  refined by direct correlation with its real FIR taps at the lags around its last coarse
  tier's maximum -- a window the gate model sets per chain -- instead of a whole-block
  transform. `TimeDomainFilterBank` hands its taps to hierarchical plans at a rate ratio of
  1 (`HierarchicalFilter.set_taps`); the chain choice prices it. Captured
  `pycbc_inspiral_fir` calls: identical peaks, 13.7% less wall on a Zen 5 core, mostly from
  the cheaper chains it unlocks. `MF_DIRECT_REFINE=0` turns it off.
- GPU coarse layout as a measured per-device choice: tile (templates per thread) on Vulkan,
  Metal and CUDA from every shipped build, and on Vulkan the subgroup size and pairs per
  workgroup too, timed once per device and band and kept in `MF_COST_FILE`. The fixed
  per-band tile table is gone. Radeon Vega iGPU (RENOIR, GCN; gravity-dev3): +15% throughput; Intel
  Iris Xe: the coarse kernel 10-17x faster at subgroup 8 than at its default 32; Apple M2:
  untiled wins at bands 128 and 1024.
- Vulkan subgroup size of the remaining pipelines (transforms, refine, follow-ups) as a
  measured per-device choice in `MF_COST_FILE`, each candidate run in a subprocess and
  checked against the default size's triggers. Intel Iris Xe: SIMD32 by default, the
  measured size (8) runs the ladder 4.4-4.7x faster, exact. Required sizes never exceed the device's
  `maxComputeWorkgroupSubgroups` for a pipeline's workgroup (8 on the Iris Xe lost the device
  for the 1024-invocation transforms).

### Fixed

- A block-size lock could still be reopened from one process's steady-state timing with the
  re-check off (its default since 0.1.0a7, as for chain and Q15 locks), so two processes
  sharing an `MF_COST_FILE` could end on different block sizes
  (`test_reproducible_choices[gpu:0]`, 1 of 5 gate runs). The block-size re-check now
  runs only with `MF_TRIAL_RECHECK=1`.
- Vulkan fp16 coarse tier on GPUs that flush fp16 subnormals (Intel Iris Xe): templates or
  data far from unit scale were flushed to zero and every pair dismissed (`gate_margin
  --gate gpu-c16`: the transient family at every band, injections at 256-1024). The tier
  now places its operands by exact powers of two -- templates to a fixed range, data so the
  threshold sits where production banks already do (raised with the band, so the products
  a band-wide transform sums stay in fp16's normal range) -- as the CPU fp16 gate does.
  In-range results are unchanged.
- The tiled fp16 coarse kernel dismissed every pair of an overflowing (very loud) row when
  a pair spans more than one subgroup -- band 1024 on 32-wide subgroups (Intel, NVIDIA) --
  and its error bound overflowed to inf for ordinary pairs there. Every backend now uses
  the integer overflow test Metal had and the scaled energy of the single-subgroup path.

## 0.1.0a7

### Fixed before release

- Two processes sharing an `MF_COST_FILE` could end on different gate chains
  (`test_reproducible_choices[gpu:0]` failed 1 in 5 on the L40S; the macOS Metal
  CI wheel failed it too). Two causes. A stored chain lock was checked against
  the first plan's own feasible chains, and when that plan could not run it the
  process recorded "no lock" and re-trialled for every plan of the key; the lock
  now decides every plan that can run it, the others run their model's chain,
  and a locked key never opens a trial. And the steady-state re-check reopened a
  lock on one process's timing, so the next process could lock another choice;
  it is now opt-in (`MF_TRIAL_RECHECK=1`, see the usage guide), and a stored
  lock is final until the cost file is deleted.

- Re-measure the hardware comparison at `2b3cac13` on gravity-dev1,
  gravity-dev2 (CPU and Radeon 8060S), gravity-dev3 (CPU), Apple M2 (CPU and
  GPU), Haswell (CPU) and the NVIDIA L40S, at 16 × 512 and, new for the CPUs,
  512 × 512. See [teaser-fleet-20261013](docs/measurements/teaser-fleet-20261013.md).
  Entries not re-measured (A100 and A40 from 2026-10-04 at `2a33e8f`; the
  gravity-dev3 GPU, gravity-dev4, sugwg-login2 and the EPYC 9845 CPU from
  2026-10-03 at `50597f3`) are carried over and labelled with their date and
  revision. Haswell ran at load 35-37 and its rows are indicative only. The
  README teaser is redrawn from the gravity-dev2 512 × 512 reports with the
  new `tools/teaser_figure.py --from-fleet`, without re-measuring.

- Add the Haswell node (Xeon E5-2698 v3) to the hardware comparison. It had
  been in the PyCBC fleet benchmark from the start but never the hardware
  comparison, which is an odd gap for the oldest and most register-starved
  x86 target in the fleet. It exposes no GPU, and as a shared cluster node at
  load 41.8-44.2 of 64 cores only its FFTW (1.3%) and peak-only (2.5%) rows
  reproduce across three runs; full output (20.7%) and hierarchical (9-64%)
  are indicative only. Its SNR sweep is non-monotone where all six other
  hosts are monotone; the gate selects the identical band, taps and
  refinement fraction as gravity-dev1 at every threshold, so that is
  measurement noise on a contended host, not a selection fault.
- Re-measure both fleet benchmarks at `main` `eecb43c` (twenty-five
  optimization passes). PyCBC complete search against the previous head
  `ce9c828`: dev3 +7.4%, dev1 +2.3%, dev4/sugwg-login2/Haswell flat. The
  largest gain lands on the smallest, most cache-constrained host. Six-machine
  comparison at `eecb43c`: peak-only improves 2.6-5.9% on every uncontended
  CPU, full output is flat, hierarchical mode is mixed (M2 +9.6%, Xeon +8.9%,
  others flat), and the GPU is unchanged within about 1%. See
  [pycbc-main-eecb43c-fleet-20260928](docs/measurements/pycbc-main-eecb43c-fleet-20260928/README.md)
  and [teaser-fleet-20260928](docs/measurements/teaser-fleet-20260928.md).
  gravity-dev2 was under load 38 throughout and both its rows are labelled;
  the README teaser, which can only be measured on that host, is left at
  `ce9c828` rather than republished three times slow.

- Draw the teaser and fleet banks from the captured PyCBC reference profile
  (`tests/data/reference_profile_pycbc.npy`) instead of the synthetic
  inspiral curve. The synthetic curve is narrower than a real reference
  (`B_eff` 180.8 against 232.7 at band 512), and the hierarchy's cost follows
  from that width, so it flattered the gate. Hierarchical timings are slower
  and are not comparable to earlier pages.
- Record hierarchical rows at SNR thresholds 5.0, 5.5, 5.75, 6.0 and 6.5. The
  threshold spans a factor of 2.5-4 at `fd=1e-3` and can change the band the
  gate selects. On the hardware comparison page the threshold and the FDR
  budget share one Hierarchical screening box and both are multi-select, so a
  series is one (budget, threshold) pair and several can be compared at once.
- Recalculate both fleet measurements at `main` `ce9c828`. The six-machine
  hardware comparison moves to
  [teaser-fleet-20260927](docs/measurements/teaser-fleet-20260927.md); the
  September 26 page is kept for history. Fixed FFTW/rocFFT references
  reproduce within 0.8% on the four uncontended machines, and full-output and
  peak-only are flat within noise. A like-for-like run on the synthetic
  profile, before the reference change above, put the revision's gain in
  hierarchical mode at tight budgets (`fd=1e-4` CPU 15-38%); the published
  page now carries captured-profile numbers, which are slower in absolute
  terms and not comparable across the two profiles.
- Record the PyCBC complete-search fleet benchmark for `ce9c828` in
  [pycbc-main-ce9c828-fleet-20260927](docs/measurements/pycbc-main-ce9c828-fleet-20260927/README.md).
  Against the previously documented head `c38f24f`: Haswell +5.3%, dev4 +4.1%,
  dev3 +3.3%, dev2 +1.1%, sugwg-login2 -0.2%, dev1 -1.2%. The Haswell gain is
  the first measured on that host in this line of work. Correctness for this
  revision is not yet established; the numbers are timing only.

### Known issues

- On CUDA, two processes sharing a cost file can occasionally lock different
  gate chains (seen in 1 of 5 runs of `test_reproducible_choices[gpu:0]` on
  the L40S). Results are correct; only borderline peaks may differ between
  the processes. A fix is in progress.

## 0.1.0a6

- Optimize the Haswell hierarchical coarse path with specialized FFT32
  codelets, reduced intermediate traffic, and fused thresholded peak reduction.
  The measured complete search reaches about 349,000 template-seconds/s/core,
  roughly 1.56x the neighboring original baseline. These are workload-specific
  measurements; see [the evidence and controls](docs/haswell-series-grouping.md).
- Add a shared measured execution-policy table for CPU/GPU scheduling. The
  initial rule selects a smaller series group for the measured Haswell workload;
  uncovered devices retain their existing scheduling defaults.
- Bind balanced product kernels once per bank and avoid counting pair-batched
  peaks twice. Calibration tables and thresholds are unchanged.
- Fix blocked stage-B intermediate indexing and test reused plans, partial
  windows, signed zero, full output, peak counts, and CPU calibration transfer.
  The coarse FDR guard explicitly exercises AVX2 on wider CPU hosts.

## 0.1.0a3

The earlier `v0.1.0a2` tag was not published to PyPI; this release includes
those changes and the subsequent fixes below.

This alpha adds Vulkan and Metal GPU execution, full correlation output,
and consistent overlap-save interfaces alongside the existing CPU peak filters.

### Added

- `CorrelationFilter` returns every complex lag in natural order, with the
  spectral product fused into the inverse FFT. CPU and GPU support powers
  of two from 1,024 through 4,194,304. `run()` supports bank selectors and
  reusable output storage; `empty_shared()` provides GPU-accessible storage.
- GPU flat and hierarchical filtering through `device="gpu"`, using shipped
  Vulkan/SPIR-V or native Metal kernels. Peak transforms support powers of
  two from 64 through 65,536 on GPU, subject to device limits; CPU peaks
  support 64 through 1,048,576. Unsupported requests raise explicitly.
- Automatic overlap-save execution across all three classes. Construct a
  filter with `valid=(lo, hi)` and call `run_series(series)`; block spacing
  follows from the valid interval. Peak filters return block-major peaks
  with absolute series indices. Full correlation writes valid lags directly
  into a reusable, class-owned `(templates, series_length)` result on CPU
  and GPU, without an intermediate cube or a stitching copy.
- `run_blocks()` names explicit starts and per-block peak windows. The older
  explicit-start `run_series()` form remains supported with block-local
  indices. Series execution reuses data slots; call `set_data()` before a
  subsequent spectral `run()`.
- Host-compatible DLPack ingestion, device discovery, bank subranges,
  shared GPU output buffers, and explicit output-lifetime documentation.
- Benchmarks covering supported transform lengths and series workloads,
  FFTW/MKL references, opt-in performance regression tests, and a recorded
  six-machine comparison with selectable output modes, CPU/GPU models, and axis scales.

### Changed

- Hierarchical automatic configuration requires a covering measured
  calibration file. Otherwise callers must supply both a coarse `band`
  and `set_coarse_threshold(value)`. There is no model or default threshold
  fallback; manual thresholds carry no calibrated dismissal guarantee.
- Per-device cost tables choose coarse configurations. The requested
  `snr`/`fd` budget is a calibration condition, not a guarantee for an
  arbitrary template population.
- Full-output automatic allocation is capped at 512 MiB. Select smaller
  bank ranges or supply storage for larger spectral/block results.
- Python 3.9 support is dropped. Wheels target CPython 3.10–3.14 on Linux
  x86-64 and macOS arm64.

### Performance

- Shared batching and cache handling across `run()`, `run_series()`, and
  `run_blocks()`, coarse-template reuse, and grouped GPU submissions for
  irregular windows reduce repeated preparation and submission costs.
- Metal uses specialized single-bin flat/refinement kernels at 2,048–8,192
  points, grouped window submissions, and cached Objective-C wrappers.
- Full output retains fused products and batch reuse; peak-only output
  additionally avoids writing full correlations, while hierarchy can avoid
  most full transforms. Gains depend on hardware, batch shape, and survivor
  rate. See the [recorded comparison](docs/measurements/teaser-fleet-20260926.md)
  rather than treating one GPU/CPU ratio as universal.

### Fixed

- Intel Vulkan twiddle accuracy now meets the existing FP32 tolerance,
  using a device-specific specialization. Other GPUs retain native trig.
- Vulkan hierarchical dispatch synchronizes transfer-filled arguments and
  compacted survivor counts before indirect execution, including first use
  and reused plans switching between all and zero surviving pairs.

- Vulkan contexts now release device resources when filters are dropped;
  destruction is idempotent.
- Raw peak results consistently return `(index, value)` on CPU and GPU.
- Ragged explicit-block windows no longer write beyond the output stride.
  Output dimensions, selectors, buffer ownership, and reuse are validated.
- Coarse-template caching, pinned GPU configurations, reference/threshold
  changes, and data replacement correctly invalidate or reuse cached state.
- Automatic device selection includes Metal. Workgroup, staging-memory,
  and dispatch limits are checked rather than relying on pipeline failure.
- Portable hardware identification and benchmark formatting fix macOS and
  ARM CI failures.

### Known limitations

- This remains an alpha. GPU execution is synchronous; buffers returned from
  reusable storage must be copied if needed after the next call.
- Large full transforms need substantial scratch/output memory and are not
  equally optimized across devices. Device workgroup limits may rule out
  some GPU sizes even when the CPU supports them.
- Hierarchical selection costs are not optimal on every device. The M2
  and Iris Xe measurements identify further improvements for stricter
  dismissal budgets.
- GPU coarse screening may use reduced precision, with FP32 refinement.
  Statistical calibration must be checked against the caller's inputs.

## 0.1.0a1

First alpha: single-threaded batched matched filter with peak-only output,
a hierarchical two-stage variant, and Highway multi-target SIMD dispatch on
the CPU.
