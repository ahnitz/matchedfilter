"""The release builds and checks pyproject's wheel list, and a successful builder must not
silently omit a requested wheel."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'check_wheels', Path(__file__).resolve().parents[1]/'tools/check_wheels.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

PYPROJECT = """
[tool.cibuildwheel]
build = "cp311-* cp314-*"
skip = "*-musllinux_i686 *_i686"
[tool.cibuildwheel.linux]
archs = ["x86_64"]
[tool.cibuildwheel.macos]
archs = ["arm64"]
"""

#: The wheel file each identifier above produces.
WHEELS = {'cp311-manylinux_x86_64': 'manylinux_2_28_x86_64',
          'cp311-musllinux_x86_64': 'musllinux_1_2_x86_64',
          'cp311-macosx_arm64': 'macosx_11_0_arm64',
          'cp314-manylinux_x86_64': 'manylinux_2_28_x86_64',
          'cp314-musllinux_x86_64': 'musllinux_1_2_x86_64',
          'cp314-macosx_arm64': 'macosx_11_0_arm64'}


@pytest.fixture
def pyproject(tmp_path):
    p = tmp_path / 'pyproject.toml'
    p.write_text(PYPROJECT)
    return p


def test_the_matrix_is_pyprojects_wheel_list(pyproject):
    assert sorted(checker.identifiers('*', pyproject)) == sorted(WHEELS)
    jobs = {j['build']: j for j in checker.matrix('*', pyproject)}
    assert jobs['cp311-macosx_arm64'] == {'build': 'cp311-macosx_arm64', 'os': 'macos-14',
                                          'python': '3.11', 'native': True}
    assert jobs['cp314-musllinux_x86_64']['os'] == 'ubuntu-24.04'
    assert not jobs['cp314-musllinux_x86_64']['native']
    assert [j['build'] for j in checker.matrix('cp314-manylinux_x86_64 *-macosx_*', pyproject)] \
        == ['cp314-manylinux_x86_64', 'cp311-macosx_arm64', 'cp314-macosx_arm64']
    assert checker.matrix('cp313-*', pyproject) == []


def test_the_repository_promises_wheels_for_every_supported_python():
    idents = checker.identifiers()
    for minor in range(11, 15):
        for plat in ('manylinux_x86_64', 'musllinux_x86_64', 'macosx_arm64'):
            assert 'cp3%d-%s' % (minor, plat) in idents


def test_release_requires_every_promised_wheel(tmp_path, pyproject):
    out = tmp_path / 'dist'
    out.mkdir()
    for ident, plat in WHEELS.items():
        py = ident.split('-')[0]
        (out / f'matchedfilter-0.1.0a2-{py}-{py}-{plat}.whl').touch()
    assert len(checker.check(out, pyproject)) == len(WHEELS)
    gone = out / 'matchedfilter-0.1.0a2-cp314-cp314-musllinux_1_2_x86_64.whl'
    gone.unlink()
    with pytest.raises(ValueError, match='cp314-musllinux_x86_64'):
        checker.check(out, pyproject)
    # A free-threaded wheel cannot replace the standard CPython wheel.
    gone.with_name(gone.name.replace('-cp314-', '-cp314t-')).touch()
    with pytest.raises(ValueError, match='cp314-musllinux_x86_64'):
        checker.check(out, pyproject)
