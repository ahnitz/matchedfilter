"""Fail a release build if any promised CPython wheel is missing."""
import argparse
from pathlib import Path


def check(directory, platform):
    wheels = [p.name for p in Path(directory).glob('matchedfilter-*.whl')]
    tags = {'linux-x86_64': ('manylinux', 'musllinux'),
            'macos-arm64': ('macosx',)}[platform]
    arch = 'arm64' if platform == 'macos-arm64' else 'x86_64'
    missing = []
    for minor in range(10, 15):
        for tag in tags:
            if not any(f'-cp3{minor}-cp3{minor}-' in w and
                       tag in w.rsplit('-', 1)[1] and
                       w.endswith(f'_{arch}.whl') for w in wheels):
                missing.append(f'cp3{minor}-{tag}_{arch}')
    if missing:
        raise ValueError('Missing release wheels: ' + ', '.join(missing))
    return wheels


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('--platform', required=True,
                        choices=('linux-x86_64', 'macos-arm64'))
    args = parser.parse_args()
    print('\n'.join(check(args.directory, args.platform)))
