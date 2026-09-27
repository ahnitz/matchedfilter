"""Measure the cost of successively narrower output requirements.

Matchedfilter times warm public run() calls, including GPU synchronization.
Full output reuses caller-owned storage; peak results include their normal
readback and assembly. All filter bars use the same Gaussian-noise
input and a bank whose power profile matches the reference. FFTW and rocFFT
are full-batch inverse-transform-only baselines: they do less computation
but materialize the correlation. Plan creation and input upload are excluded.

Run: python tools/teaser_figure.py --out docs/assets/teaser.svg
Writes SVG, PNG and the underlying JSON measurements. Requires pyfftw,
matplotlib and either AMD rocFFT/HIP or MLX (on macOS) for the GPU baseline.
"""
import argparse
import ctypes
import json
import os
import platform
import subprocess
from pathlib import Path
import sys
import time

import numpy as np
import matchedfilter as mf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
N, ND, NT = 4096, 16, 512
PAIRS = ND * NT
BUDGETS = (1e-2, 1e-3, 1e-4)
_DETAILS = {}


def _reference():
    from test_api import inspiral_power
    ref = inspiral_power(N)
    rng = np.random.default_rng(19)
    h = (np.sqrt(ref) * np.exp(2j*np.pi*rng.random((NT, N)))).astype(np.complex64)
    h /= np.linalg.norm(h, axis=1, keepdims=True)
    return ref, h


def _case(seed=1):
    rng = np.random.default_rng(seed)
    d = (rng.standard_normal((ND, N)) + 1j*rng.standard_normal((ND, N))).astype(np.complex64)
    return d, _reference()[1]


def _timed(fn, reps):
    """Sustained warmup and block medians; preserve variability for review.

    Three calls were insufficient to establish steady GPU clocks. Blocks
    also avoid giving a microsecond-scale timer sample undue weight. This
    cannot make a concurrently loaded machine suitable for benchmarking.
    """
    until = time.perf_counter() + .5
    while time.perf_counter() < until:
        fn()
    values = []
    counts = []
    for _ in range(reps):
        start = time.perf_counter()
        count = 0
        while time.perf_counter() - start < .05:
            fn()
            count += 1
        values.append((time.perf_counter()-start)*1000/count)
        counts.append(count)
    _timed.details = dict(block_ms=values, calls_per_block=counts,
                          min_ms=min(values), max_ms=max(values))
    return float(np.median(values))


def fftw_ms(reps=7):
    """Full batch, one CPU thread, PATIENT; no inverse-normalization pass."""
    import pyfftw
    # pyFFTW's alignment flag can be 4 even with NEON. Inspect FFTW's own
    # build string where its symbol is available instead of inferring SIMD.
    build = None
    try:
        lib = ctypes.CDLL(pyfftw.pyfftw.__file__)
        build = ctypes.string_at(ctypes.addressof(
            ctypes.c_char.in_dll(lib, 'fftwf_version'))).decode()
    except (OSError, ValueError, AttributeError):
        pass
    _DETAILS['fftw'] = dict(version=pyfftw.fftw_version, build=build,
                             simd_alignment=pyfftw.simd_alignment, compiler=pyfftw.fftw_cc)
    if build and not any(tag in build.lower() for tag in ('neon', 'sse', 'avx', 'vsx', 'altivec', 'simd')):
        print('WARNING: FFTW build has no SIMD tag; check it before comparing speeds',
              file=sys.stderr)
    if sys.platform == 'darwin' and build:
        # pyFFTW 0.15.1 detects x86 SIMD only and forces FFTW_UNALIGNED on
        # ARM, even for aligned arrays and a NEON-enabled library. Use the
        # same library's C API so its planner can actually select NEON.
        return _fftw_native_ms(lib, reps)
    a = pyfftw.empty_aligned((PAIRS, N), dtype='complex64')
    b = pyfftw.empty_aligned((PAIRS, N), dtype='complex64')
    plan = pyfftw.FFTW(a, b, axes=(1,), direction='FFTW_BACKWARD',
                       flags=('FFTW_PATIENT',), threads=1, planning_timelimit=15.0)
    a[:] = _case()[0][0]
    return _timed(plan.execute, reps)


def _fftw_native_ms(lib, reps):
    vp, integer, ip = ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    signatures = {
        'fftwf_malloc': (vp, [ctypes.c_size_t]),
        'fftwf_free': (None, [vp]),
        'fftwf_set_timelimit': (None, [ctypes.c_double]),
        'fftwf_plan_many_dft': (vp, [integer, ip, integer, vp, ip, integer, integer,
                                    vp, ip, integer, integer, integer, ctypes.c_uint]),
        'fftwf_execute': (None, [vp]),
        'fftwf_destroy_plan': (None, [vp]),
    }
    for name, (result, args) in signatures.items():
        function = getattr(lib, name)
        function.restype, function.argtypes = result, args
    if hasattr(lib, 'fftwf_init_threads') and hasattr(lib, 'fftwf_plan_with_nthreads'):
        lib.fftwf_init_threads.argtypes, lib.fftwf_init_threads.restype = [], integer
        lib.fftwf_plan_with_nthreads.argtypes, lib.fftwf_plan_with_nthreads.restype = [integer], None
        if not lib.fftwf_init_threads():
            raise RuntimeError('FFTW thread initialization failed')
        lib.fftwf_plan_with_nthreads(1)
    a = b = plan = None
    try:
        a, b = lib.fftwf_malloc(PAIRS*N*8), lib.fftwf_malloc(PAIRS*N*8)
        if not a or not b:
            raise MemoryError('FFTW benchmark allocation failed')
        lib.fftwf_set_timelimit(15.)
        length = (integer*1)(N)
        # FFTW_BACKWARD=+1, FFTW_PATIENT=32. No normalization or UNALIGNED.
        plan = lib.fftwf_plan_many_dft(1, length, PAIRS, a, None, 1, N,
                                      b, None, 1, N, 1, 32)
        if not plan:
            raise RuntimeError('FFTW could not plan the aligned batch')
        values = np.ctypeslib.as_array((ctypes.c_float*(2*PAIRS*N)).from_address(a))
        values.view(np.complex64).reshape(PAIRS,N)[:] = _case()[0][0]
        lib.fftwf_execute(plan)
        first = np.ctypeslib.as_array((ctypes.c_float*(2*N)).from_address(b)).view(np.complex64)
        np.testing.assert_allclose(first, np.fft.ifft(_case()[0][0].astype(np.complex128))*N,
                                   rtol=3e-5, atol=3e-5)
        _DETAILS['fftw']['interface'] = 'aligned C API; single thread'
        return _timed(lambda: lib.fftwf_execute(plan), reps)
    finally:
        if plan: lib.fftwf_destroy_plan(plan)
        if a: lib.fftwf_free(a)
        if b: lib.fftwf_free(b)


def _filter_ms(kind, device, reps, fd):
    d, h = _case()
    if kind == 'full':
        f = mf.CorrelationFilter(N, ND, NT, device=device)
    elif kind == 'flat':
        f = mf.MatchedFilter(N, ND, NT, device=device)
    else:
        ref, h = _reference()
        f = mf.HierarchicalFilter(N, ND, NT, snr=5.5, fd=fd, device=device)
        f.set_reference(ref)
    f.set_data(d); f.set_templates(h)
    try:
        if kind == 'full':
            output = f.empty_shared((ND, NT, N))
            ms = _timed(lambda: f.run(out=output), reps)
        else:
            ms = _timed(lambda: f.run(binsize=N, threshold=5.5), reps)
        details = {}
        ctx = getattr(f, '_gpu', None)
        if ctx is not None and hasattr(ctx, 'last_gpu_time'):
            durations = []
            for _ in range(9):
                if kind == 'full':
                    f.run(out=output)
                else:
                    f.run(binsize=N, threshold=5.5)
                durations.append(ctx.last_gpu_time * 1000)
            details['device_ms'] = float(np.median(durations))
        _DETAILS[(device, kind, fd)] = details
        if kind == 'hier' and hasattr(f, 'config'):
            _DETAILS[(device, fd)] = {'band': f.config[0], 'taps': f.config[1],
                                      'refine_rate': f.refine_rate}
        return ms
    finally:
        ctx = getattr(f, '_gpu', None)
        if ctx is not None:
            ctx.destroy()


def cpu_ms(kind, reps=7, fd=1e-2):
    return _filter_ms(kind, 'cpu', reps, fd)


def gpu_ms(kind, reps=15, fd=1e-2):
    return _filter_ms(kind, 'gpu', reps, fd)


def rocfft_ms(reps=7):
    """Full-batch in-place rocFFT, amortized sync, initialized resident data."""
    hip = ctypes.CDLL('libamdhip64.so')
    roc = ctypes.CDLL('librocfft.so.0')
    vp, sz, integer = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int
    signatures = {
        'rocfft_plan_create': [ctypes.POINTER(vp), integer, integer, integer, sz,
                               ctypes.POINTER(sz), sz, vp],
        'rocfft_plan_get_work_buffer_size': [vp, ctypes.POINTER(sz)],
        'rocfft_execution_info_create': [ctypes.POINTER(vp)],
        'rocfft_execution_info_set_work_buffer': [vp, vp, sz],
        'rocfft_execute': [vp, ctypes.POINTER(vp), ctypes.POINTER(vp), vp],
        'rocfft_plan_destroy': [vp], 'rocfft_execution_info_destroy': [vp],
        'rocfft_setup': [], 'rocfft_cleanup': []}
    for name, args in signatures.items():
        getattr(roc, name).argtypes = args
        getattr(roc, name).restype = integer
    hip.hipMalloc.argtypes = [ctypes.POINTER(vp), sz]
    hip.hipMemset.argtypes = [vp, integer, sz]
    hip.hipFree.argtypes = [vp]
    hip.hipDeviceSynchronize.argtypes = []
    def checked(value, name):
        if value:
            raise RuntimeError('%s failed: %d' % (name, value))
    plan, buf, work, info = vp(), vp(), vp(), vp()
    checked(roc.rocfft_setup(), 'rocfft_setup')
    try:
        lengths = (sz * 1)(N)
        checked(roc.rocfft_plan_create(ctypes.byref(plan), 0, 1, 0, 1,
                                      lengths, PAIRS, None), 'rocfft_plan_create')
        checked(hip.hipMalloc(ctypes.byref(buf), N*PAIRS*8), 'hipMalloc')
        # Zero is invariant under repeated unnormalized inverse transforms;
        # uninitialized or repeatedly amplified data can become NaN/Inf.
        checked(hip.hipMemset(buf, 0, N*PAIRS*8), 'hipMemset')
        size = sz()
        checked(roc.rocfft_plan_get_work_buffer_size(plan, ctypes.byref(size)), 'work size')
        checked(roc.rocfft_execution_info_create(ctypes.byref(info)), 'execution info')
        if size.value:
            checked(hip.hipMalloc(ctypes.byref(work), size.value), 'work allocation')
            checked(roc.rocfft_execution_info_set_work_buffer(info, work, size), 'work buffer')
        ins = (vp * 1)(buf)
        def batch():
            for _ in range(8):
                checked(roc.rocfft_execute(plan, ins, None, info), 'rocfft_execute')
            checked(hip.hipDeviceSynchronize(), 'hipDeviceSynchronize')
        return _timed(batch, reps) / 8
    finally:
        if info: roc.rocfft_execution_info_destroy(info)
        if plan: roc.rocfft_plan_destroy(plan)
        if work: hip.hipFree(work)
        if buf: hip.hipFree(buf)
        roc.rocfft_cleanup()


def mlx_ms(reps=7):
    """Resident full-batch IFFT; eight queued executions per synchronization.

    MLX owns its result allocations. No product, peak scan or NumPy copy is
    timed, matching the operation scope of the rocFFT reference.
    """
    import mlx.core as mx
    mx.set_default_device(mx.gpu)
    a = mx.zeros((PAIRS, N), dtype=mx.complex64)
    mx.eval(a)
    def batch():
        results = []
        for _ in range(8):
            value = mx.fft.ifft(a, axis=-1, norm='forward')
            mx.async_eval(value)
            results.append(value)
        mx.synchronize()
    return _timed(batch, reps) / 8


def _cpu_name():
    if sys.platform == 'darwin':
        return subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                return line.split(':', 1)[1].strip()
    except OSError:
        pass
    return 'CPU'


def _gpu_name():
    for device in mf.devices():
        if device.kind == 'gpu' and not device.is_software:
            return device.name
    return 'GPU'


def plot(report, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.fonttype': 'none'})
    bg, fg, muted = '#0b0f19', '#e8eef7', '#adb9ca'
    colors = ['#94a3b8', '#818cf8', '#4facfe', '#38ef7d', '#28c4a7', '#50a798']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), facecolor=bg)
    fig.subplots_adjust(left=.06, right=.98, top=.73, bottom=.29, wspace=.22)
    fig.text(.04, .95, f'{PAIRS:,} correlations × {N:,} points', color=fg, size=18, weight='bold')
    fig.text(.04, .90, 'Throughput · higher is better · CPU and GPU use different scales', color=muted, size=11)
    fig.text(.04, .852, 'Same matched-profile bank and Gaussian noise · SNR 5.5 · full lag window', color=muted, size=10)
    for ax, device, name in zip(axes, ['cpu','gpu'], [report['cpu'],report['gpu']]):
        ax.set_facecolor(bg)
        rows = [r for r in report['rows'] if r['device']==device]
        throughput = [PAIRS / (r['ms'] / 1000) for r in rows]
        # Overlay from largest to smallest, all measured from zero. The
        # visible segments are increments, not independent throughputs.
        for i, (row, value) in enumerate(zip(rows[:3], throughput[:3])):
            ax.bar(i, value, color=colors[i], width=.65, zorder=3)
            inside = (i == 2 and min(throughput[3:]) - value < max(throughput)*.18)
            ax.text(i, value*.5 if inside else value,
                    f"{value/1e6:.2f}M/s\n{row['ms']:.2f} ms", ha='center',
                    va='center' if inside else 'bottom', color=bg if inside else fg,
                    size=9 if inside else 10, linespacing=1.4)
        hierarchical = sorted(zip(rows[3:], throughput[3:], colors[3:]),
                              key=lambda item: item[1], reverse=True)
        for row, value, color in hierarchical:
            ax.bar(3.2, value, color=color, width=.8, zorder=3)
            ax.plot([2.64, 2.8], [value, value], color=color, lw=1, zorder=4)
            budget = {1e-2:'10⁻²', 1e-3:'10⁻³', 1e-4:'10⁻⁴'}[row['fd']]
            ax.text(2.58, value, f"{budget}  {value/1e6:.2f}M/s · {row['ms']:.2f} ms",
                    ha='right', va='center', color=fg, size=9)
        ax.set_xlim(-.55, 3.95)
        ax.set_ylim(0, max(throughput)*1.27)
        ax.set_xticks([0, 1, 2, 3.2], [rows[0]['label'], 'Full output', 'Peak only', 'Hierarchical'],
                      color=fg, size=10)
        ax.tick_params(axis='x', length=0, pad=8)
        ax.tick_params(axis='y', colors=muted, labelsize=9)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f'{v/1e6:g}M'))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.grid(axis='y', color='#243044', zorder=0)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.set_title(device.upper() + '  ·  ' + name.split(' w/')[0].replace('AMD ',''),
                     color=fg, size=11, loc='left', pad=16)
    fig.text(.04, .15, 'Each step restricts the result: all lags → one peak per pair → a screened subset. Hierarchical FDR is requested, not measured here.',
             color=muted, size=10)
    baseline = report.get('gpu_baseline', 'rocFFT')
    fig.text(.04, .105, f'FFTW / {baseline}: inverse FFT only. Full: product + inverse FFT + all lags. Peak: product + inverse FFT + maximum.',
             color=muted, size=10)
    fig.text(.04, .06, 'Setup excluded; FFTW PATIENT planning capped at 15 s. Full output reuses caller storage; GPU timing includes synchronization.',
             color=muted, size=9)
    fig.text(.04, .023, report['date'] + ' · single CPU thread · ' + report['cpu'].split(' w/')[0] + ' / ' + report['gpu'],
             color=muted, size=9)
    out = Path(out)
    fig.savefig(out, facecolor=bg)
    if out.suffix == '.svg':
        out.write_text('\n'.join(line.rstrip() for line in out.read_text().splitlines())+'\n')
    fig.savefig(out.with_suffix('.png'), facecolor=bg, dpi=150)
    plt.close(fig)


def plot_comparison(reports, out):
    """Compare two saved teaser runs on common axes within each device panel."""
    shape = lambda r: (r['n'], r['data'], r['templates'], r['snr'])
    if shape(reports[0]) != shape(reports[1]):
        raise ValueError('teaser comparisons require the same workload shape and SNR')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    pairs = reports[0]['data'] * reports[0]['templates']
    bg, fg, muted = '#0b0f19', '#e8eef7', '#adb9ca'
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.6), facecolor=bg)
    fig.subplots_adjust(left=.06, right=.98, top=.78, bottom=.27, wspace=.22)
    fig.text(.04, .94, 'Same teaser workload · CPU and GPU comparison', color=fg, size=19, weight='bold')
    fig.text(.04, .88, f"{pairs:,} correlations × {reports[0]['n']:,} points · single CPU thread · warm public calls",
             color=muted, size=12)
    fig.text(.04, .83, 'Throughput: higher is better. Log scales; CPU and GPU panels have different ranges.',
             color=muted, size=10)
    for ax, device in zip(axes, ('cpu', 'gpu')):
        ax.set_facecolor(bg)
        first = [r for r in reports[0]['rows'] if r['device'] == device]
        keys = [(r['kind'], r['fd']) for r in first]
        for offset, report, color in zip((-.19, .19), reports, ('#4facfe', '#f3b65b')):
            by_key = {(r['kind'], r['fd']): r for r in report['rows'] if r['device'] == device}
            if set(by_key) != set(keys):
                raise ValueError('teaser comparisons require the same output modes and budgets')
            rows = [by_key[k] for k in keys]
            values = [pairs / r['ms'] / 1000 for r in rows]
            label = report.get('comparison_label', report[device].split(' w/')[0])
            bars = ax.bar(np.arange(len(rows))+offset, values, width=.36, color=color, label=label, zorder=3)
            for bar, row in zip(bars, rows):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.07,
                        f"{row['ms']:.2f} ms", ha='center', va='bottom', color=fg, size=8, rotation=35)
        ax.set_yscale('log')
        ax.set_xticks(range(len(first)), ['FFT only*' if r['kind'] == 'baseline' else r['label'] for r in first], color=fg)
        ax.tick_params(axis='y', colors=muted)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'{v:g}M/s'))
        ax.set_ylim(top=ax.get_ylim()[1]*2)
        ax.grid(axis='y', which='both', alpha=.22, color=muted, zorder=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(device.upper(), color=fg, loc='left', weight='bold')
        ax.legend(frameon=False, labelcolor=fg, fontsize=9, loc='upper left')
    fig.text(.04, .16, 'Full → peak avoids writing every lag. Hierarchical additionally skips most full FFTs.', color=fg, size=11)
    fig.text(.04, .11, 'FFT-only references may use different engines. Compare the matchedfilter bars directly.', color=muted, size=10)
    fig.text(.04, .065, 'Hierarchical bars use automatic per-device choices; requested dismissal budgets are not measured here.', color=muted, size=10)
    fig.text(.04, .025, 'Sources: ' + ' / '.join(r.get('comparison_note', r['date']) for r in reports), color=muted, size=10)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=bg)
    fig.savefig(out.with_suffix('.png'), facecolor=bg, dpi=150)
    plt.close(fig)


def main(argv=None):
    from datetime import date
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='docs/assets/teaser.svg')
    ap.add_argument('--compare', nargs=2, metavar='JSON', help='plot two existing teaser reports without benchmarking')
    args = ap.parse_args(argv)
    if args.compare:
        plot_comparison([json.loads(Path(p).read_text()) for p in args.compare], args.out)
        return 0
    baseline, gpu_reference = ('MLX', mlx_ms) if sys.platform == 'darwin' else ('rocFFT', rocfft_ms)
    report = dict(n=N, data=ND, templates=NT, snr=5.5, date=date.today().isoformat(),
                  cpu=_cpu_name(), gpu=_gpu_name(), fftw_planning_limit_seconds=15,
                  gpu_baseline=baseline, cpu_backend=mf.backend(), python=platform.python_version(),
                  numpy=np.__version__, load_average=os.getloadavg() if hasattr(os, 'getloadavg') else None,
                  timing='0.5 s warmup, median of >=50 ms blocks; public API', rows=[])
    for device, baseline, fn, measure in [('cpu','FFTW',fftw_ms,cpu_ms),
                                          ('gpu',baseline,gpu_reference,gpu_ms)]:
        for label, kind, fd in [(baseline+'\nFFT only','baseline',None),
                                ('Full','full',None), ('Peak','flat',None)] + [
                                ('Hier.\n'+{.01:'10⁻²', .001:'10⁻³', .0001:'10⁻⁴'}[fd],'hier',fd) for fd in BUDGETS]:
            ms = fn() if kind=='baseline' else measure(kind, fd=fd or .01)
            row = dict(device=device,label=label,kind=kind,fd=fd,ms=ms,
                       timing=dict(_timed.details))
            if device == 'gpu' and kind == 'baseline':
                # Each GPU reference call executes eight transform batches.
                row['timing']['executions_per_call'] = 8
            if device == 'cpu' and kind == 'baseline':
                row['fftw'] = _DETAILS.get('fftw', {})
            if row['timing']['max_ms'] > 1.25 * row['timing']['min_ms']:
                print('WARNING: >25% timing spread; check competing workloads', file=sys.stderr)
            if kind=='hier': row.update(_DETAILS[(device,fd)])
            if kind != 'baseline': row.update(_DETAILS.get((device,kind,fd or .01), {}))
            report['rows'].append(row)
            print(json.dumps(row), flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')
    plot(report, out)
    print('wrote', out, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
