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
    array's id cannot alias a new one). A block is uploaded once, not once per search: the
    caller must not rewrite a spectrum in place once a search has read it (BlockInput);
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

from . import _kernels
from ._errors import UnsupportedSize
from ._shared import BUFFER_SERIALS, shared_view

#: Per device (its str): the DeviceRoot, or None where the device cannot run the root.
_ROOTS = {}


def device_root(device):
    """The DeviceRoot of a parsed GPU device, made on first use, or None when its backend
    cannot run one (no context)."""
    key = str(device)
    if key not in _ROOTS:
        from ._filter import _compute_module
        try:
            ctx = _compute_module(device).Context(device.index)
        except Exception:          # no driver for it: the host computes every root
            ctx = None
        _ROOTS[key] = (DeviceRoot(ctx, getattr(ctx, "device_name", None) or key)
                       if ctx is not None else None)
    return _ROOTS[key]


class _Block:
    """One input block's spectrum in device memory, named by a weak reference to the
    caller's array object."""
    __slots__ = ("ref", "buffer", "serial")

    def __init__(self, ref, buffer):
        self.ref, self.buffer, self.serial = ref, buffer, next(BUFFER_SERIALS)


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
    def _collect(self):
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
        first use, or None where the array cannot be named (no weak reference)."""
        key = id(spectrum)
        b = self._blocks.get(key)
        if b is not None and b.ref() is spectrum:
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
        arr = np.ascontiguousarray(np.asarray(spectrum)[:nbins], dtype=np.complex64)
        buf = self.ctx._x_alloc(arr.nbytes)
        buf.write(arr)
        b = self._blocks[key] = _Block(ref, buf)
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
        self._collect()
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


#: The placements of a GPU search's roots: the preference first (it stands unless the host is
#: clearly faster).
PLACES = ("device", "host")


class Placement:
    """Where a GPU search computes its roots at one series length on one device: "device"
    (DeviceRoot) or "host" (_core.Root, overlapped with the device's leaf work where the
    walk allows), one measured choice (_choice) for the process and, through MF_COST_FILE,
    later ones.

    Which is faster depends on which side bounds the search: a host that runs the hooks and
    feeds the device gains the root's host time from the device; a device that is already
    the bound (a slow GPU beside a fast core, sharing its memory bandwidth) loses the root's
    device time, while the host's root hides under the device's leaves. So it is measured on
    the search's own chunks, as it runs:

      * placement holds for two consecutive roots at a time, in the order host, device,
        device, host (a block each), so that the rounds alternate which arm goes first;
      * a chunk's time -- from its start to the next chunk's, with the root computed ahead
        during it -- is a sample of its placement when both roots it used (its own and the
        next one) had that placement, normalised by the chunk's leaf work (templates x
        searched samples);
      * a chunk in which any setup ran -- a bank built or calibrated (the search's setup
        timer), a root recording built or a block uploaded (DeviceRoot.built), the host's
        transform plan made -- is no sample: neither arm pays setup in its timed runs. Both
        placements write the same output buffers, so moving between them rebuilds nothing
        downstream (the October trial measured those re-recordings);
      * consecutive samples of the two arms within one run are a round (_choice.Choice.round:
        the device stands unless the host is faster by the tie in three quarters of rounds).

    A run's first chunk is no sample either (its banks' first calls record their device
    work). A contest that gets no rounds (runs of one chunk) ends on its budget of roots
    placed (BUDGET, _choice.Choice.tick), the device standing. Without autotuning the device
    stands."""

    #: (per arm, slack) roots placed before an open contest ends (Choice's budget).
    BUDGET = (40, 20)

    def __init__(self, key, store_key):
        from . import _choice
        self.choice = _choice.choice("root-place", key, PLACES, store_key=store_key,
                                     what="root placement %s" % (key,), budget=self.BUDGET)
        self._blocks = 0             # placement blocks started (the schedule's position)
        self._left = 0               # roots left in the current block
        self._arm = None
        self._half = None            # a sample awaiting its round: (arm, seconds per work)

    def winner(self):
        from ._choice import _autotune_enabled
        if self.choice.winner is not None:
            return self.choice.winner
        if not _autotune_enabled():
            return self.choice.preference
        return None

    def next(self):
        """Where the next root is computed."""
        w = self.winner()
        if w is None:
            w = self.choice.tick()
        if w is not None:
            return w
        if self._left <= 0:
            self._arm = PLACES[1] if self._blocks % 4 in (0, 3) else PLACES[0]
            self._blocks += 1
            self._left = 2
        self._left -= 1
        return self._arm

    def new_run(self):
        """A run starts: a sample left from the one before has no partner."""
        self._half = None

    def sample(self, arm, seconds_per_work):
        """A clean chunk's time per unit of leaf work, its roots computed at `arm`."""
        if self.winner() is not None:
            return
        if self._half is None or self._half[0] == arm:
            self._half = (arm, seconds_per_work)
            return
        prev, self._half = self._half, None
        from ._choice import _AUTOTUNE_LOCK
        with _AUTOTUNE_LOCK:
            self.choice.round({prev[0]: prev[1], arm: seconds_per_work})


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
