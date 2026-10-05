#ifndef AP_REFINE_H
#define AP_REFINE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

size_t ap_refine_peaks_decim(
    const float *series,
    size_t s_len,
    const float *raw_taps,
    const int64_t *tap_counts,
    size_t n_templates,
    size_t max_taps,
    const int64_t *in_tmpl,
    const int64_t *in_samp,
    const float *in_snr,
    size_t n_cand,
    float threshold,
    float scalloping_L,
    int decim_stride,
    int64_t *out_tmpl,
    int64_t *out_samp,
    float *out_snr,
    int64_t *out_surv
);

#ifdef __cplusplus
}
#endif

#endif /* AP_REFINE_H */
