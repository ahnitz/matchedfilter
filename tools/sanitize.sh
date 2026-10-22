#!/usr/bin/env bash
# Run tests against an AddressSanitizer + UndefinedBehaviorSanitizer build of the extension.
#
#     tools/sanitize.sh [--python PY] [--keep DIR] -- <pytest arguments>
#     tools/sanitize.sh -- tests/test_native_buffers.py
#
# Needs a compiler with the ASan and UBSan runtimes (the libasan and libubsan packages);
# it says so and exits 2 where they are missing. Highway comes from third_party/highway
# when checked out, else HIGHWAY_ROOT.
#
# The tree is copied (tracked files plus third_party/highway) into a scratch directory, the
# extension is built there in place at -O3 -g with -fsanitize=address,undefined (setup.py's
# own flags still apply; UBSan reports are fatal), and pytest runs from that copy with the
# ASan runtime preloaded into the interpreter, which is not itself built with ASan. Leak
# detection is off: CPython's arenas read as leaks. Exit status is pytest's; a sanitizer
# report aborts the test process, so it fails the run. The verdict line names the build.
set -euo pipefail

PY=${PYTHON:-python3}
KEEP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --python) PY=$2; shift 2 ;;
    --keep) KEEP=$2; shift 2 ;;
    --) shift; break ;;
    *) echo "usage: $0 [--python PY] [--keep DIR] -- <pytest args>" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || set -- tests
PY=$(command -v "$PY" || true)
[ -n "$PY" ] || { echo "sanitize: no python"; exit 2; }
PY=$(realpath "$PY")

ROOT=$(cd "$(dirname "$0")/.." && pwd)
WORK=${KEEP:-$(mktemp -d "${TMPDIR:-/tmp}/mf-sanitize.XXXXXX")}
mkdir -p "$WORK"
[ -n "$KEEP" ] || trap 'rm -rf "$WORK"' EXIT
echo "sanitize: building $(git -C "$ROOT" rev-parse --short HEAD) in $WORK"
( cd "$ROOT" && git ls-files -z | tar --null -T - -cf - ) | tar -xf - -C "$WORK"
# Highway: the vendored submodule when it is checked out, else HIGHWAY_ROOT (setup.py
# reads it), which must then be set.
if [ -e "$ROOT/third_party/highway/hwy/highway.h" ]; then
  rm -rf "$WORK/third_party/highway"
  cp -a "$ROOT/third_party/highway" "$WORK/third_party/highway"
elif [ -z "${HIGHWAY_ROOT:-}" ]; then
  echo "sanitize: third_party/highway is not checked out; set HIGHWAY_ROOT"; exit 2
fi

FLAGS="-g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined"
# The compiler must link and run a sanitized program: the runtimes (libasan, libubsan) are
# separate packages on most distributions.
printf 'int main(void){return 0;}\n' > "$WORK/probe.c"
if ! ${CC:-cc} $FLAGS "$WORK/probe.c" -o "$WORK/probe" 2>"$WORK/probe.log" || ! "$WORK/probe"; then
  echo "sanitize: ${CC:-cc} cannot build and run an ASan/UBSan program here (install the"
  echo "          libasan and libubsan packages); see $WORK/probe.log"
  exit 2
fi
# LDSHARED: link with the system compiler, not the one a conda Python names (its ld does not
# find the system's sanitizer runtimes).
T0=$SECONDS
( cd "$WORK" && CFLAGS="$FLAGS" CXXFLAGS="$FLAGS" LDFLAGS="-fsanitize=address,undefined" \
    LDSHARED="${CXX:-c++} -shared" "$PY" setup.py build_ext --inplace > build.log 2>&1 ) \
  || { echo "sanitize: build FAILED (see $WORK/build.log)"; exit 1; }
echo "sanitize: built in $((SECONDS - T0)) s"

ASAN_LIB=$(${CC:-cc} -print-file-name=libasan.so)
[ -e "$ASAN_LIB" ] || { echo "sanitize: no libasan.so from ${CC:-cc}"; exit 1; }
cd "$WORK"
set +e
env LD_PRELOAD="$ASAN_LIB" PYTHONMALLOC=malloc PYTHONPATH="$WORK/python" \
    ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:allocator_may_return_null=1 \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    "$PY" -m pytest -q -p no:cacheprovider "$@"
rc=$?
set -e
echo "sanitize: pytest ran $((SECONDS - T0)) s since the build started"
echo "sanitize: pytest rc=$rc ($([ $rc -eq 0 ] && echo clean || echo FAILED))"
exit $rc
