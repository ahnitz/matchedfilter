#!/usr/bin/env bash
# Run tests against an AddressSanitizer + UndefinedBehaviorSanitizer build of the extension.
#
#     tools/sanitize.sh [--python PY] [--keep DIR] -- <pytest arguments>
#     tools/sanitize.sh -- tests/test_native_buffers.py
#     tools/sanitize.sh --keep DIR --build-only        # build once into DIR ...
#     tools/sanitize.sh --prebuilt DIR -- <pytest args>  # ... and test from it, many times
#     tools/sanitize.sh --prebuilt DIR --gdb -- TEST     # one test under gdb: the native
#                                                        # stack where a signal stops it
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
# detection is off: CPython's arenas read as leaks. handle_abort: any abort() prints ASan's
# native stack, so an abort that prints nothing of its own still says where it came from.
# allow_user_segv_handler=0: pytest's faulthandler would otherwise replace ASan's SEGV handler, so
# a segfault printed only Python's stack (CI, 2026-10-22). Exit status is pytest's; a sanitizer
# report aborts the test process, so it fails the run. The verdict line names the build.
set -euo pipefail

PY=${PYTHON:-python3}
KEEP=""
PREBUILT=""
BUILD_ONLY=0
GDB=0
USAGE="usage: $0 [--python PY] [--keep DIR [--build-only] | --prebuilt DIR [--gdb]] -- <pytest args>"
while [ $# -gt 0 ]; do
  case "$1" in
    --python) PY=$2; shift 2 ;;
    --keep) KEEP=$2; shift 2 ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --prebuilt) PREBUILT=$2; shift 2 ;;
    --gdb) GDB=1; shift ;;
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

# The runtime a sanitized program loads, by asking one: -print-file-name=libasan.so can
# name a linker script (Fedora), which LD_PRELOAD ignores.
printf 'int main(void){return 0;}\n' > "$WORK/asan_probe.c"
${CC:-cc} -fsanitize=address "$WORK/asan_probe.c" -o "$WORK/asan_probe"
ASAN_LIB=$(ldd "$WORK/asan_probe" | awk '/libasan/ {print $3; exit}')
[ -e "$ASAN_LIB" ] || { echo "sanitize: no libasan for ${CC:-cc}"; exit 1; }
# Does this toolchain keep an over-aligned local aligned in ASan's fake stack frames (its
# use-after-return detection)? Some do not (GCC PR 110027), and then any 64-byte-aligned
# local -- which -O3 stores with aligned AVX-512 moves -- faults at random. Nightly
# 2026-10-22, gcc 13 on Ubuntu 24.04: vmovaps to a float[16] in fft() raised SEGV. Where the
# probe fails, use-after-return detection is off for the run and says so; every other check
# stays.
UAR=""
cat > "$WORK/align_probe.c" <<'PROBE'
#include <stdint.h>
#include <stdio.h>
__attribute__((noinline)) int check(volatile int depth){
  _Alignas(64) float t[16];
  int bad = ((uintptr_t)t & 63) != 0;
  if(depth > 0) bad |= check(depth - 1);
  t[0] = (float)depth;
  return bad;
}
int main(void){ int bad = 0; for(int i = 0; i < 64; i++) bad |= check(i % 8); return bad; }
PROBE
${CC:-cc} -O2 -fsanitize=address "$WORK/align_probe.c" -o "$WORK/align_probe"
if ! "$WORK/align_probe"; then
  UAR=":detect_stack_use_after_return=0"
  echo "::notice title=sanitizer toolchain::${CC:-cc} misaligns 64-byte-aligned locals in ASan's fake stack (GCC PR 110027): use-after-return detection is off for this run"
  echo "sanitize: $(${CC:-cc} --version | head -1) misaligns over-aligned locals in ASan's fake stack; detect_stack_use_after_return=0"
fi
cd "$WORK"
T1=$SECONDS
RUN=()
if [ "$GDB" = 1 ]; then
  # gdb stops at the first SIGSEGV/SIGBUS/SIGABRT, before any handler (ASan's or Python's)
  # runs, and prints the native stack there; ASan's own SEGV checks are off for it.
  command -v gdb >/dev/null || { echo "sanitize: --gdb needs gdb"; exit 2; }
  RUN=(gdb -batch -nx -ex "set pagination off" -ex "set startup-with-shell off"
       -ex "handle SIGSEGV stop print" -ex "handle SIGBUS stop print"
       -ex "handle SIGABRT stop print" -ex run -ex "bt 40" -ex "info registers"
       -ex "x/4i \$pc" --args)
fi
# The sanitizers write their reports to files, not to stderr: pytest captures fd 2 into a
# temporary file during each test, and a report written there is lost when the process
# aborts (nightly 2026-10-22: rc=134 and no report). Printed below after the run.
SANLOG="$WORK/sanitizer-logs"
rm -rf "$SANLOG"; mkdir -p "$SANLOG"
set +e
env LD_PRELOAD="$ASAN_LIB" PYTHONMALLOC=malloc PYTHONPATH="$WORK/python" \
    ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:allocator_may_return_null=1:handle_abort=1:handle_segv=1:allow_user_segv_handler=0$UAR:log_path="$SANLOG/asan" \
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:log_path="$SANLOG/ubsan" \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TEST_TIMEOUT_SCALE=10 \
    "${RUN[@]}" "$PY" -m pytest -p no:cacheprovider "$@"
rc=$?
set -e
for f in "$SANLOG"/*; do
  [ -e "$f" ] || continue
  echo "=== sanitizer report $(basename "$f") ==="
  cat "$f"
done
echo "sanitize: pytest ran $((SECONDS - T1)) s"
echo "sanitize: pytest rc=$rc ($([ $rc -eq 0 ] && echo clean || echo FAILED))"
exit $rc
