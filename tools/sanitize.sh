#!/usr/bin/env bash
# Run tests against an AddressSanitizer + UndefinedBehaviorSanitizer build of the extension.
#
#     tools/sanitize.sh [--python PY] [--keep DIR] -- <pytest arguments>
#     tools/sanitize.sh -- tests/test_native_buffers.py
#     tools/sanitize.sh --keep DIR --build-only        # build once into DIR ...
#     tools/sanitize.sh --prebuilt DIR -- <pytest args>  # ... and test from it, many times
#
# Needs a compiler with the ASan and UBSan runtimes (the libasan and libubsan packages);
# it says so and exits 2 where they are missing. Highway comes from third_party/highway
# when checked out, else HIGHWAY_ROOT.
#
# The tree is copied (tracked files plus third_party/highway) into a scratch directory, the
# extension is built there in place at -O3 -g with -fsanitize=address,undefined (without
# use-after-scope, see FLAGS; setup.py's
# own flags still apply; UBSan reports are fatal), and pytest runs from that copy with the
# ASan runtime preloaded into the interpreter, which is not itself built with ASan. Leak
# detection is off: CPython's arenas read as leaks. Exit status is pytest's; a sanitizer
# report aborts the test process, so it fails the run. The verdict line names the build.
set -euo pipefail

PY=${PYTHON:-python3}
KEEP=""
PREBUILT=""
BUILD_ONLY=0
USAGE="usage: $0 [--python PY] [--keep DIR [--build-only] | --prebuilt DIR] -- <pytest args>"
while [ $# -gt 0 ]; do
  case "$1" in
    --python) PY=$2; shift 2 ;;
    --keep) KEEP=$2; shift 2 ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --prebuilt) PREBUILT=$2; shift 2 ;;
    --) shift; break ;;
    *) echo "$USAGE" >&2; exit 2 ;;
  esac
done
# --build-only needs a --keep directory to leave the build in; --prebuilt builds nothing.
if [ "$BUILD_ONLY" = 1 ] && [ -z "$KEEP" ]; then echo "$USAGE" >&2; exit 2; fi
if [ -n "$PREBUILT" ] && { [ -n "$KEEP" ] || [ "$BUILD_ONLY" = 1 ]; }; then
  echo "$USAGE" >&2; exit 2
fi
[ $# -gt 0 ] || set -- tests
PY=$(command -v "$PY" || true)
[ -n "$PY" ] || { echo "sanitize: no python"; exit 2; }
PY=$(realpath "$PY")

ROOT=$(cd "$(dirname "$0")/.." && pwd)
if [ -n "$PREBUILT" ]; then
  WORK=$(cd "$PREBUILT" && pwd)
  ls "$WORK"/python/matchedfilter/_core*.so >/dev/null 2>&1 \
    || { echo "sanitize: no built extension in $WORK"; exit 1; }
  echo "sanitize: testing the build in $WORK"
else
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

# Without use-after-scope checking: it is the one ASan check that triples the build (gcc,
# src/kernel.cc on Zen 5, 2026-10-22: plain 30 s, full 679 s, without it 225 s; on the arm64
# CI runner the full build did not finish in 65 minutes). Every other check stays, at -O3.
FLAGS="-g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined"
FLAGS="$FLAGS -fno-sanitize-address-use-after-scope"
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
[ "$BUILD_ONLY" = 1 ] && { echo "sanitize: build kept in $WORK"; exit 0; }
fi

ASAN_LIB=$(${CC:-cc} -print-file-name=libasan.so)
[ -e "$ASAN_LIB" ] || { echo "sanitize: no libasan.so from ${CC:-cc}"; exit 1; }
cd "$WORK"
T1=$SECONDS
set +e
env LD_PRELOAD="$ASAN_LIB" PYTHONMALLOC=malloc PYTHONPATH="$WORK/python" \
    ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:allocator_may_return_null=1 \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    "$PY" -m pytest -q -p no:cacheprovider "$@"
rc=$?
set -e
echo "sanitize: pytest ran $((SECONDS - T1)) s"
echo "sanitize: pytest rc=$rc ($([ $rc -eq 0 ] && echo clean || echo FAILED))"
exit $rc
