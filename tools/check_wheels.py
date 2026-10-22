"""The wheels a release ships, read from pyproject's [tool.cibuildwheel], and a check that
a directory holds every one of them.

    python3 tools/check_wheels.py --matrix [SELECT]   the build matrix wheels.yml runs,
                                                      as JSON (SELECT: cibuildwheel
                                                      patterns, default every wheel)
    python3 tools/check_wheels.py DIRECTORY           fail unless DIRECTORY holds every
                                                      promised wheel

pyproject's build, skip and per-platform archs are the one list: the release builds it,
one wheel per job, and the publish job checks it before uploading.
"""
import argparse
import fnmatch
import json
import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / 'pyproject.toml'

#: cibuildwheel platform -> (hosted runner, platform tag families built there).
PLATFORMS = {'linux': ('ubuntu-24.04', ('manylinux', 'musllinux')),
             'macos': ('macos-14', ('macosx',))}


def identifiers(select='*', pyproject=PYPROJECT):
    """The cibuildwheel identifiers (cp312-manylinux_x86_64, ...) pyproject promises,
    narrowed to those matching a pattern in select."""
    cfg = tomllib.loads(Path(pyproject).read_text())['tool']['cibuildwheel']
    build, skip = cfg['build'].split(), cfg.get('skip', '').split()
    pythons = sorted({p.split('-')[0] for p in build})
    out = []
    for platform, (_, families) in PLATFORMS.items():
        for arch in cfg.get(platform, {}).get('archs', ()):
            for py in pythons:
                for family in families:
                    ident = '%s-%s_%s' % (py, family, arch)
                    if (any(fnmatch.fnmatch(ident, p) for p in build)
                            and not any(fnmatch.fnmatch(ident, p) for p in skip)
                            and any(fnmatch.fnmatch(ident, p) for p in select.split())):
                        out.append(ident)
    return out


def matrix(select='*', pyproject=PYPROJECT):
    """One wheels.yml job per identifier: its runner, its Python, and whether the runner
    can install the wheel itself (a musllinux wheel runs only in its build container)."""
    runner = {f: os for os, fams in PLATFORMS.values() for f in fams}
    jobs = []
    for ident in identifiers(select, pyproject):
        py, plat = ident.split('-', 1)
        family = plat.split('_')[0]
        jobs.append({'build': ident, 'os': runner[family],
                     'python': '%s.%s' % (py[2], py[3:]), 'native': family != 'musllinux'})
    return jobs


def check(directory, pyproject=PYPROJECT):
    """The wheel names in directory; ValueError naming each promised wheel that is not
    there (a free-threaded cp314t wheel does not stand in for cp314)."""
    wheels = [p.name for p in Path(directory).glob('matchedfilter-*.whl')]
    missing = []
    for ident in identifiers('*', pyproject):
        py, plat = ident.split('-', 1)
        family, arch = plat.split('_', 1)
        if not any('-%s-%s-' % (py, py) in w and w.rsplit('-', 1)[1].startswith(family)
                   and w.endswith('_%s.whl' % arch) for w in wheels):
            missing.append(ident)
    if missing:
        raise ValueError('Missing release wheels: ' + ', '.join(missing))
    return wheels


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('directory', nargs='?')
    parser.add_argument('--matrix', nargs='?', const='*', metavar='SELECT')
    args = parser.parse_args()
    if args.matrix is not None:
        jobs = matrix(args.matrix)
        if not jobs:
            sys.exit('no promised wheel matches %r' % args.matrix)
        print(json.dumps({'include': jobs}))
    elif args.directory:
        print('\n'.join(check(args.directory)))
    else:
        parser.error('give a directory or --matrix')
