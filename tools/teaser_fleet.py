"""Collect the teaser workload on one device, or compare saved machine reports.

Use separate CPU/GPU processes so an unavailable GPU cannot lose CPU results.
All filter timings reuse the public-call implementation in teaser_figure.py.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np
import teaser_figure as teaser
from teaser_labels import cpu_label


# The hierarchy's cost depends on the detection threshold as well as the
# budget: a higher SNR threshold admits a higher coarse gate, so fewer pairs
# survive to refinement. Recording several lets the comparison page select
# one instead of fixing 5.5 for every reader.
SNRS = (5.0, 5.5, 5.75, 6.0, 6.5)
DEFAULT_SNR = 5.5

MODES = [('Full output', 'full', None, None), ('Peak only', 'flat', None, None)] + [
    (f'Hierarchical {fd:g} @ SNR {snr:g}', 'hier', fd, snr)
    for snr in SNRS for fd in teaser.BUDGETS]


def validate(device):
    """Check all full lags and peak phase/index independently before timing."""
    mf = teaser.mf
    rng = np.random.default_rng(132)
    n = teaser.N
    data = (rng.normal(size=(2, n)) + 1j*rng.normal(size=(2, n))).astype('complex64')
    ref, bank = teaser._reference()
    bank = bank[:3].copy()
    # Include a strong injected match for the hierarchy, away from lag zero.
    data[0] += 30 * bank[1] * np.exp(2j*np.pi*np.arange(n)*731/n).astype('complex64')
    expected = np.fft.ifft(data[:, None].astype('complex128') *
                           bank[None].astype('complex128').conj(), axis=-1)*n
    errors = {}
    for kind in ('full', 'flat', 'hier'):
        cls = {'full': mf.CorrelationFilter, 'flat': mf.MatchedFilter,
               'hier': mf.HierarchicalFilter}[kind]
        kwargs = dict(snr=5.5, fd=.01) if kind == 'hier' else {}
        filt = cls(n, 2, 3, device=device, **kwargs)
        try:
            if kind == 'hier':
                filt.set_reference(ref)
            filt.set_data(data)
            filt.set_templates(bank)
            if kind == 'full':
                got = np.asarray(filt.run())
                error = float(np.max(np.abs(got-expected))/np.max(np.abs(expected)))
                assert error < 1e-5, (kind, error)
            else:
                got = filt.run(binsize=n, threshold=5.5 if kind == 'hier' else 0)
                indices = got['index'][..., 0]
                values = got['value'][..., 0]
                peaks = np.argmax(np.abs(expected), axis=-1)
                mask = indices >= 0
                if kind == 'flat':
                    assert mask.all()
                else:
                    assert mask[0, 1], 'hierarchy lost the strong injected match'
                np.testing.assert_array_equal(indices[mask], peaks[mask])
                want = np.take_along_axis(expected, peaks[..., None], axis=-1)[..., 0]
                error = float(np.max(np.abs(values[mask]-want[mask]))/np.max(np.abs(want[mask])))
                assert error < 1e-5, (kind, error)
            errors[kind] = error
        finally:
            ctx = getattr(filt, '_gpu', None)
            if ctx is not None:
                ctx.destroy()
    return errors


def collect(args):
    if args.cpu is not None:
        os.sched_setaffinity(0, {args.cpu})
    devices = teaser.mf.devices()
    report = dict(host=args.host or platform.node().split('.')[0],
                  date=datetime.now(timezone.utc).isoformat(), revision=args.revision,
                  n=teaser.N, data=teaser.ND, templates=teaser.NT, snr=DEFAULT_SNR,
                  snrs=list(SNRS), reference_profile=teaser.REFERENCE_PROFILE,
                  cpu=teaser._cpu_name(), gpu=teaser._gpu_name(),
                  cpu_backend=teaser.mf.backend(), python=platform.python_version(),
                  numpy=np.__version__, platform=platform.platform(),
                  affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
                  load_before=os.getloadavg(), devices=[repr(d) for d in devices],
                  rows=[], errors=[], device=args.device)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    def save():
        report['load_after'] = os.getloadavg()
        out.write_text(json.dumps(report, indent=2)+'\n')
    save()
    if args.device == 'gpu' and not any(d.kind == 'gpu' and not d.is_software for d in devices):
        report['errors'].append('No physical GPU exposed; software rendering excluded')
        save()
        return
    try:
        report['validation'] = validate(args.device)
    except Exception as error:
        report['errors'].append(f'Correctness/capability check failed: {type(error).__name__}: {error}')
        save()
        raise
    baseline = 'FFTW' if args.device == 'cpu' else ('MLX' if sys.platform == 'darwin' else 'rocFFT')
    for label, kind, fd, snr in [(baseline, 'baseline', None, None)] + MODES:
        try:
            if kind == 'baseline':
                fn = {'FFTW': teaser.fftw_ms, 'MLX': teaser.mlx_ms, 'rocFFT': teaser.rocfft_ms}[baseline]
                ms = fn()
            else:
                ms = teaser._filter_ms(kind, args.device, args.reps, fd or .01,
                                       snr if snr is not None else DEFAULT_SNR)
            row = dict(device=args.device, label=label, kind=kind, fd=fd, snr=snr, ms=ms,
                       timing=dict(teaser._timed.details))
            if kind == 'hier':
                hier_info = teaser._DETAILS.get((args.device, fd, snr), teaser._DETAILS.get((args.device, fd), {}))
                row.update(hier_info)
            row.update(teaser._DETAILS.get((args.device, kind, fd or .01), {}))
            if baseline == 'FFTW' and kind == 'baseline':
                row['fftw'] = teaser._DETAILS.get('fftw', {})
            if args.device == 'gpu' and kind == 'baseline':
                row['timing']['executions_per_call'] = 8
                # _timed measured eight queued batches; fn returned ms/8.
                # Keep samples in the same units as the reported median.
                row['timing']['block_ms'] = [v/8 for v in row['timing']['block_ms']]
                row['timing']['min_ms'] /= 8
                row['timing']['max_ms'] /= 8
                row['timing']['block_ms_scope'] = 'per transform batch'
            report['rows'].append(row)
            print(json.dumps(row), flush=True)
        except Exception as error:
            report['errors'].append(f'{label}: {type(error).__name__}: {error}')
            if kind != 'baseline':
                save()
                raise
        save()


def compare(paths, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    plt.rcParams['svg.fonttype'] = 'none'
    saved = [json.loads(Path(p).read_text()) for p in paths]
    reports = [report for item in saved for report in item.get('reports', [item])]
    shapes = {(r['n'], r['data'], r['templates'], r['snr']) for r in reports}
    if len(shapes) != 1:
        raise ValueError('comparison requires the same workload and SNR')
    hosts = list(dict.fromkeys(r['host'] for r in reports))
    if len({(r['host'], r['device']) for r in reports}) != len(reports):
        raise ValueError('provide only one report per host and device')
    n, nd, nt, _ = next(iter(shapes))
    colors = ['#a8b6c9', '#ad9aff', '#55b7ff', '#64e6ac', '#25b995', '#efbb64']
    # The static chart shows one SNR; the interactive page selects others.
    keys = [('baseline', None)] + [(k, fd) for _, k, fd, snr in MODES
            if snr is None or snr == DEFAULT_SNR]
    labels = ['FFT only', 'Full output', 'Peak only', 'Hier. 10⁻²', 'Hier. 10⁻³', 'Hier. 10⁻⁴']
    bg, fg, muted = '#0b0f19', '#e8eef7', '#aebccf'
    fig, axes = plt.subplots(1, 2, figsize=(17, 9), facecolor=bg)
    fig.subplots_adjust(left=.22, right=.98, top=.84, bottom=.17, wspace=.23)
    fig.text(.04, .95, f'{nd*nt:,} correlations × {n:,} points · {len(hosts)}-machine comparison',
             color=fg, weight='bold', size=22)
    fig.text(.04, .90, 'Warm public calls · one CPU thread · higher throughput is better · logarithmic axes',
             color=muted, size=13)
    for ax, device in zip(axes, ('cpu', 'gpu')):
        ax.set_facecolor(bg)
        ticks = []
        for hi, host in enumerate(hosts):
            report = next((r for r in reports if r['host'] == host and r['device'] == device), None)
            rows = {} if report is None else {
            (r['kind'], r['fd']): r for r in report['rows']
            if r.get('snr') in (None, DEFAULT_SNR)}
            name = report.get(device, '') if report else ''
            processor = cpu_label(report['cpu']) if report else host
            if report and report.get('virtualized'):
                processor += ' (VM)'
            ticks.append(processor if device == 'cpu' else name.replace('AMD ', '').replace('Intel(R) ', '').replace('(TM)', ''))
            for ki, key in enumerate(keys):
                row = rows.get(key)
                if row is None:
                    continue
                y = hi + (ki-2.5)*.125
                rate = nd*nt/row['ms']/1000
                label_rate = rate
                ax.barh(y, rate, height=.11, color=colors[ki], zorder=3)
                samples = row.get('timing', {}).get('block_ms', [])
                if samples:
                    low_ms, high_ms = np.percentile(samples, [10, 90])
                    low_rate, high_rate = nd*nt/high_ms/1000, nd*nt/low_ms/1000
                    label_rate = max(rate, high_rate)
                    ax.errorbar(rate, y, xerr=[[max(0, rate-low_rate)], [max(0, high_rate-rate)]],
                                fmt='none', ecolor=fg, elinewidth=.7, zorder=4)
                ax.text(label_rate*1.04, y, f"{row['ms']:.2f} ms", color=fg, va='center', fontsize=7)
            if not rows:
                errors = report.get('errors', []) if report else []
                reason = ('Validation failed' if any('check failed' in e for e in errors)
                          else 'No physical GPU exposed' if device == 'gpu' else 'Unavailable')
                ax.text(.03, hi, reason, transform=ax.get_yaxis_transform(),
                        color=muted, va='center', fontsize=9)
        ax.set_yticks(range(len(hosts)), ticks, color=fg, fontsize=9)
        ax.set_ylim(len(hosts)-.5, -.6)
        ax.set_xscale('log')
        ax.set_xlim(.01, 160)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}M/s'))
        ax.tick_params(axis='x', colors=muted)
        ax.grid(axis='x', color='#263244', which='major', zorder=0)
        ax.set_title(device.upper(), color=fg, loc='left', weight='bold', pad=16)
        for spine in ax.spines.values():
            spine.set_visible(False)
    handles = [plt.Rectangle((0,0),1,1,color=c) for c in colors]
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5,.085), ncol=6,
               frameon=False, labelcolor=fg, fontsize=11)
    fig.text(.04,.055,'Whiskers: timing-block 10th–90th percentiles. Full → peak avoids output traffic; hierarchy also skips FFTs. Configurations vary by device.',color=muted,size=10)
    fig.text(.04,.025,'FFT-only: FFTW on CPU; rocFFT or MLX where available on GPU. Missing references are omitted. Setup/upload excluded; synchronization included.',color=muted,size=10)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=bg)
    fig.savefig(out.with_suffix('.png'), facecolor=bg, dpi=160)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--device', choices=['cpu', 'gpu'], default='cpu')
    parser.add_argument('--host')
    parser.add_argument('--cpu', type=int, help='Linux CPU affinity for repeatability')
    parser.add_argument('--revision', default='unknown')
    parser.add_argument('--reps', type=int, default=9, help='timing blocks per filter mode')
    parser.add_argument('--compare', nargs='+', metavar='JSON')
    args = parser.parse_args(argv)
    if args.reps < 1:
        parser.error('--reps must be positive')
    if args.compare:
        compare(args.compare, args.out)
    else:
        collect(args)


if __name__ == '__main__':
    main()
