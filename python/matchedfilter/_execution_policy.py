"""Measured execution choices shared by CPU, Vulkan and Metal.

These rows select scheduling, never calibration or device capability. Missing
coverage returns no override; each executor retains its established default.
Hardware/memory limits always bound the selected group size at execution.
"""
from functools import lru_cache
import json
import os
from pathlib import Path


@lru_cache(maxsize=16)
def _load(path):
    data = json.loads(Path(path).read_text())
    if (not isinstance(data, dict) or set(data) != {'version', 'rules'}
            or type(data.get('version')) is not int or data['version'] != 1
            or not isinstance(data.get('rules'), list)):
        raise ValueError('unsupported execution policy format')
    required = {'id', 'kind', 'device', 'backend', 'operation', 'n', 'band',
                'templates_min', 'templates_max', 'series_group', 'evidence'}
    ids = set()
    for row in data['rules']:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError('execution policy row has missing or unknown fields')
        if any(not isinstance(row[k], str) or not row[k] for k in
               ('id', 'device', 'backend', 'evidence')):
            raise ValueError('execution policy identifiers must be nonempty strings')
        if row['id'] in ids:
            raise ValueError('duplicate execution policy id')
        ids.add(row['id'])
        if row['kind'] not in ('cpu', 'gpu') or row['operation'] not in (
                'hierarchical_series', 'flat_series', 'correlation_series'):
            raise ValueError('unsupported execution policy kind or operation')
        for key in ('n', 'band', 'templates_min', 'templates_max', 'series_group'):
            if type(row[key]) is not int:
                raise ValueError('execution policy sizes must be integers')
        if (row['n'] < 1 or row['band'] < 0 or row['band'] >= row['n']
                or not 1 <= row['templates_min'] <= row['templates_max']
                or not 1 <= row['series_group'] <= 65535):
            raise ValueError('invalid execution policy bounds')
    return data['rules']


@lru_cache(maxsize=128)
def _select_cached(path, device_kind, device_backend, device_name, device_arch, operation, n, band, templates):
    keys = (device_name, *device_arch, '*')
    found = []
    for row in _load(path):
        if (row['kind'] == device_kind and row['backend'] == device_backend
                and row['operation'] == operation and row['n'] == n
                and row['band'] == band and row['templates_min'] <= templates <= row['templates_max']
                and row['device'] in keys):
            found.append((keys.index(row['device']), row))
    if not found:
        return ()
    best = min(rank for rank, row in found)
    matches = [row for rank, row in found if rank == best]
    if len(matches) != 1:
        raise ValueError('ambiguous execution policy rows for this workload')
    row = matches[0]
    return (row['id'], row['series_group'])


def select(device, operation, n, band, templates):
    """Return a measured override; exact device names precede architecture keys.

    MF_EXECUTION_POLICY permits isolated experiments with another table. The
    file is cached per path; use a new process after editing an existing file.
    Equally specific overlapping rows are errors, not order-dependent choices.
    """
    path = os.environ.get('MF_EXECUTION_POLICY') or str(Path(__file__).with_name('execution-policy.json'))
    res = _select_cached(path, device.kind, device.backend, device.name, device.arch,
                         operation, int(n), int(band), int(templates))
    if not res:
        return {}
    return {'id': res[0], 'series_group': res[1]}
