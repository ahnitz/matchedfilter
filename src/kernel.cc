/* The kernel translation unit.
 *
 * foreach_target.h re-includes this file once per SIMD target Highway can
 * generate for the machine being built for; balanced-inl.h supplies the body
 * each time, specialised to that target's vector width.  HWY_DYNAMIC_DISPATCH
 * then picks one at run time from what the CPU actually reports.
 *
 * That replaces the hand-written __builtin_cpu_supports ladder and the
 * per-ISA compilation groups in setup.py: the set of kernels a build contains
 * is now whatever Highway decided it could compile, and the build file names
 * none of them.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "alloc.h"
#include "env.h"
#include "matchedfilter.h"
#include "backend.h"

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "kernel.cc"
#include "hwy/foreach_target.h"      // must come before highway.h

#include "balanced-inl.h"

#if HWY_ONCE
#include "hwy/targets.h"

namespace ap {
HWY_EXPORT(Backend);

/* MF_ISA names a Highway target -- SSE4, AVX2, AVX3, NEON, EMU128 -- and
   restricts the process to it: it is the baseline the selection starts from and
   returns to (ap_set_target(NULL)), so a run forced to SSE4 stays on SSE4 even when
   a test restores "the default".  Highway already owns both the list of targets in
   this build and the CPU detection, so forcing one is a matter of telling it what to
   consider rather than of keeping a parallel table.  Anything unrecognised is an
   error (ap_isa_init returns -1, and the library has no back end), so a typo in a
   benchmark script cannot quietly measure the default. */
static bool isa_failed = false;
static int64_t baseline = 0;   /* the MF_ISA target, or 0: the hardware's choice */
static int64_t current = 0;    /* what is selected now (0: the baseline's choice) */

static void apply_env(void) {
  const char *e = getenv("MF_ISA");
  if (!e || !*e) return;
  for (int64_t t : hwy::SupportedAndGeneratedTargets()) {
    if (!strcasecmp(e, hwy::TargetName(t))) {
      baseline = current = t;
      hwy::SetSupportedTargetsForTest(t);
      return;
    }
  }
  fprintf(stderr, "matchedfilter: MF_ISA=\"%s\" is not one of:", e);
  for (int64_t t : hwy::SupportedAndGeneratedTargets())
    fprintf(stderr, " %s", hwy::TargetName(t));
  fprintf(stderr, "\n");
  isa_failed = true;
}

static bool env_applied(void) {
  static const bool once = (apply_env(), true);
  return once;
}

/* The dispatch call must be made from INSIDE namespace ap.  With more than
   one target Highway routes through the export table and either spelling
   works, but a single-target build (macOS arm64 has only NEON) falls back to
   HWY_STATIC_DISPATCH, which expands to HWY_STATIC_NAMESPACE::FUNC -- so
   HWY_DYNAMIC_DISPATCH(ap::Backend) becomes N_NEON::ap::Backend where the
   function is ap::N_NEON::Backend, and the build fails on an undeclared
   N_NEON.  Calling it unqualified from in here resolves both ways. */
static const ap_backend *active(void) { return HWY_DYNAMIC_DISPATCH(Backend)(); }

}  // namespace ap

/* MF_ISA applied (once): 0, or -1 when it names no target of this build (the
   library then has no back end).  The extension calls this at import and raises. */
extern "C" int ap_isa_init(void) {
  ap::env_applied();
  return ap::isa_failed ? -1 : 0;
}

/* The targets this build contains that this CPU can also run, widest first -- only
   MF_ISA's when it is set.  Highway owns both halves of that question, so the list
   is asked for rather than kept. */
extern "C" int ap_target_count(void) {
  ap::env_applied();
  return (int)hwy::SupportedAndGeneratedTargets().size();
}

extern "C" const char *ap_target_name(int i) {
  ap::env_applied();
  const auto ts = hwy::SupportedAndGeneratedTargets();
  if (i < 0 || (size_t)i >= ts.size()) return NULL;
  return hwy::TargetName(ts[(size_t)i]);
}

/* Narrow the runtime choice to one target, by name, or restore the baseline (MF_ISA's
   target, else the hardware's choice) when name is NULL.  A name that is not a target
   this process may select -- not in the build, not supported by this CPU, or outside
   MF_ISA's restriction -- returns -1 and leaves the selection as it was.  Existing plans
   keep the kernel they were built with: they hold the back end, not a promise to
   re-dispatch. */
extern "C" int ap_set_target(const char *name) {
  ap::env_applied();
  if (ap::isa_failed) return -1;
  if (!name) {
    ap::current = ap::baseline;
    hwy::SetSupportedTargetsForTest(ap::baseline);
    return 0;
  }
  /* Search the baseline's targets: while a target is forced, SupportedAndGenerated-
     Targets reports only that one, so the search starts from the baseline and the
     previous selection is restored on a miss. */
  hwy::SetSupportedTargetsForTest(ap::baseline);
  for (int64_t t : hwy::SupportedAndGeneratedTargets()) {
    if (!strcasecmp(name, hwy::TargetName(t))) {
      ap::current = t;
      hwy::SetSupportedTargetsForTest(t);
      return 0;
    }
  }
  hwy::SetSupportedTargetsForTest(ap::current);
  return -1;
}

extern "C" const ap_backend *ap_backend_active(void) {
  ap::env_applied();
  if (ap::isa_failed) return NULL;
  return ap::active();
}
#endif
