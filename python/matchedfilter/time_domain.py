"""TimeDomainFilterBank: Ingest raw time-domain filters, dynamically partition by length,
automatically select optimal FFT block sizes, and filter continuous series."""

import math
import os
import time
from typing import Any, NamedTuple, Optional, Sequence, Union, Tuple, List, Dict
import numpy as np
try:
    from . import _core
except ImportError:
    _core = None



class FilterResults(NamedTuple):
    template_indices: np.ndarray   # int64: index into original input templates
    sample_indices: np.ndarray     # int64: sample index in continuous series
    snr: np.ndarray                # complex64: peak complex SNR
    block_starts: np.ndarray       # int64: start sample index of the block
    block_lengths: np.ndarray      # int64: FFT block length used for this template


def _partition_templates(
    counts: np.ndarray,
    max_batch: Optional[int] = None,
    candidate_ns: Sequence[int] = (2048, 4096, 8192, 16384, 32768, 65536),
    engine: Optional[str] = None,
    device: Optional[Any] = None,
    **kwargs: Any,
) -> Tuple[List[Tuple[int, int, int, int]], np.ndarray]:
    """Partition templates sorted by length into homogeneous, balanced sub-batches.

    Avoids over-fragmentation by keeping sub-batches sized according to the L2 cache
    budget (up to 256 templates fitting inside 512 KB L2 cache) when max_batch is None, or
    bounded by max_batch if explicitly specified. Selects FFT block sizes based on
    filter length to guarantee high efficiency (valid fraction >= 50%) while
    maximizing L1/L2 cache hit rates and SIMD lane utilization.

    Returns:
        (groups, sort_order)
        where each group is a tuple: (start_idx, end_idx, chosen_N, max_tap_count).
    """
    counts = np.asarray(counts, dtype=np.int64)
    order = np.argsort(counts)
    sorted_counts = counts[order]
    M = len(sorted_counts)
    if M == 0:
        return [], order

    valid_ns = sorted(int(n) for n in candidate_ns)

    min_cand = valid_ns[0] if valid_ns else 1024

    def pick_n(max_c: int) -> int:
        for n in valid_ns:
            if n > max_c and (n - max_c) / n >= 0.50:
                return n
        for n in reversed(valid_ns):
            if n > max_c:
                return n
        return 1 << int(math.ceil(math.log2(max(min_cand, 2 * max_c))))

    # Partition contiguous runs sharing the same chosen FFT block size,
    # then split each run into balanced sub-batches sized to the cache budget.
    # This guarantees that all M templates are included without dropping any.
    groups = []
    run_start = 0
    while run_start < M:
        current_n = pick_n(int(sorted_counts[run_start]))
        run_end = run_start + 1
        while run_end < M and pick_n(int(sorted_counts[run_end])) == current_n:
            run_end += 1

        if max_batch is None:
            # Sized to stay resident within 1 MB L2 cache per core:
            # coarse template memory = b * sizeof(complex64) = (current_n // 8) * 8 bytes = current_n bytes.
            batch_target = min(256, max(32, 1048576 // (max(64, current_n // 8) * 8)))
        else:
            batch_target = int(max_batch)

        run_len = run_end - run_start
        k_run = math.ceil(run_len / batch_target)
        sub_i = run_start
        for k in range(k_run):
            rem = k_run - k
            target_sz = (run_end - sub_i + rem - 1) // rem
            sub_j = min(run_end, sub_i + target_sz)
            max_c = int(sorted_counts[sub_j - 1])
            groups.append((sub_i, sub_j, current_n, max_c))
            sub_i = sub_j

        run_start = run_end
    return groups, order


_REF_PROFILE_CACHE: Dict[Tuple[int, int, float, float, float], np.ndarray] = {}
_REF_BINNED_CACHE: Dict[Tuple[int, int, float], np.ndarray] = {}


class _TemplateGroup:
    """Internal container for a homogeneous batch of templates sharing an FFT size."""

    def __init__(self, plan, n, template_indices, c_bad, n_valid, spectra, orig_taps_max, device=None):
        self.plan = plan
        self.n = int(n)
        self.template_indices = np.asarray(template_indices, dtype=np.int64)
        self.c_bad = int(c_bad)
        self.n_valid = int(n_valid)
        self.spectra = spectra
        self.orig_taps_max = int(orig_taps_max)
        self.device = device
        self.templates_loaded = False
        self._cached_layout: Optional[Tuple[Tuple[int, int, int], np.ndarray, np.ndarray, np.ndarray]] = None
        self._flat_plan: Optional[Any] = None
        self._corr_plan: Optional[Any] = None

    def get_flat_plan(self):
        from . import MatchedFilter, HierarchicalFilter
        if not isinstance(self.plan, HierarchicalFilter):
            return self.plan
        if self._flat_plan is None:
            fp = MatchedFilter(
                self.n, ndata=1, ntemplates=len(self.template_indices),
                device=self.device
            )
            fp.set_templates(self.spectra)
            self._flat_plan = fp
        return self._flat_plan

    def get_correlation_plan(self):
        if self._corr_plan is None:
            from . import CorrelationFilter
            if isinstance(self.plan, CorrelationFilter):
                self._corr_plan = self.plan
            else:
                cp = CorrelationFilter(
                    self.n, ndata=1, ntemplates=len(self.template_indices),
                    device=self.device, valid=(self.c_bad, self.n - self.c_bad)
                )
                cp.set_templates(self.spectra)
                self._corr_plan = cp
        return self._corr_plan



class TimeDomainFilterBank:
    """Filter bank that ingests raw time-domain filters and optimizes blocking dynamically.

    PyCBC passes raw time-domain FIR taps and sample rates.
    TimeDomainFilterBank clusters templates by length, chooses optimal FFT block sizes
    per cluster, handles rate conversion (zero-padding or Nyquist truncation), rolls center
    taps circularly, and executes overlap-save filtering returning trigger coordinates
    directly in continuous series coordinates.
    """

    def __init__(
        self,
        taps: Union[np.ndarray, Sequence[np.ndarray]],
        tap_counts: Optional[Sequence[int]] = None,
        *,
        tap_sample_rate: float = 2048.0,
        data_sample_rate: float = 2048.0,
        engine: str = 'hier',
        threshold: float = 5.0,
        false_dismissal: float = 0.001,
        first_stage_snr: float = 0.0,
        coarse_band_hz: Optional[float] = None,
        device: Optional[str] = None,
        max_batch_size: Optional[int] = None,
        fft_lengths: Optional[Sequence[int]] = None,
        reference: Optional[Any] = None,
        analytic: bool = False,
    ):
        from . import MatchedFilter, HierarchicalFilter

        self.tap_sample_rate = float(tap_sample_rate)
        self.data_sample_rate = float(data_sample_rate)
        self.threshold = float(threshold)
        self.false_dismissal = float(false_dismissal)
        self.first_stage_snr = float(first_stage_snr)
        self.coarse_band_hz = coarse_band_hz
        self.device = device
        self.analytic = bool(analytic)
        self.max_batch_size = int(max_batch_size) if max_batch_size is not None else None

        mode = {'pycbc': 'flat', 'matchedfilter': 'flat',
                'matchedfilter-hierarchical': 'hier',
                'correlation': 'corr', 'corr': 'corr'}.get(engine, engine).lower()
        self.engine = mode

        # Parse inputs
        self._raw_taps = None
        if isinstance(taps, (list, tuple)):
            n_templates = len(taps)
            if tap_counts is None:
                tap_counts = np.array([len(t) for t in taps], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [np.asarray(t, dtype=np.float32) for t in taps]
        elif isinstance(taps, np.ndarray):
            if taps.ndim == 1:
                taps = taps[None, :]
            n_templates = taps.shape[0]
            if tap_counts is None:
                tap_counts = np.full(n_templates, taps.shape[1], dtype=np.int64)
            else:
                tap_counts = np.asarray(tap_counts, dtype=np.int64)
            taps_list = [taps[i, :tap_counts[i]].astype(np.float32) for i in range(n_templates)]
            self._raw_taps = np.ascontiguousarray(taps, dtype=np.float32)
        else:
            self._raw_taps = None
            raise TypeError("taps must be a numpy array or sequence of arrays")

        if len(tap_counts) != n_templates:
            raise ValueError(f"tap_counts length ({len(tap_counts)}) does not match n_templates ({n_templates})")

        self.n_templates = n_templates
        self.tap_counts = tap_counts
        self._taps_list = taps_list


        # Multi-rate scaling: ratio of tap sample rate to data sample rate
        self.rate_ratio = self.tap_sample_rate / self.data_sample_rate
        # Effective tap length in data samples
        self.effective_data_counts = np.ceil(self.tap_counts / self.rate_ratio).astype(np.int64)

        if fft_lengths is None:
            env_lengths = os.environ.get('PYCBC_RATIO_FFT_LENGTH')
            if env_lengths:
                candidate_ns = tuple(sorted(int(x.strip()) for x in env_lengths.split(',') if x.strip()))
            elif self.data_sample_rate <= 1024.0 or self.analytic:
                candidate_ns = (1024, 2048, 4096, 8192, 16384, 32768, 65536)
            else:
                candidate_ns = (2048, 4096, 8192, 16384, 32768, 65536)
        else:
            candidate_ns = tuple(sorted(int(n) for n in fft_lengths))

        # Dynamic partitioning
        raw_groups, order = _partition_templates(
            self.effective_data_counts,
            max_batch=self.max_batch_size,
            candidate_ns=candidate_ns,
            engine=self.engine,
            device=self.device,
        )

        self._groups: List[_TemplateGroup] = []
        self._filters_f_list = [None] * n_templates
        self._block_lengths_arr = np.zeros(n_templates, dtype=np.int64)

        for start_idx, end_idx, chosen_N, _ in raw_groups:
            tmpl_indices = order[start_idx:end_idx]
            T = len(tmpl_indices)
            chosen_N = int(chosen_N)

            orig_taps_max = int(np.max(self.tap_counts[tmpl_indices]))
            l_data_max = int(np.max(self.effective_data_counts[tmpl_indices]))
            c_bad = int(np.ceil((orig_taps_max // 2) / self.rate_ratio))
            n_valid = int(chosen_N - l_data_max + 1)

            # Frequency domain conversion for each template in this group
            spectra = np.zeros((T, chosen_N), dtype=np.complex64)
            has_fast_c = (self.rate_ratio == 1.0 and _core is not None and hasattr(_core, 'taps_to_spectra'))
            used_fast_c = False
            if has_fast_c:
                try:
                    if self._raw_taps is not None and self._raw_taps.shape[1] >= orig_taps_max:
                        group_taps = np.ascontiguousarray(self._raw_taps[tmpl_indices, :orig_taps_max])
                    else:
                        group_taps = np.zeros((T, orig_taps_max), dtype=np.float32)
                        for r, g_idx in enumerate(tmpl_indices):
                            t_arr = self._taps_list[g_idx]
                            cnt = min(int(self.tap_counts[g_idx]), orig_taps_max)
                            group_taps[r, :cnt] = t_arr[:cnt]
                    group_counts = np.ascontiguousarray(self.tap_counts[tmpl_indices], dtype=np.int64)
                    _core.taps_to_spectra(group_taps, group_counts, chosen_N, orig_taps_max, spectra)
                    for row, g_idx in enumerate(tmpl_indices):
                        self._filters_f_list[g_idx] = np.conj(spectra[row])
                        self._block_lengths_arr[g_idx] = chosen_N
                    used_fast_c = True
                except Exception:
                    used_fast_c = False

            if not used_fast_c:
                for row, g_idx in enumerate(tmpl_indices):
                    t_arr = self._taps_list[g_idx]
                    cnt = int(self.tap_counts[g_idx])
                    N_taps = int(round(chosen_N * self.rate_ratio))

                    buf = np.zeros(N_taps, dtype=np.float32)
                    buf[:cnt] = t_arr[:cnt]
                    # Center-tap circular roll alignment
                    buf = np.roll(buf, -(cnt // 2))

                    spec = np.fft.fft(buf).astype(np.complex64)
                    if self.analytic and N_taps > chosen_N:
                        # For an analytic series with positive-frequency support [f_low, f_high) < data Nyquist:
                        # Positive-frequency bins [0, chosen_N) map directly to [0, f_Nyquist) without
                        # negative-frequency mirroring.
                        spec_data = np.ascontiguousarray(spec[:chosen_N])
                    elif N_taps > chosen_N:
                        # Truncate frequencies above data Nyquist (preserving positive and negative bins)
                        spec_data = np.zeros(chosen_N, dtype=np.complex64)
                        spec_data[:chosen_N // 2 + 1] = spec[:chosen_N // 2 + 1]
                        neg_count = chosen_N - (chosen_N // 2 + 1)
                        spec_data[chosen_N // 2 + 1:] = spec[N_taps - neg_count:]
                    elif N_taps < chosen_N:
                        # Zero-pad frequencies above template Nyquist
                        spec_data = np.zeros(chosen_N, dtype=np.complex64)
                        half_taps = N_taps // 2
                        spec_data[:half_taps + 1] = spec[:half_taps + 1]
                        neg_count = N_taps - (half_taps + 1)
                        spec_data[chosen_N - neg_count:] = spec[half_taps + 1:]
                    else:
                        spec_data = spec

                    spectra[row] = spec_data
                    self._filters_f_list[g_idx] = np.conj(spec_data)
                    self._block_lengths_arr[g_idx] = chosen_N

            # Create matchedfilter plan
            if self.engine == 'corr':
                from . import CorrelationFilter
                plan = CorrelationFilter(
                    chosen_N, ndata=1, ntemplates=T,
                    device=self.device, valid=(c_bad, chosen_N - c_bad)
                )
            elif self.engine == 'hier':
                band_bins = None
                if self.coarse_band_hz is not None and self.coarse_band_hz > 0:
                    delta_f = self.data_sample_rate / chosen_N
                    band_bins = int(round(self.coarse_band_hz / delta_f))
                plan = HierarchicalFilter(
                    chosen_N, ndata=1, ntemplates=T,
                    snr=self.threshold, fd=self.false_dismissal,
                    band=band_bins, device=self.device
                )
                if self.first_stage_snr > 0:
                    plan.set_first_stage(self.first_stage_snr)
            else:
                plan = MatchedFilter(
                    chosen_N, ndata=1, ntemplates=T,
                    device=self.device
                )
            grp = _TemplateGroup(
                plan=plan,
                n=chosen_N,
                template_indices=tmpl_indices,
                c_bad=c_bad,
                n_valid=n_valid,
                spectra=spectra,
                orig_taps_max=orig_taps_max,
                device=self.device,
            )
            grp.templates_loaded = False
            if self.engine != 'hier':
                plan.set_templates(spectra)
                grp.templates_loaded = True
                if self.engine == 'corr':
                    grp._corr_plan = plan
            self._groups.append(grp)

        self._template_map = [None] * n_templates
        for g in self._groups:
            for ti_local, global_idx in enumerate(g.template_indices):
                self._template_map[int(global_idx)] = (g, int(ti_local))

        if reference is not None:
            self.set_reference(reference)
            for g in self._groups:
                if not g.templates_loaded:
                    g.plan.set_templates(g.spectra)
                    g.templates_loaded = True
        self._taps_list = None
        self._raw_taps = None

    @property
    def filters_f(self) -> Sequence[np.ndarray]:
        """Sequence of frequency-domain filters for each template."""
        return self._filters_f_list

    @property
    def block_lengths(self) -> np.ndarray:
        """FFT block length assigned to each template."""
        return self._block_lengths_arr

    @property
    def groups(self) -> List[Dict]:
        """Summary of template partitions."""
        return [
            {
                'n': g.n,
                'count': len(g.template_indices),
                'template_indices': g.template_indices,
                'c_bad': g.c_bad,
                'n_valid': g.n_valid,
                'orig_taps_max': g.orig_taps_max,
                'efficiency': g.n_valid / g.n
            }
            for g in self._groups
        ]

    def get_filter_f(self, template_index: int) -> np.ndarray:
        """Return the frequency-domain filter for a specific template."""
        return self._filters_f_list[template_index]

    def get_block_length(self, template_index: int) -> int:
        """Return the FFT block length for a specific template."""
        return int(self._block_lengths_arr[template_index])

    def set_reference(
        self,
        reference: Union[np.ndarray, Dict[int, np.ndarray]],
        delta_f: Optional[float] = None
    ) -> None:
        """Set reference SNR profile across all hierarchical groups.

        Parameters:
            reference:
                - Dict mapping block length N -> 1D reference array of length N, OR
                - 1D array of power spectrum w(f) on fine grid with frequency spacing delta_f, OR
                - 1D reference profile if all groups share the same block size.
            delta_f: Frequency resolution of fine grid (required when reference is w(f)).
        """
        if isinstance(reference, dict):
            for g in self._groups:
                if hasattr(g.plan, 'set_reference') and g.n in reference:
                    g.plan.set_reference(reference[g.n])
            return

        ref_arr = np.asarray(reference, dtype=np.float64)
        if delta_f is not None and float(delta_f) > 0:
            for g in self._groups:
                if hasattr(g.plan, 'set_reference'):
                    b_key = (id(reference), g.n, float(delta_f))
                    ref_input = _REF_BINNED_CACHE.get(b_key)
                    if ref_input is None:
                        delta_f_engine = self.data_sample_rate / g.n
                        ratio = int(round(delta_f_engine / float(delta_f)))
                        if ratio < 1:
                            ratio = 1
                        keep = (len(ref_arr) // ratio) * ratio
                        binned = ref_arr[:keep].reshape(-1, ratio).sum(axis=1)
                        ref_g = np.zeros(g.n, dtype=np.float64)
                        k = min(len(binned), g.n // 2 + 1)
                        ref_g[:k] = binned[:k]
                        tot = ref_g.sum()
                        ref_input = (ref_g / tot).astype(np.float32) if tot > 0 else None
                        if ref_input is not None:
                            _REF_BINNED_CACHE[b_key] = ref_input
                    if ref_input is not None:
                        g.plan.set_reference(ref_input)
        else:
            for g in self._groups:
                if hasattr(g.plan, 'set_reference'):
                    if len(ref_arr) == g.n:
                        g.plan.set_reference(ref_arr.astype(np.float32))

        for g in self._groups:
            if not g.templates_loaded and hasattr(g.plan, 'set_templates'):
                g.plan.set_templates(g.spectra)
                g.templates_loaded = True

    def set_reference_from_template(
        self,
        stilde,
        psd,
        ref_template,
        f_high: Optional[float] = None
    ) -> None:
        """Compute closed-form reference SNR profile and set across all groups."""
        flo = float(getattr(ref_template, 'f_lower', 0.0) or 0.0)
        fhi = float(f_high or 0.0)
        df = float(stilde.delta_f)
        p_key = (id(ref_template), id(psd), flo, fhi, df)
        w = _REF_PROFILE_CACHE.get(p_key)
        if w is None:
            h = np.asarray(ref_template)
            S = np.asarray(psd)
            m = min(len(h), len(S))
            w = np.zeros(m, dtype=np.float64)
            good = S[:m] > 0
            w[good] = (np.abs(h[:m][good]) ** 2) / S[:m][good]
            f = np.arange(m) * df
            w[f < flo] = 0.0
            if fhi > 0:
                w[f > fhi] = 0.0
            _REF_PROFILE_CACHE[p_key] = w
        self.set_reference(w, delta_f=df)

    def filter_series(
        self,
        series: np.ndarray,
        valid_slice: Optional[slice] = None,
        binsize: Optional[int] = None,
        threshold: Optional[float] = None,
        template_index: Optional[int] = None
    ) -> FilterResults:
        """Filter a continuous series across all template groups (or a specific template).

        Parameters:
            series: Continuous data series (e.g. complex reference SNR).
            valid_slice: Analysis window slice(start, stop). None analyzes whole series.
            binsize: Bins per block. Defaults to block size N (1 bin per block).
            threshold: Optional SNR threshold override. None uses bank threshold.
            template_index: Optional single template index to filter.

        Returns:
            FilterResults namedtuple with:
                template_indices: index into original input templates
                sample_indices: sample index in continuous series
                snr: complex peak SNR value
                block_starts: start sample of block containing each trigger
                block_lengths: FFT block length used for each trigger
        """
        ser = np.ascontiguousarray(series, dtype=np.complex64)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = len(ser)

        if valid_slice is not None:
            v_start = 0 if valid_slice.start is None else int(valid_slice.start)
            v_stop = S if valid_slice.stop is None else int(valid_slice.stop)
        else:
            v_start, v_stop = 0, S

        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")

        eff_threshold = self.threshold if threshold is None else float(threshold)

        out_template_indices = []
        out_sample_indices = []
        out_snrs = []
        out_tstarts = []
        out_block_lens = []

        cache_key = (S, v_start, v_stop)

        if template_index is not None:
            if template_index < 0 or template_index >= self.n_templates:
                raise IndexError(f"template_index {template_index} out of range [0, {self.n_templates})")
            target_g, ti_local = self._template_map[template_index]
            work_items = [(target_g, (ti_local, 1))]
        else:
            work_items = [(g, None) for g in self._groups]

        for g, tmpl_arg in work_items:
            if self.engine == 'hier' and (eff_threshold < self.threshold or eff_threshold <= 0.0 or tmpl_arg is not None):
                active_plan = g.get_flat_plan()
            else:
                active_plan = g.plan

            N = g.n
            c_bad = g.c_bad
            N_valid = g.n_valid
            STEP = N_valid

            is_narrow = (template_index is not None) or ((v_stop - v_start) < 4 * N_valid)
            if is_narrow:
                first_b = max(0, int((v_start - c_bad) // STEP))
                last_b = min(max(0, int((S - 1) // STEP)), int((v_stop - 1 - c_bad) // STEP))
                if last_b < first_b:
                    bstarts = np.empty(0, np.uintp)
                    bws = np.empty(0, np.uintp)
                    bwe = np.empty(0, np.uintp)
                else:
                    bstarts_list = []
                    bws_list = []
                    bwe_list = []
                    for b_idx in range(first_b, last_b + 1):
                        t = b_idx * STEP
                        if t >= S:
                            break
                        bvt0 = t + c_bad
                        rs = max(v_start, bvt0)
                        re = min(v_stop, bvt0 + N_valid)
                        if re > rs:
                            bstarts_list.append(t)
                            bws_list.append(rs - t)
                            bwe_list.append(re - t)
                    bstarts = np.asarray(bstarts_list, dtype=np.uintp)
                    bws = np.asarray(bws_list, dtype=np.uintp)
                    bwe = np.asarray(bwe_list, dtype=np.uintp)
            else:
                layout = g._cached_layout
                if layout is None or layout[0] != cache_key:
                    first_block_idx = max(0, int(np.floor((v_start - c_bad) / STEP)))
                    loop_start = first_block_idx * STEP
                    ts = np.arange(loop_start, S, STEP, dtype=np.uintp)

                    bvt0 = ts + c_bad
                    keep = (bvt0 < v_stop) & (bvt0 + N_valid > v_start)
                    if keep.any():
                        last = np.flatnonzero(bvt0 < v_stop)
                        keep &= np.arange(ts.size) <= last[-1]
                    ts = ts[keep]
                    if not ts.size:
                        g._cached_layout = (cache_key, np.empty(0, np.uintp), np.empty(0, np.uintp), np.empty(0, np.uintp))
                        continue

                    rs = np.maximum(v_start, bvt0[keep])
                    re = np.minimum(v_stop, bvt0[keep] + N_valid)
                    good = re > rs
                    bstarts = np.ascontiguousarray(ts[good], dtype=np.uintp)
                    bws = np.ascontiguousarray((rs - ts)[good], dtype=np.uintp)
                    bwe = np.ascontiguousarray((re - ts)[good], dtype=np.uintp)
                    g._cached_layout = (cache_key, bstarts, bws, bwe)
                else:
                    _, bstarts, bws, bwe = layout

            if bstarts.size == 0:
                continue

            data_in = ser

            bs = N if binsize is None else int(binsize)
            if bs >= N:
                groups_bins = [(bstarts, bws, bwe)]
            else:
                bin_counts = ((bwe - bws + bs - 1) // bs).astype(np.int64)
                if len(bstarts) <= 1 or np.all(bin_counts == bin_counts[0]):
                    groups_bins = [(bstarts, bws, bwe)]
                else:
                    groups_bins = []
                    for u_cnt in np.unique(bin_counts):
                        mask = (bin_counts == u_cnt)
                        groups_bins.append((bstarts[mask], bws[mask], bwe[mask]))

            for sub_starts, sub_bws, sub_bwe in groups_bins:
                aidx, aval = active_plan.run_series(
                    data_in, sub_starts, sub_bws, sub_bwe, binsize=bs,
                    threshold=eff_threshold, templates=tmpl_arg, raw=True
                )

                # aidx has shape (nblocks, ntemplates, nbins)
                if tmpl_arg is not None:
                    # Single template filtered (ntemplates == 1)
                    if aidx.ndim == 3 and aidx.shape[2] == 1:
                        ii = aidx[:, 0, 0]
                        bi = np.nonzero(ii >= 0)[0]
                        if bi.size:
                            out_template_indices.append(np.full(bi.size, template_index, dtype=np.int64))
                            out_sample_indices.append(sub_starts[bi] + ii[bi])
                            out_snrs.append(aval[:, 0, 0][bi])
                            out_tstarts.append(sub_starts[bi])
                            out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                    else:
                        bi, _, bini = np.nonzero(aidx >= 0)
                        if bi.size:
                            out_template_indices.append(np.full(bi.size, template_index, dtype=np.int64))
                            out_sample_indices.append(sub_starts[bi] + aidx[bi, 0, bini])
                            out_snrs.append(aval[bi, 0, bini])
                            out_tstarts.append(sub_starts[bi])
                            out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                else:
                    if aidx.ndim == 3 and aidx.shape[2] == 1:
                        ii = aidx[:, :, 0]
                        bi, ti = np.nonzero(ii >= 0)
                        if bi.size:
                            out_template_indices.append(g.template_indices[ti])
                            out_sample_indices.append(sub_starts[bi] + ii[bi, ti])
                            out_snrs.append(aval[:, :, 0][bi, ti])
                            out_tstarts.append(sub_starts[bi])
                            out_block_lens.append(np.full(bi.size, N, dtype=np.int64))
                    else:
                        bi, ti, bini = np.nonzero(aidx >= 0)
                        if bi.size:
                            out_template_indices.append(g.template_indices[ti])
                            out_sample_indices.append(sub_starts[bi] + aidx[bi, ti, bini])
                            out_snrs.append(aval[bi, ti, bini])
                            out_tstarts.append(sub_starts[bi])
                            out_block_lens.append(np.full(bi.size, N, dtype=np.int64))

        if out_template_indices:
            if len(out_template_indices) == 1:
                return FilterResults(
                    template_indices=out_template_indices[0].astype(np.int64, copy=False),
                    sample_indices=out_sample_indices[0].astype(np.int64, copy=False),
                    snr=out_snrs[0].astype(np.complex64, copy=False),
                    block_starts=out_tstarts[0].astype(np.int64, copy=False),
                    block_lengths=out_block_lens[0].astype(np.int64, copy=False),
                )
            return FilterResults(
                template_indices=np.concatenate(out_template_indices).astype(np.int64),
                sample_indices=np.concatenate(out_sample_indices).astype(np.int64),
                snr=np.concatenate(out_snrs).astype(np.complex64),
                block_starts=np.concatenate(out_tstarts).astype(np.int64),
                block_lengths=np.concatenate(out_block_lens).astype(np.int64),
            )
        else:
            return FilterResults(
                template_indices=np.empty(0, dtype=np.int64),
                sample_indices=np.empty(0, dtype=np.int64),
                snr=np.empty(0, dtype=np.complex64),
                block_starts=np.empty(0, dtype=np.int64),
                block_lengths=np.empty(0, dtype=np.int64),
            )

    def correlate_series(
        self,
        series: np.ndarray,
        valid_slice: Optional[slice] = None,
        scales: Optional[Union[np.ndarray, Sequence[float]]] = None,
        template_index: Optional[int] = None,
        out: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Correlate a continuous series across all templates (or a specific template).

        Templates are filtered using their dynamically partitioned FFT block sizes
        for optimal cache and SIMD efficiency. Returns continuous correlation series
        in the original template ordering.

        Parameters:
            series: Continuous data series (1D complex64).
            valid_slice: Optional analysis window slice(start, stop). None analyzes whole series.
            scales: Optional per-template scale factors. Must have length `n_templates`
                    (or 1 / length matching template if `template_index` is specified).
            template_index: Optional single template index to filter. If specified,
                            returns a 1D array of shape `(len(series),)`.
            out: Optional preallocated output array. If `template_index` is None, shape
                 must be `(n_templates, len(series))` and dtype `complex64`. If `template_index`
                 is specified, shape can be `(len(series),)` or `(1, len(series))`.
                 If None, a new array is allocated.

        Returns:
            If `template_index` is None: 2D complex64 array of shape `(n_templates, len(series))`.
            If `template_index` is specified: 1D complex64 array of shape `(len(series),)`.
        """
        from . import _from_any, _automatic_series_layout

        ser = np.ascontiguousarray(_from_any(series), dtype=np.complex64)
        if ser.ndim != 1:
            raise ValueError("series must be a 1D array")
        S = ser.size
        nt = self.n_templates

        if template_index is not None:
            if template_index < 0 or template_index >= nt:
                raise IndexError(f"template_index {template_index} out of range [0, {nt})")
            target_g, ti_local = self._template_map[template_index]
            cplan = target_g.get_correlation_plan()

            if scales is not None:
                sc_arr = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
                if sc_arr.size == nt:
                    single_scale = sc_arr[template_index:template_index + 1]
                elif sc_arr.size == 1:
                    single_scale = sc_arr.ravel()[:1]
                else:
                    raise ValueError(f"scales must have length {nt} or 1 for single template")
            else:
                single_scale = None

            if out is not None:
                if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
                   or not out.flags.c_contiguous or not out.flags.writeable:
                    raise ValueError("out must be a writable C-contiguous complex64 array")
                if out.shape == (S,):
                    out_2d = out.reshape(1, S)
                elif out.shape == (1, S):
                    out_2d = out
                else:
                    raise ValueError(f"out shape {out.shape} must match ({S},) or (1, {S})")
                if valid_slice is not None:
                    out_2d.fill(0)
            else:
                out_2d = np.zeros((1, S), dtype=np.complex64) if valid_slice is not None else np.empty((1, S), dtype=np.complex64)

            st, _, _ = _automatic_series_layout(S, cplan.valid)
            if valid_slice is not None:
                vs = 0 if valid_slice.start is None else int(valid_slice.start)
                ve = S if valid_slice.stop is None else int(valid_slice.stop)
                if vs < 0:
                    vs = max(0, S + vs)
                if ve < 0:
                    ve = max(0, S + ve)
                lo, hi = cplan.valid
                b_start = st + lo
                b_end = np.minimum(st + hi, S)
                keep = (b_start < ve) & (b_end > vs)
                st = st[keep] if keep.any() else np.empty(0, dtype=np.uintp)
            else:
                out_2d[:, :cplan.valid[0]] = 0
                if st.size > 0:
                    last_end = min(S, st[-1] + cplan.valid[1])
                    if last_end < S:
                        out_2d[:, last_end:] = 0

            if cplan._gpu is not None:
                cplan._continuous_gpu(ser, st, ti_local, 1, out_2d)
            else:
                cplan._execution_plan().correlate_series_continuous(
                    ser, st, cplan.valid[0], cplan.valid[1], ti_local, 1, out_2d
                )

            if single_scale is not None:
                np.multiply(out_2d, single_scale[:, None], out=out_2d)

            if out is not None and out.ndim == 1:
                return out
            return out_2d[0] if out is None else out_2d

        # Full bank correlation across all groups
        shape = (nt, S)
        if scales is not None:
            scales_arr = np.ascontiguousarray(_from_any(scales), dtype=np.float32)
            if scales_arr.ndim != 1 or scales_arr.size != nt:
                raise ValueError(f"scales must be a 1D array of length {nt}, got shape {scales_arr.shape}")
        else:
            scales_arr = None

        if out is not None:
            if not isinstance(out, np.ndarray) or out.dtype != np.complex64 \
               or out.shape != shape or not out.flags.c_contiguous \
               or not out.flags.writeable:
                raise ValueError(f"out must be a writable C-contiguous complex64 array of shape {shape}")
            result = out
            if valid_slice is not None:
                result.fill(0)
        else:
            result = np.zeros(shape, dtype=np.complex64) if valid_slice is not None else np.empty(shape, dtype=np.complex64)

        for g in self._groups:
            cplan = g.get_correlation_plan()
            g_indices = g.template_indices
            g_cnt = len(g_indices)
            if g_cnt == 0:
                continue
            g_scales = scales_arr[g_indices] if scales_arr is not None else None

            is_contiguous_slice = (
                (g_indices[-1] - g_indices[0] + 1 == g_cnt) and
                np.array_equal(g_indices, np.arange(g_indices[0], g_indices[0] + g_cnt))
            )

            st, _, _ = _automatic_series_layout(S, cplan.valid)
            if valid_slice is not None:
                vs = 0 if valid_slice.start is None else int(valid_slice.start)
                ve = S if valid_slice.stop is None else int(valid_slice.stop)
                if vs < 0:
                    vs = max(0, S + vs)
                if ve < 0:
                    ve = max(0, S + ve)
                lo, hi = cplan.valid
                b_start = st + lo
                b_end = np.minimum(st + hi, S)
                keep = (b_start < ve) & (b_end > vs)
                st = st[keep] if keep.any() else np.empty(0, dtype=np.uintp)

            if is_contiguous_slice:
                g_dest = result[g_indices[0] : g_indices[0] + g_cnt]
                if valid_slice is None:
                    g_dest[:, :cplan.valid[0]] = 0
                    if st.size > 0:
                        last_end = min(S, st[-1] + cplan.valid[1])
                        if last_end < S:
                            g_dest[:, last_end:] = 0
                if cplan._gpu is not None:
                    cplan._continuous_gpu(ser, st, 0, g_cnt, g_dest)
                else:
                    cplan._execution_plan().correlate_series_continuous(
                        ser, st, cplan.valid[0], cplan.valid[1], 0, g_cnt, g_dest
                    )
                if g_scales is not None:
                    np.multiply(g_dest, g_scales[:, None], out=g_dest)
            else:
                # Group templates are interleaved; use cplan's internal buffer or allocate
                g_tmp = cplan.run_series(ser, valid_slice=valid_slice, scales=g_scales)
                result[g_indices] = g_tmp

        return result

    process_segment = filter_series
