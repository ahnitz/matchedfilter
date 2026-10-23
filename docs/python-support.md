# Python version support

The minimum supported Python is 3.11. Package metadata requires Python >=3.11 and
numpy >=1.23.2 (the first numpy with Python 3.11 wheels). Release wheels cover CPython
3.11–3.15 on Linux x86-64 (manylinux and musllinux) and macOS arm64, the list in
pyproject's `[tool.cibuildwheel]`, and CI tests each of those versions. Free-threaded
builds are not supported. Historical test reports retain the versions they actually
tested.

## History

- 2026-10-23: Python 3.15 added: wheels (cibuildwheel 4.3.4, which builds 3.15 by
  default from 4.2) and CI test jobs, the forced AVX2 target and the widest one.
- 2026-10-21: Python 3.10 dropped. It reaches end of life in October 2026, and support
  was dropped by project decision (docs/robustness-plan.md, decision 1). pycbc's runtime
  asks for numpy 1.16 or newer, and its production environment runs 2.2.3.
- 2026-09-26: Python 3.9 dropped, by project decision after its CI test job failed. The
  failure was reproduced in `test_metal_ownership.py`: its reference-count assertion
  compares a `Counter` containing a zero-count entry with one that omits the entry.
  Python 3.9 considers these unequal; Python 3.10 and newer consider them equal. This
  was a test compatibility issue, not a filtering or GPU ownership defect.
