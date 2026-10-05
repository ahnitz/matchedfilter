#include "refine.h"
#include <math.h>
#include <stdlib.h>

#if (defined(__x86_64__) || defined(_M_X64)) && (defined(__GNUC__) || defined(__clang__))
#include <immintrin.h>

__attribute__((target("avx2,fma")))
static inline void complex_dot_avx2(
    const float *s,
    const float *h,
    size_t cnt,
    float *out_re,
    float *out_im
) {
    __m256 acc0 = _mm256_setzero_ps();
    __m256 acc1 = _mm256_setzero_ps();
    size_t j = 0;

    for (; j + 8 <= cnt; j += 8) {
        __m256 v0 = _mm256_loadu_ps(s + 2 * j);
        __m256 v1 = _mm256_loadu_ps(s + 2 * j + 8);
        __m256 vh = _mm256_loadu_ps(h + j);

        __m128 h_low = _mm256_castps256_ps128(vh);
        __m128 h_hi  = _mm256_extractf128_ps(vh, 1);

        __m256 h_dup0 = _mm256_castps128_ps256(_mm_unpacklo_ps(h_low, h_low));
        h_dup0 = _mm256_insertf128_ps(h_dup0, _mm_unpackhi_ps(h_low, h_low), 1);

        __m256 h_dup1 = _mm256_castps128_ps256(_mm_unpacklo_ps(h_hi, h_hi));
        h_dup1 = _mm256_insertf128_ps(h_dup1, _mm_unpackhi_ps(h_hi, h_hi), 1);

        acc0 = _mm256_fmadd_ps(v0, h_dup0, acc0);
        acc1 = _mm256_fmadd_ps(v1, h_dup1, acc1);
    }

    __m256 acc = _mm256_add_ps(acc0, acc1);
    __m128 lo = _mm256_castps256_ps128(acc);
    __m128 hi = _mm256_extractf128_ps(acc, 1);
    __m128 sum128 = _mm_add_ps(lo, hi);
    __m128 shuf = _mm_shuffle_ps(sum128, sum128, _MM_SHUFFLE(1, 0, 3, 2));
    __m128 total = _mm_add_ps(sum128, shuf);

    float sum_re = _mm_cvtss_f32(total);
    float sum_im = _mm_cvtss_f32(_mm_shuffle_ps(total, total, _MM_SHUFFLE(1, 1, 1, 1)));

    for (; j < cnt; j++) {
        float hj = h[j];
        sum_re += s[2 * j] * hj;
        sum_im += s[2 * j + 1] * hj;
    }

    *out_re = sum_re;
    *out_im = sum_im;
}
#endif

static inline void complex_dot_scalar(
    const float *s,
    const float *h,
    size_t cnt,
    float *out_re,
    float *out_im
) {
    float re = 0.0f;
    float im = 0.0f;
    for (size_t j = 0; j < cnt; j++) {
        float hj = h[j];
        re += s[2 * j] * hj;
        im += s[2 * j + 1] * hj;
    }
    *out_re = re;
    *out_im = im;
}

typedef struct {
    int64_t tmpl_id;
    int64_t samp;
    float mag2;
    float re;
    float im;
    int64_t orig_idx;
} RefinedCandidate;

static int compare_refined_candidates(const void *a, const void *b) {
    const RefinedCandidate *pA = (const RefinedCandidate *)a;
    const RefinedCandidate *pB = (const RefinedCandidate *)b;
    if (pA->tmpl_id != pB->tmpl_id) {
        return (pA->tmpl_id < pB->tmpl_id) ? -1 : 1;
    }
    if (pA->samp != pB->samp) {
        return (pA->samp < pB->samp) ? -1 : 1;
    }
    if (pA->mag2 != pB->mag2) {
        return (pA->mag2 > pB->mag2) ? -1 : 1;
    }
    return 0;
}

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
) {
    if (!series || !raw_taps || !tap_counts || !in_tmpl || !in_samp || !in_snr || n_cand == 0) {
        return 0;
    }

    float thr2 = threshold * threshold;
    float refine_thr = threshold * (1.0f - scalloping_L);
    float refine_thr2 = refine_thr * refine_thr;

    int use_avx2 = 0;
#if (defined(__x86_64__) || defined(_M_X64)) && (defined(__GNUC__) || defined(__clang__))
    if (__builtin_cpu_supports("avx2") && __builtin_cpu_supports("fma")) {
        use_avx2 = 1;
    }
#endif

    RefinedCandidate stack_buf[512];
    RefinedCandidate *cands = stack_buf;
    if (n_cand > 512) {
        cands = (RefinedCandidate *)malloc(n_cand * sizeof(RefinedCandidate));
        if (!cands) {
            cands = stack_buf;
        }
    }
    size_t max_cands = (cands == stack_buf) ? 512 : n_cand;
    size_t n_surv = 0;

    for (size_t idx = 0; idx < n_cand; idx++) {
        int64_t tmpl_id = in_tmpl[idx];
        if (tmpl_id < 0 || (size_t)tmpl_id >= n_templates) continue;

        int64_t m = in_samp[idx];
        int64_t k_even = m * (int64_t)decim_stride;

        float z_even_re = in_snr[2 * idx];
        float z_even_im = in_snr[2 * idx + 1];
        float mag2_even = z_even_re * z_even_re + z_even_im * z_even_im;

        if (mag2_even < refine_thr2) {
            continue;
        }

        size_t cnt = (size_t)tap_counts[tmpl_id];
        if (cnt > max_taps) cnt = max_taps;

        if (cnt == 0) {
            if (mag2_even >= thr2 && n_surv < max_cands) {
                cands[n_surv].tmpl_id = tmpl_id;
                cands[n_surv].samp = k_even;
                cands[n_surv].mag2 = mag2_even;
                cands[n_surv].re = z_even_re;
                cands[n_surv].im = z_even_im;
                cands[n_surv].orig_idx = (int64_t)idx;
                n_surv++;
            }
            continue;
        }

        const float *taps = raw_taps + (size_t)tmpl_id * max_taps;
        int64_t half = (int64_t)(cnt / 2);
        int64_t s_0 = k_even - half;
        int64_t s_m1 = s_0 - 1;
        int64_t s_p1 = s_0 + 1;

        float z0_re = z_even_re, z0_im = z_even_im;
        float zm1_re = 0.0f, zm1_im = 0.0f;
        float zp1_re = 0.0f, zp1_im = 0.0f;

        if (s_0 >= 0 && (size_t)(s_0 + cnt) <= s_len) {
#if (defined(__x86_64__) || defined(_M_X64)) && (defined(__GNUC__) || defined(__clang__))
            if (use_avx2) {
                complex_dot_avx2(series + 2 * s_0, taps, cnt, &z0_re, &z0_im);
            } else
#endif
            {
                complex_dot_scalar(series + 2 * s_0, taps, cnt, &z0_re, &z0_im);
            }
        }

        if (s_m1 >= 0 && (size_t)(s_m1 + cnt) <= s_len) {
#if (defined(__x86_64__) || defined(_M_X64)) && (defined(__GNUC__) || defined(__clang__))
            if (use_avx2) {
                complex_dot_avx2(series + 2 * s_m1, taps, cnt, &zm1_re, &zm1_im);
            } else
#endif
            {
                complex_dot_scalar(series + 2 * s_m1, taps, cnt, &zm1_re, &zm1_im);
            }
        }

        if (s_p1 >= 0 && (size_t)(s_p1 + cnt) <= s_len) {
#if (defined(__x86_64__) || defined(_M_X64)) && (defined(__GNUC__) || defined(__clang__))
            if (use_avx2) {
                complex_dot_avx2(series + 2 * s_p1, taps, cnt, &zp1_re, &zp1_im);
            } else
#endif
            {
                complex_dot_scalar(series + 2 * s_p1, taps, cnt, &zp1_re, &zp1_im);
            }
        }

        float mag0 = z0_re * z0_re + z0_im * z0_im;
        float mag_m1 = zm1_re * zm1_re + zm1_im * zm1_im;
        float mag_p1 = zp1_re * zp1_re + zp1_im * zp1_im;

        int64_t best_k;
        float best_re, best_im, best_mag2;

        if (mag_p1 > mag0 && mag_p1 >= mag_m1) {
            best_k = k_even + 1;
            best_re = zp1_re;
            best_im = zp1_im;
            best_mag2 = mag_p1;
        } else if (mag_m1 > mag0 && mag_m1 > mag_p1) {
            best_k = k_even - 1;
            best_re = zm1_re;
            best_im = zm1_im;
            best_mag2 = mag_m1;
        } else {
            best_k = k_even;
            best_re = z0_re;
            best_im = z0_im;
            best_mag2 = mag0;
        }

        if (best_mag2 >= thr2 && n_surv < max_cands) {
            cands[n_surv].tmpl_id = tmpl_id;
            cands[n_surv].samp = best_k;
            cands[n_surv].mag2 = best_mag2;
            cands[n_surv].re = best_re;
            cands[n_surv].im = best_im;
            cands[n_surv].orig_idx = (int64_t)idx;
            n_surv++;
        }
    }

    if (n_surv == 0) {
        if (cands != stack_buf) free(cands);
        return 0;
    }

    if (n_surv == 1) {
        out_tmpl[0] = cands[0].tmpl_id;
        out_samp[0] = cands[0].samp;
        out_snr[0] = cands[0].re;
        out_snr[1] = cands[0].im;
        out_surv[0] = cands[0].orig_idx;
        if (cands != stack_buf) free(cands);
        return 1;
    }

    /* Sort candidates by template ID, then sample index */
    qsort(cands, n_surv, sizeof(RefinedCandidate), compare_refined_candidates);

    /* Cluster adjacent/duplicate peaks for the same template within cluster_win */
    int64_t cluster_win = (int64_t)(decim_stride * 2);
    size_t out_count = 0;
    size_t i = 0;

    while (i < n_surv) {
        int64_t cur_tmpl = cands[i].tmpl_id;
        size_t best_idx = i;
        float best_mag2 = cands[i].mag2;
        int64_t last_samp = cands[i].samp;

        size_t j = i + 1;
        while (j < n_surv && cands[j].tmpl_id == cur_tmpl &&
               (cands[j].samp - last_samp) <= cluster_win) {
            if (cands[j].mag2 > best_mag2) {
                best_mag2 = cands[j].mag2;
                best_idx = j;
            }
            last_samp = cands[j].samp;
            j++;
        }

        out_tmpl[out_count] = cands[best_idx].tmpl_id;
        out_samp[out_count] = cands[best_idx].samp;
        out_snr[2 * out_count] = cands[best_idx].re;
        out_snr[2 * out_count + 1] = cands[best_idx].im;
        out_surv[out_count] = cands[best_idx].orig_idx;
        out_count++;

        i = j;
    }

    if (cands != stack_buf) free(cands);
    return out_count;
}
