/* The one rule for the environment switches the C reads (python/matchedfilter/_config.py):
   unset or empty gives the default; 0/false/no/off and 1/true/yes/on, in any case and with
   surrounding space, say what they mean. The package refuses any other value at import,
   so from Python the C sees only these; a C-only caller with another value gets the
   default. */
#ifndef AP_ENV_H
#define AP_ENV_H
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

static inline int ap_env_flag(const char *name, int dflt){
  static const char *const on[4] = {"1", "true", "yes", "on"};
  static const char *const off[4] = {"0", "false", "no", "off"};
  const char *e = getenv(name);
  if(!e) return dflt;
  while(*e && isspace((unsigned char)*e)) e++;
  size_t n = strlen(e);
  while(n && isspace((unsigned char)e[n-1])) n--;
  for(int i = 0; i < 4; i++){
    if(n == strlen(on[i]) && !strncasecmp(e, on[i], n)) return 1;
    if(n == strlen(off[i]) && !strncasecmp(e, off[i], n)) return 0;
  }
  return dflt;
}

/* An integer switch: unset, empty or not an integer gives dflt. */
static inline long ap_env_int(const char *name, long dflt){
  const char *e = getenv(name);
  if(!e) return dflt;
  char *end;
  long v = strtol(e, &end, 10);
  if(end == e) return dflt;
  while(*end && isspace((unsigned char)*end)) end++;
  return *end ? dflt : v;
}

/* A text switch: unset or empty gives NULL. */
static inline const char *ap_env_text(const char *name){
  const char *e = getenv(name);
  return (e && *e) ? e : NULL;
}
#endif
