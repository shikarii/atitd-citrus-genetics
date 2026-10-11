#pragma once

#include <cstdint>
#include <string>

namespace citrus {
namespace avx2 {

// Check if AVX2 is available at runtime
bool is_available();

// Vectorized display computation: processes 8 values at once
// Fills out[0..n-1] with display(rule, g1[i], g2[i], rround)
void display_avx2(const std::string& rule, const int* g1, const int* g2,
                  int* out, int n, const std::string& rround);

// Vectorized clamp to [0, 1000]
void clamp_avx2(int* values, int n);

// Vectorized log-sum for loglik
// Computes sum(log(x[i] + floor)) for i in [0, n)
double log_sum_avx2(const double* x, int n, double floor_val);

} // namespace avx2
} // namespace citrus
