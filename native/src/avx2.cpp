#include "citrus/avx2.h"

#include <cmath>
#include <cstring>

#ifdef _MSC_VER
#include <intrin.h>
#else
#include <cpuid.h>
#include <x86intrin.h>
#endif

#include <immintrin.h>

namespace citrus {
namespace avx2 {

static bool check_avx2() {
#ifdef _MSC_VER
    int info[4];
    __cpuidex(info, 7, 0);
    return (info[1] & (1 << 5)) != 0; // EBX bit 5 = AVX2
#else
    unsigned int eax, ebx, ecx, edx;
    if (__get_cpuid_count(7, 0, &eax, &ebx, &ecx, &edx)) {
        return (ebx & (1 << 5)) != 0;
    }
    return false;
#endif
}

bool is_available() {
    static bool cached = check_avx2();
    return cached;
}

void display_avx2(const std::string& rule, const int* g1, const int* g2,
                  int* out, int n, const std::string& rround) {
    int i = 0;

    if (rule == "mean") {
        if (rround == "halfup") {
            __m256i one = _mm256_set1_epi32(1);
            for (; i + 8 <= n; i += 8) {
                __m256i v1 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g1 + i));
                __m256i v2 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g2 + i));
                __m256i sum = _mm256_add_epi32(v1, v2);
                __m256i result = _mm256_srli_epi32(_mm256_add_epi32(sum, one), 1);
                _mm256_storeu_si256(reinterpret_cast<__m256i*>(out + i), result);
            }
        } else { // floor
            for (; i + 8 <= n; i += 8) {
                __m256i v1 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g1 + i));
                __m256i v2 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g2 + i));
                __m256i sum = _mm256_add_epi32(v1, v2);
                __m256i result = _mm256_srli_epi32(sum, 1);
                _mm256_storeu_si256(reinterpret_cast<__m256i*>(out + i), result);
            }
        }
    } else if (rule == "min") {
        for (; i + 8 <= n; i += 8) {
            __m256i v1 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g1 + i));
            __m256i v2 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g2 + i));
            __m256i result = _mm256_min_epi32(v1, v2);
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(out + i), result);
        }
    } else if (rule == "max") {
        for (; i + 8 <= n; i += 8) {
            __m256i v1 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g1 + i));
            __m256i v2 = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(g2 + i));
            __m256i result = _mm256_max_epi32(v1, v2);
            _mm256_storeu_si256(reinterpret_cast<__m256i*>(out + i), result);
        }
    } else { // "g1"
        if (n >= 8) {
            std::memcpy(out, g1, n * sizeof(int));
            return;
        }
    }

    // Scalar tail
    for (; i < n; ++i) {
        if (rule == "mean") {
            int s = g1[i] + g2[i];
            out[i] = (rround == "halfup") ? (s + 1) / 2 : s / 2;
        } else if (rule == "min") {
            out[i] = std::min(g1[i], g2[i]);
        } else if (rule == "max") {
            out[i] = std::max(g1[i], g2[i]);
        } else {
            out[i] = g1[i];
        }
    }
}

void clamp_avx2(int* values, int n) {
    __m256i zero = _mm256_setzero_si256();
    __m256i max_val = _mm256_set1_epi32(1000);
    int i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256i v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(values + i));
        v = _mm256_max_epi32(v, zero);
        v = _mm256_min_epi32(v, max_val);
        _mm256_storeu_si256(reinterpret_cast<__m256i*>(values + i), v);
    }
    for (; i < n; ++i) {
        if (values[i] < 0) values[i] = 0;
        else if (values[i] > 1000) values[i] = 1000;
    }
}

double log_sum_avx2(const double* x, int n, double floor_val) {
    __m256d sum_vec = _mm256_setzero_pd();
    __m256d floor_vec = _mm256_set1_pd(floor_val);
    int i = 0;

    for (; i + 4 <= n; i += 4) {
        __m256d v = _mm256_loadu_pd(x + i);
        __m256d v_floored = _mm256_add_pd(v, floor_vec);
        // We need log() - AVX2 doesn't have native log, use scalar
        alignas(32) double vals[4];
        _mm256_store_pd(vals, v_floored);
        vals[0] = std::log(vals[0]);
        vals[1] = std::log(vals[1]);
        vals[2] = std::log(vals[2]);
        vals[3] = std::log(vals[3]);
        __m256d log_v = _mm256_load_pd(vals);
        sum_vec = _mm256_add_pd(sum_vec, log_v);
    }

    // Horizontal sum
    alignas(32) double sums[4];
    _mm256_store_pd(sums, sum_vec);
    double total = sums[0] + sums[1] + sums[2] + sums[3];

    // Scalar tail
    for (; i < n; ++i) {
        total += std::log(x[i] + floor_val);
    }

    return total;
}

} // namespace avx2
} // namespace citrus
