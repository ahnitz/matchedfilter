"""The root stage of a hierarchical search on a GPU (HierarchicalSearch, search.py).

The root's output for an input block is the real n-point series scale * C2R(conj(T) D) over
the root's band: on the host, _core.Root (one n/2-point transform of the merged spectrum,
src/rsplit-inl.h); here the same transform as two device dispatches (src/gpu/root_transform.slang:
the merge and the first stage of the n/2-point inverse; the second, writing the series),
which the middle stage then reads where it was written.

What it keeps, so that its steady cost is the transform's and nothing else:
  * one context per device for the process, whatever the number of searches (pycbc builds
    one per top template), holding everything below;
  * each input block's spectrum in device memory, uploaded the first time a search reads
    it and kept while the caller's array object lives (a weak reference names it: a freed
    array's id cannot alias a new one). A block is uploaded once, not once per search; each
    run checks the array's contents against the copy's (its XXH64, _signature)
    and uploads it again if a caller rewrote it in place;
  * the root's spectrum in one buffer per length, written once per run;
  * the outputs, a pool of series buffers that searches take for a run and give back, so
    a search per root reuses the buffers -- and the middle stage's recordings, keyed on
    them -- of the search before;
  * one recording per chunk shape (the blocks' and outputs' buffers), replayed on every
    later run: the band and the scales are read from a small parameter buffer the host
    writes before each run, so they change nothing that is recorded.

Placement (host or device) is the search's decision (search.py, _root_place); both write
the same pooled outputs, so moving between them re-records nothing downstream.
"""
import weakref

import numpy as np

from . import _core, _kernels
from ._errors import UnsupportedSize
from ._shared import BUFFER_SERIALS, shared_view

#: Per device (its str): the DeviceRoot, or None where the device cannot run the root.
_ROOTS = {}

#: Backends whose root kernels have been run against the host root on hardware. The Metal
#: build gave wrong series on an Apple GPU (CI, 2026-11-25) and the CUDA build has not been
#: run: until each passes tests/test_gpu_root.py on a device, its searches keep the host
#: root. This is a statement about verification, not a tuning choice; a backend joins the
#: list when its kernels pass, and placement is then measured as on Vulkan.
VERIFIED_BACKENDS = ("vulkan",)


def device_root(device):
    """The DeviceRoot of a parsed GPU device, made on first use, or None when its backend
    cannot run one (no context) or its root kernels are not verified (VERIFIED_BACKENDS)."""
    key = str(device)
    if key not in _ROOTS:
        from ._filter import _compute_module
        ctx = None
        try:
            if device.backend in VERIFIED_BACKENDS:
                ctx = _compute_module(device).Context(device.index)
        except Exception:          # no driver for it: the host computes every root
            ctx = None
        _ROOTS[key] = (DeviceRoot(ctx, getattr(ctx, "device_name", None) or key)
                       if ctx is not None else None)
    return _ROOTS[key]


def _signature(arr):
    """A block's contents in one word: XXH64 of its bytes (_core.xxh64, one read of the
    array at memory speed). Every word is mixed at its position, so a rewrite that permutes
    words or whose changes cancel changes it too."""
    return _core.xxh64(arr)


class _Block:
    """One input block's spectrum in device memory, named by a weak reference to the
    caller's array object, with the signature of the contents it was uploaded with."""
    __slots__ = ("ref", "buffer", "serial", "sig")

    def __init__(self, ref, buffer, sig):
        self.ref, self.buffer, self.serial, self.sig = ref, buffer, next(BUFFER_SERIALS), sig


class DeviceRoot:
    """The root stage on one GPU context (see the module docstring)."""

    def __init__(self, ctx, name):
        self.ctx, self.name = ctx, str(name)
        self._kernels = {}           # n -> (stage 1, stage 2, split), or None (unsupported)
        self._blocks = {}            # id(spectrum) -> _Block
        self._dead = []              # blocks whose array died: freed once no run reads them
        self._tmpl = {}              # n -> template buffer
        self._params = {}            # (n, parity) -> (buffer, channels it holds)
        self._scratch = {}           # (n, channel position) -> scratch buffer
        self._records = {}           # (n, parity, ((block, out) serials per channel)) -> native
        self._free = {}              # (n, channel position, parity) -> idle output arrays
        self._last = {}              # (n, parity) -> wait() of the newest run there
        self._tmpl_run = {}          # n -> wait() of the newest run reading the template
        #: Setup this context did (recordings built, blocks uploaded): a timing that is to
        #: stand for steady state leaves out the chunks in which it grew.
        self.built = 0

    # ---- what it can run --------------------------------------------------------------
    def kernels(self, n):
        """(stage 1, stage 2, stage 1 workgroups, stage 2 workgroups) at series length n, or
        None: n/2 needs the two-stage transform (2^17 to 2^22), whose root kernels this
        backend shipped and this device can run. A workgroup takes `ppg` columns of the
        n/2 = n1 n2 decomposition (the kernels' manifest record)."""
        if n not in self._kernels:
            got = None
            h = n // 2
            if n >= 4 and n & (n - 1) == 0:
                try:
                    n1, n2 = self.ctx._x_tierc(h)
                    ppg = int(_kernels.record(self.ctx.kernel_family, "tc_root1_%d" % h)["ppg"])
                    got = (self.ctx._x_kernel("root1", h), self.ctx._x_kernel("root2", h),
                           n1 // ppg, n2 // ppg)
                except Exception:      # not shipped, or a pipeline this device cannot make
                    got = None         # (tests/test_gpu_root.py builds it where it can)
            self._kernels[n] = got
        return self._kernels[n]

    # ---- the outputs ----------------------------------------------------------------------
    def take_output(self, n, position, parity):
        """A series buffer (float32, n) in device memory the host reads: an idle one of this
        (length, channel position, chunk parity), else a new one."""
        idle = self._free.get((n, position, parity))
        if idle:
            return idle.pop()
        return self.ctx.empty_shared((n,), np.float32, readback=True)

    def give_output(self, n, position, parity, out):
        """Return a buffer take_output gave; the next take of the same kind gets it back."""
        self._free.setdefault((n, position, parity), []).append(out)

    # ---- device copies of the inputs -------------------------------------------------------
    def collect(self):
        """Free the blocks whose arrays died, once no run still reads them."""
        if not self._dead:
            return
        for wait in list(self._last.values()):
            wait()
        self._last.clear()
        dead, self._dead = self._dead, []
        gone = {b.serial for b in dead}
        for key in [k for k in self._records if any(s in gone for s, _ in k[2])]:
            self.ctx._x_release(self._records.pop(key), done=True)
        for b in dead:
            self.ctx._x_free(b.buffer)

    def _block(self, spectrum, nbins):
        """The _Block holding `spectrum` (its first nbins bins) in device memory, uploaded on
        first use and again whenever its contents changed (a caller that rewrote the array in
        place: its signature differs), or None where the array cannot be named (no weak
        reference)."""
        key = id(spectrum)
        b = self._blocks.get(key)
        arr = np.ascontiguousarray(np.asarray(spectrum)[:nbins], dtype=np.complex64)
        sig = _signature(arr)
        if b is not None and b.ref() is spectrum:
            if b.sig != sig:
                for wait in list(self._last.values()):   # runs still reading the old copy
                    wait()
                self._last.clear()
                b.buffer.write(arr)
                b.sig = sig
                self.built += 1
            return b
        try:
            def gone(_ref, key=key, roots=weakref.ref(self)):
                me = roots()
                if me is not None:
                    blk = me._blocks.get(key)
                    if blk is not None and blk.ref is _ref:
                        me._dead.append(me._blocks.pop(key))
            ref = weakref.ref(spectrum, gone)
        except TypeError:
            return None
        buf = self.ctx._x_alloc(arr.nbytes)
        buf.write(arr)
        b = self._blocks[key] = _Block(ref, buf, sig)
        self.built += 1
        return b

    # ---- a chunk's roots ----------------------------------------------------------------
    def set_template(self, n, spectrum):
        """Write the root's spectrum (its first n/2 + 1 bins) for the runs that follow, once
        the runs reading the one before have finished."""
        h = n // 2
        arr = np.ascontiguousarray(np.asarray(spectrum)[:h + 1], dtype=np.complex64)
        if arr.shape[0] != h + 1:
            raise ValueError("a root spectrum needs %d bins at series length %d" % (h + 1, n))
        buf = self._tmpl.get(n)
        if buf is None:
            buf = self._tmpl[n] = self.ctx._x_alloc(arr.nbytes)
        wait = self._tmpl_run.pop(n, None)
        if wait is not None:
            wait()
        buf.write(arr)

    def run(self, n, parity, blocks, outs, band, scales):
        """Submit the roots of one chunk, left in flight (device readers are ordered after
        them; a host reader settles the device's writes first): blocks[c] (a spectrum of
        n/2 + 1 bins) into outs[c] (a take_output buffer), over band (k0, k1) at scales[c].
        Returns the number of recordings this call built (0 in steady state)."""
        stage1, stage2, groups1, groups2 = self.kernels(n)
        h = n // 2
        built = self.built
        self.collect()
        bufs = [self._block(s, h + 1) for s in blocks]
        if any(b is None for b in bufs):
            raise UnsupportedSize("a root input block that cannot be named")
        nch = len(blocks)
        # the previous run on this parity's parameters and scratch has finished
        wait = self._last.pop((n, parity), None)
        if wait is not None:
            wait()
        held = self._params.get((n, parity))
        if held is None or held[1] < nch:
            if held is not None:
                for key in [k for k in self._records if k[:2] == (n, parity)]:
                    self.ctx._x_release(self._records.pop(key), done=True)
                self.ctx._x_free(held[0])
            held = self._params[(n, parity)] = (self.ctx._x_alloc(16 * nch), nch)
        words = np.zeros((held[1], 4), np.uint32)
        words[:, 0], words[:, 1] = int(band[0]), int(band[1])
        words[:nch, 2] = np.asarray(scales, np.float32).view(np.uint32)
        held[0].write(words)
        views = [shared_view(o, self.ctx) for o in outs]
        if any(v is None for v in views):
            raise ValueError("root outputs must be take_output buffers")
        key = (n, parity, tuple((b.serial, o.owner.serial) for b, o in zip(bufs, views)))
        bufs = [b.buffer for b in bufs]
        native = self._records.get(key)
        if native is None:
            tmpl = self._tmpl[n]
            lst = self.ctx._x_list("root")
            lst.barrier()                    # earlier readers of the outputs and scratch first
            scratch = []
            for c in range(nch):
                s = self._scratch.get((n, c))
                if s is None:
                    s = self._scratch[(n, c)] = self.ctx._x_alloc(8 * h)
                scratch.append(s)
                lst.dispatch(stage1, groups1, [bufs[c], tmpl, held[0], s], (c,))
            lst.stamp("root merge + stage 1")
            lst.barrier()
            for c in range(nch):
                lst.dispatch(stage2, groups2, [scratch[c], views[c]])
            lst.stamp("root stage 2")
            lst.barrier()
            native = self._records[key] = lst.end()
            self.built += 1
        wait = self.ctx._x_submit(native, {}, None)
        self._last[(n, parity)] = wait
        self._tmpl_run[n] = wait
        return self.built - built


#: The placements of a GPU search's roots: the preference first. It stands unless the host is
#: clearly faster -- on a tie too: a device root moves work off the host, which is the
#: direction a GPU search wants (the host's time is what its hooks and the next chunk need).
PLACES = ("device", "host")


class Placement:
    """Where a GPU search computes its roots at one series length on one device: "device"
    (DeviceRoot) or "host" (_core.Root, computed ahead while the device runs the leaves),
    one measured choice (_choice) for the process and, through MF_COST_FILE, later ones.

    Which is faster depends on which side bounds the search, and the time a choice moves
    lands away from the root: a host root computed ahead hides under the device's leaves, and
    a device root's host time saved can come back as a longer wait for those leaves. A sample
    must therefore hold everything the choice changes, end to end. So the trial compares the
    two halves of one run (one root: the same templates, comparable chunks):

      * a run's roots before its middle chunk go to one arm, the rest to the other, the
        first arm alternating from run to run (host first, then device first, ...);
      * each half's sample is its chunks' wall time summed -- every chunk from its start to
        the next one's, the next root computed ahead in it, the leaves waited for and the
        hooks run -- per unit of leaf work (templates x searched samples), over the chunks
        whose own root and next root were both of that half: the chunk at the switch, the
        run's first chunk (its banks' first calls record their device work) and any chunk in
        which setup ran -- a bank built or calibrated, a root recording built or a block
        uploaded (DeviceRoot.built), the host's transform plan made, a recording built by a
        bank's GPU context (a new top's first calls, a call shape's band forward) -- are
        left out, so
        neither arm pays setup in its timed time;
      * the two halves of a run are a round (_choice.Choice.round): the device stands unless
        the host is faster by the tie in three quarters of rounds, and on a tie (see PLACES).

    Both placements write the same output buffers, so moving between them rebuilds nothing
    downstream (the October trial measured those re-recordings). A contest that gets no
    rounds (runs too short to split) ends on its budget of roots placed (BUDGET,
    _choice.Choice.tick), the device standing. Without autotuning the device stands."""

    #: (per arm, slack) roots placed before an open contest ends (Choice's budget).
    BUDGET = (80, 40)

    def __init__(self, key, store_key):
        from . import _choice
        self.choice = _choice.choice("root-place", key, PLACES, store_key=store_key,
                                     what="root placement %s" % (key,), budget=self.BUDGET)
        self._runs = 0               # runs started while the contest is open
        self._run = None             # this run's (arm order, split chunk, {arm: [s, work]})

    def winner(self):
        from ._choice import _autotune_enabled
        if self.choice.winner is not None:
            return self.choice.winner
        if not _autotune_enabled():
            return self.choice.preference
        return None

    def new_run(self, nchunks):
        """A run of nchunks chunks starts: its halves' arms."""
        order = (PLACES[1], PLACES[0]) if self._runs % 2 == 0 else (PLACES[0], PLACES[1])
        self._runs += 1
        self._run = (order, int(nchunks) // 2, {a: [0.0, 0] for a in PLACES})

    def next(self, k):
        """Where the root of chunk k is computed."""
        w = self.winner()
        if w is None:
            w = self.choice.tick()
        if w is not None:
            return w
        if self._run is None:
            return self.choice.preference
        order, split, _ = self._run
        return order[0] if k < split else order[1]

    def sample(self, arm, seconds, work):
        """A clean chunk of this run: its wall time and leaf work, its roots at `arm`."""
        if self._run is not None:
            acc = self._run[2][arm]
            acc[0] += seconds
            acc[1] += work

    def end_run(self):
        """The run is over: its two halves are a round, when both have samples."""
        run, self._run = self._run, None
        if run is None or self.winner() is not None:
            return
        acc = run[2]
        if all(a[1] > 0 and a[0] > 0 for a in acc.values()):
            from ._choice import _AUTOTUNE_LOCK, _log_autotune
            _log_autotune("root placement round: %s first, %s", run[0][0], ", ".join(
                "%s %.4f s / %d = %.3g" % (arm, a[0], a[1], a[0] / a[1]) for arm, a in acc.items()))
            with _AUTOTUNE_LOCK:
                self.choice.round({arm: a[0] / a[1] for arm, a in acc.items()})


#: (device, series length) -> Placement, for the process.
_PLACEMENTS = {}


def placement(root, n):
    """The Placement of roots of length n on DeviceRoot `root` (made on first use)."""
    key = (root.name, n)
    p = _PLACEMENTS.get(key)
    if p is None:
        from ._costmodel import gpu_kernel_id
        p = _PLACEMENTS[key] = Placement(key, "root-place|%s|n%d|k%s" % (
            key[0], n, gpu_kernel_id(root.ctx.kernel_family)))
    return p
