#!/usr/bin/env python3
"""Warm public-API overlap-save benchmarks, with output checks.

The ordinary benchmark sweeps spectral ``run()``. This measures the other
common entry point: automatic ``run_series()`` for peak and continuous output.
It reports time per whole series, including GPU synchronization and access to
the returned NumPy array. Setup, template loading, and plan creation are out
of the timed region. No timing threshold is asserted on shared CI runners.
"""
import argparse
import json
import time

import numpy as np

import matchedfilter as mf


def _spectra(shape, rng):
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)).astype(np.complex64)


def _elapsed(call):
    start = time.perf_counter()
    call()
    return time.perf_counter() - start


def _paired_ms(first, second, reps):
    """Interleave paths so clock drift and shared-runner load affect both."""
    first()
    second()
    times = ([], [])
    for i in range(reps):
        order = (0, 1) if i % 2 == 0 else (1, 0)
        for j in order:
            times[j].append(_elapsed((first, second)[j]))
    return tuple(float(np.median(t) * 1000) for t in times)


def _devices():
    yield 'cpu'
    for device in mf.devices():
        if device.kind == 'gpu' and not device.is_software:
            yield str(device)
            break


def peak_series(device, n, reps):
    lo, hi = n // 8, 7 * n // 8
    length = (hi - lo) * 43 + lo
    rng = np.random.default_rng(n)
    series = _spectra((length,), rng)
    templates = _spectra((128, n), rng)
    filt = mf.MatchedFilter(n, ntemplates=128, device=device, valid=(lo, hi))
    filt.set_templates(templates)
    starts = np.arange(0, length - lo, hi - lo, dtype=np.uintp)

    def automatic():
        return filt.run_series(series, binsize=n)

    def explicit():
        return filt.run_series(series, starts, np.full(len(starts), lo),
                               np.full(len(starts), hi), binsize=n)

    expected = explicit().copy()
    index = expected['index']
    np.add(index, starts[:, None, None].astype(np.int64), out=index,
           where=index >= 0)
    actual = automatic().copy()
    np.testing.assert_array_equal(actual['index'], expected['index'])
    np.testing.assert_allclose(actual['value'], expected['value'], rtol=1e-5, atol=1e-5)
    auto_ms, explicit_ms = _paired_ms(automatic, explicit, reps)
    return {'kind': 'peak_series', 'n': n, 'templates': 128,
            'blocks': len(starts), 'series_length': length,
            'automatic_ms': auto_ms, 'explicit_ms': explicit_ms}


def continuous_series(device, length, reps):
    n, lo, hi = 32768, 4000, 28768
    rng = np.random.default_rng(32768)
    series = _spectra((length,), rng)
    taps = rng.standard_normal((6, 8001)).astype(np.float32)
    centered = np.zeros((6, n), np.float32)
    centered[:, (np.arange(8001) - 4000) % n] = taps
    templates = np.fft.fft(centered, axis=-1).astype(np.complex64)
    filt = mf.CorrelationFilter(n, ntemplates=6, device=device, valid=(lo, hi))
    filt.set_templates(templates)
    starts = np.arange(0, length - lo, hi - lo, dtype=np.uintp)
    blocks = np.empty((len(starts), 6, n), np.complex64)
    assembled = np.zeros((6, length), np.complex64)

    def explicit():
        filt.run_series(series, starts, out=blocks)
        for b, start in enumerate(starts):
            end = min(hi, length - int(start))
            assembled[:, int(start) + lo:int(start) + end] = blocks[b, :, lo:end]
        return assembled

    def automatic():
        return filt.run_series(series)

    expected = explicit().copy()
    actual = automatic()
    scale = max(float(np.max(np.abs(expected))), 1.0)
    error = float(np.max(np.abs(actual - expected))) / scale
    if error >= 3e-5:
        raise AssertionError(f'continuous series differs from blocks: {error:.2g}')
    auto_ms, explicit_ms = _paired_ms(automatic, explicit, reps)
    return {'kind': 'continuous_series', 'n': n, 'templates': 6,
            'blocks': len(starts), 'series_length': length,
            'automatic_ms': auto_ms, 'explicit_and_stitch_ms': explicit_ms,
            'max_relative_error': error}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reps', type=int, default=5)
    parser.add_argument('--quick', action='store_true', help='shorter continuous series for CI')
    parser.add_argument('--json', help='write machine-readable results')
    args = parser.parse_args(argv)
    if args.reps < 1:
        parser.error('--reps must be positive')
    rows = []
    for device in _devices():
        for n in (2048, 4096, 8192):
            try:
                row = peak_series(device, n, args.reps)
            except mf.UnsupportedSize:
                continue
            row['device'] = device
            rows.append(row)
            print(json.dumps(row), flush=True)
        row = continuous_series(device, 131072 if args.quick else 1048576, args.reps)
        row['device'] = device
        rows.append(row)
        print(json.dumps(row), flush=True)
    if args.json:
        with open(args.json, 'w') as stream:
            json.dump({'version': mf.__version__, 'reps': args.reps,
                       'rows': rows}, stream, indent=2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
