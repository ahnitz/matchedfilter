#ifndef AP_INT16_COARSE_H
#define AP_INT16_COARSE_H

#if defined(__x86_64__) || defined(_M_X64)
#include <immintrin.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include "matchedfilter.h"

#ifdef __cplusplus
extern "C" {
#endif

#if defined(__GNUC__) || defined(__clang__)
#define AP_TARGET_AVX2 __attribute__((target("avx2,fma")))
#else
#define AP_TARGET_AVX2
#endif

static int16_t ap_tw256_re[128] __attribute__((aligned(32)));
static int16_t ap_tw256_im[128] __attribute__((aligned(32)));
static int16_t ap_tw512_re[256] __attribute__((aligned(32)));
static int16_t ap_tw512_im[256] __attribute__((aligned(32)));

static __m128i ap_vtw256_re[128] __attribute__((aligned(32)));
static __m128i ap_vtw256_im[128] __attribute__((aligned(32)));
static __m128i ap_vtw512_re[256] __attribute__((aligned(32)));
static __m128i ap_vtw512_im[256] __attribute__((aligned(32)));

static int16_t ap_bitrev256[256] __attribute__((aligned(32)));
static int16_t ap_bitrev512[512] __attribute__((aligned(32)));
static pthread_once_t ap_int16_init_once = PTHREAD_ONCE_INIT;

static void ap_int16_init_tables(void) {
    for (int k = 0; k < 128; k++) {
        double a = 2.0 * M_PI * k / 256.0;
        int16_t cr = (int16_t)round(cos(a) * 32767.0);
        int16_t ci = (int16_t)round(sin(a) * 32767.0);
        ap_tw256_re[k] = cr;
        ap_tw256_im[k] = ci;
        ap_vtw256_re[k] = _mm_set1_epi16(cr);
        ap_vtw256_im[k] = _mm_set1_epi16(ci);
    }
    for (int k = 0; k < 256; k++) {
        double a = 2.0 * M_PI * k / 512.0;
        int16_t cr = (int16_t)round(cos(a) * 32767.0);
        int16_t ci = (int16_t)round(sin(a) * 32767.0);
        ap_tw512_re[k] = cr;
        ap_tw512_im[k] = ci;
        ap_vtw512_re[k] = _mm_set1_epi16(cr);
        ap_vtw512_im[k] = _mm_set1_epi16(ci);
    }
    for (int i = 0; i < 256; i++) {
        int r = 0;
        for (int b = 0; b < 8; b++) if (i & (1 << b)) r |= (1 << (7 - b));
        ap_bitrev256[i] = (int16_t)r;
    }
    for (int i = 0; i < 512; i++) {
        int r = 0;
        for (int b = 0; b < 9; b++) if (i & (1 << b)) r |= (1 << (8 - b));
        ap_bitrev512[i] = (int16_t)r;
    }
}

AP_TARGET_AVX2 static inline void ap_ifft256_q15_avx2(__m128i *X_re, __m128i *X_im) {
    int half = 128;
    int step = 1;
    for (int s = 0; s < 8; s++) {
        int tw_step = step;
        for (int b = 0; b < 256; b += 2 * half) {
            // First butterfly (k=0) has W = 1.0 (no twiddle multiplication)
            int i0 = b;
            int i1 = i0 + half;
            __m128i u_r = X_re[i0], u_i = X_im[i0];
            __m128i v_r = X_re[i1], v_i = X_im[i1];

            X_re[i0] = _mm_srai_epi16(_mm_add_epi16(u_r, v_r), 1);
            X_im[i0] = _mm_srai_epi16(_mm_add_epi16(u_i, v_i), 1);
            X_re[i1] = _mm_srai_epi16(_mm_sub_epi16(u_r, v_r), 1);
            X_im[i1] = _mm_srai_epi16(_mm_sub_epi16(u_i, v_i), 1);

            for (int k = 1; k < half; k++) {
                i0 = b + k;
                i1 = i0 + half;

                u_r = X_re[i0]; u_i = X_im[i0];
                v_r = X_re[i1]; v_i = X_im[i1];

                X_re[i0] = _mm_srai_epi16(_mm_add_epi16(u_r, v_r), 1);
                X_im[i0] = _mm_srai_epi16(_mm_add_epi16(u_i, v_i), 1);

                __m128i diff_r = _mm_srai_epi16(_mm_sub_epi16(u_r, v_r), 1);
                __m128i diff_i = _mm_srai_epi16(_mm_sub_epi16(u_i, v_i), 1);

                int tw_idx = k * tw_step;
                __m128i vWr = ap_vtw256_re[tw_idx];
                __m128i vWi = ap_vtw256_im[tw_idx];

                __m128i rr = _mm_mulhrs_epi16(diff_r, vWr);
                __m128i ii = _mm_mulhrs_epi16(diff_i, vWi);
                __m128i ri = _mm_mulhrs_epi16(diff_r, vWi);
                __m128i ir = _mm_mulhrs_epi16(diff_i, vWr);

                X_re[i1] = _mm_sub_epi16(rr, ii);
                X_im[i1] = _mm_add_epi16(ri, ir);
            }
        }
        half /= 2;
        step *= 2;
    }
}

AP_TARGET_AVX2 static inline void ap_ifft512_q15_avx2(__m128i *X_re, __m128i *X_im) {
    int half = 256;
    int step = 1;
    for (int s = 0; s < 9; s++) {
        int tw_step = step;
        for (int b = 0; b < 512; b += 2 * half) {
            int i0 = b;
            int i1 = i0 + half;
            __m128i u_r = X_re[i0], u_i = X_im[i0];
            __m128i v_r = X_re[i1], v_i = X_im[i1];

            X_re[i0] = _mm_srai_epi16(_mm_add_epi16(u_r, v_r), 1);
            X_im[i0] = _mm_srai_epi16(_mm_add_epi16(u_i, v_i), 1);
            X_re[i1] = _mm_srai_epi16(_mm_sub_epi16(u_r, v_r), 1);
            X_im[i1] = _mm_srai_epi16(_mm_sub_epi16(u_i, v_i), 1);

            for (int k = 1; k < half; k++) {
                i0 = b + k;
                i1 = i0 + half;

                u_r = X_re[i0]; u_i = X_im[i0];
                v_r = X_re[i1]; v_i = X_im[i1];

                X_re[i0] = _mm_srai_epi16(_mm_add_epi16(u_r, v_r), 1);
                X_im[i0] = _mm_srai_epi16(_mm_add_epi16(u_i, v_i), 1);

                __m128i diff_r = _mm_srai_epi16(_mm_sub_epi16(u_r, v_r), 1);
                __m128i diff_i = _mm_srai_epi16(_mm_sub_epi16(u_i, v_i), 1);

                int tw_idx = k * tw_step;
                __m128i vWr = ap_vtw512_re[tw_idx];
                __m128i vWi = ap_vtw512_im[tw_idx];

                __m128i rr = _mm_mulhrs_epi16(diff_r, vWr);
                __m128i ii = _mm_mulhrs_epi16(diff_i, vWi);
                __m128i ri = _mm_mulhrs_epi16(diff_r, vWi);
                __m128i ir = _mm_mulhrs_epi16(diff_i, vWr);

                X_re[i1] = _mm_sub_epi16(rr, ii);
                X_im[i1] = _mm_add_epi16(ri, ir);
            }
        }
        half /= 2;
        step *= 2;
    }
}

AP_TARGET_AVX2 static inline int ap_binmax_prod_batch_q15(const float *dr, const float *di,
                                                         const float *tr, const float *ti,
                                                         int nlane, size_t n, size_t binsize,
                                                         float thr, ap_peak *out,
                                                         size_t ws, size_t we) {
    (void)binsize;
    pthread_once(&ap_int16_init_once, ap_int16_init_tables);
    if (n != 256 && n != 512) return -1;
    if (nlane < 1 || nlane > 8) return -1;
    if (we > n) we = n;
    if (ws >= we) return 0;

    // 1. Vectorized dynamic range calculation (AVX2 FMA)
    __m256 vmax_d2 = _mm256_setzero_ps();
    for (size_t k = 0; k < n; k += 8) {
        __m256 vr = _mm256_loadu_ps(dr + k);
        __m256 vi = _mm256_loadu_ps(di + k);
        vmax_d2 = _mm256_max_ps(vmax_d2, _mm256_fmadd_ps(vr, vr, _mm256_mul_ps(vi, vi)));
    }
    __m128 d_lo = _mm256_castps256_ps128(vmax_d2);
    __m128 d_hi = _mm256_extractf128_ps(vmax_d2, 1);
    __m128 dm = _mm_max_ps(d_lo, d_hi);
    dm = _mm_max_ps(dm, _mm_movehl_ps(dm, dm));
    dm = _mm_max_ps(dm, _mm_shuffle_ps(dm, dm, 1));
    float max_d2 = _mm_cvtss_f32(dm);

    __m256 vmax_t2 = _mm256_setzero_ps();
    for (size_t k = 0; k < n * 8; k += 8) {
        __m256 vr = _mm256_loadu_ps(tr + k);
        __m256 vi = _mm256_loadu_ps(ti + k);
        vmax_t2 = _mm256_max_ps(vmax_t2, _mm256_fmadd_ps(vr, vr, _mm256_mul_ps(vi, vi)));
    }
    __m128 t_lo = _mm256_castps256_ps128(vmax_t2);
    __m128 t_hi = _mm256_extractf128_ps(vmax_t2, 1);
    __m128 tm = _mm_max_ps(t_lo, t_hi);
    tm = _mm_max_ps(tm, _mm_movehl_ps(tm, tm));
    tm = _mm_max_ps(tm, _mm_shuffle_ps(tm, tm, 1));
    float max_t2 = _mm_cvtss_f32(tm);

    float prod2 = max_d2 * max_t2;
    if (prod2 < 1e-24f) prod2 = 1e-24f;
    float inv_mag = _mm_cvtss_f32(_mm_rsqrt_ss(_mm_set_ss(prod2)));
    float scale = 26000.f * inv_mag;
    float inv_scale = (float)n / scale;

    __m128i X_re[512] __attribute__((aligned(32)));
    __m128i X_im[512] __attribute__((aligned(32)));
    __m256 vscale = _mm256_set1_ps(scale);

    // 2. Fused Matched Filter Product into Q15 (256-bit AVX2)
    for (size_t k = 0; k < n; k++) {
        __m256 d_r = _mm256_set1_ps(dr[k]);
        __m256 d_i = _mm256_set1_ps(di[k]);

        __m256 t_r = _mm256_loadu_ps(tr + k * 8);
        __m256 t_i = _mm256_loadu_ps(ti + k * 8);

        __m256 p_r = _mm256_mul_ps(_mm256_fmsub_ps(d_r, t_r, _mm256_mul_ps(d_i, t_i)), vscale);
        __m256 p_i = _mm256_mul_ps(_mm256_fmadd_ps(d_r, t_i, _mm256_mul_ps(d_i, t_r)), vscale);

        __m256i ir = _mm256_cvtps_epi32(p_r);
        __m256i ii = _mm256_cvtps_epi32(p_i);

        X_re[k] = _mm_packs_epi32(_mm256_castsi256_si128(ir), _mm256_extracti128_si256(ir, 1));
        X_im[k] = _mm_packs_epi32(_mm256_castsi256_si128(ii), _mm256_extracti128_si256(ii, 1));
    }

    // 3. Fast Fixed-Point IFFT
    if (n == 256) {
        ap_ifft256_q15_avx2(X_re, X_im);
    } else {
        ap_ifft512_q15_avx2(X_re, X_im);
    }

    // 4. Vectorized Peak Scan
    float qthr = (thr > 0.f) ? (thr * scale / (float)n) : 0.f;
    int32_t qthr2 = (int32_t)(qthr * qthr);

    __m256i cur_max = _mm256_set1_epi32(qthr2);
    __m256i cur_idx = _mm256_set1_epi32(-1);

    const int16_t *bitrev_tab = (n == 256) ? ap_bitrev256 : ap_bitrev512;

    for (size_t t = ws; t < we; t++) {
        int rev = bitrev_tab[t];
        __m128i r = X_re[rev];
        __m128i i = X_im[rev];

        __m128i lo = _mm_unpacklo_epi16(r, i);
        __m128i hi = _mm_unpackhi_epi16(r, i);

        __m128i m2_lo = _mm_madd_epi16(lo, lo);
        __m128i m2_hi = _mm_madd_epi16(hi, hi);
        __m256i m2 = _mm256_set_m128i(m2_hi, m2_lo);

        __m256i mask = _mm256_cmpgt_epi32(m2, cur_max);
        if (__builtin_expect(_mm256_movemask_ps(_mm256_castsi256_ps(mask)) != 0, 0)) {
            cur_max = _mm256_max_epi32(cur_max, m2);
            __m256i vt = _mm256_set1_epi32((int)t);
            cur_idx = _mm256_blendv_epi8(cur_idx, vt, mask);
        }
    }

    int32_t bmax[8];
    int32_t bidx[8];
    _mm256_storeu_si256((__m256i*)bmax, cur_max);
    _mm256_storeu_si256((__m256i*)bidx, cur_idx);

    for (int l = 0; l < nlane; l++) {
        if (bidx[l] >= 0) {
            out[l].index = bidx[l];
            out[l].magnitude = sqrtf((float)bmax[l]) * inv_scale;
            int rev = bitrev_tab[bidx[l]];
            int16_t r[8], i[8];
            _mm_storeu_si128((__m128i*)r, X_re[rev]);
            _mm_storeu_si128((__m128i*)i, X_im[rev]);
            out[l].re = (float)r[l] * inv_scale;
            out[l].im = (float)i[l] * inv_scale;
        } else {
            out[l].index = -1;
            out[l].magnitude = 0.f;
            out[l].re = 0.f;
            out[l].im = 0.f;
        }
    }
    return 0;
}

#ifdef __cplusplus
}
#endif

#endif /* __x86_64__ */

#endif /* AP_INT16_COARSE_H */
