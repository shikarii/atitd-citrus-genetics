#pragma once

#include <array>
#include <cmath>
#include <cstdint>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

namespace citrus {

constexpr int V = 1001;
constexpr double FLOOR = 1e-15;
constexpr double CONVERGENCE_THRESHOLD = 1e-6;
constexpr double PARENT_COIN = 0.5;

// Gene pair: (g1, g2) where g1, g2 in [0, 1000]
using GenePair = std::pair<int, int>;

// Nudge kernel: offsets and their probabilities
struct Kernel {
    std::vector<int64_t> offsets;
    std::vector<double> probs;
};

// Trait row distribution: probability vectors of length V
struct TraitRows {
    std::array<double, V> none{};
    std::array<double, V> s1{};
    std::array<double, V> s2{};
    std::array<double, V> both{};
    bool has_both = false;
};

// Per-child column likelihoods (indexed by child observation)
struct ColLik {
    std::vector<double> none;
    std::vector<double> s1;
    std::vector<double> s2;
    std::vector<double> both;
    bool has_both = false;
};

// Scan result: best loglik and gene pair
struct ScanResult {
    double loglik;
    GenePair genes;
};

// --- Core functions ---

// Compute nudge kernel
Kernel kernel(const std::string& shape, int r);

// Display rule: compute trait value from two genes
int display_scalar(const std::string& rule, int g1, int g2, const std::string& rround);

// Vectorized display for AVX2 (declared in avx2.h)
void display_batch(const std::string& rule, const int* g1, const int* g2,
                   int* out, int n, const std::string& rround);

// Compute trait row distributions
TraitRows trait_rows(const std::string& rule, GenePair a, GenePair b,
                     const Kernel& kern, const std::string& rround,
                     bool need_both = false);

// Index trait rows by child observations to produce column likelihoods
ColLik index_trait_rows(const TraitRows& rows, const int32_t* y_trait, int n_children);

// Compute per-child likelihood
// y: child observations, shape (n_children, 4), row-major
// cols: 4 column likelihood arrays (one per trait)
// mut: "one8", "one_g1", or "indep"
// p: per-gene nudge probability (indep only)
// c: clone fraction
// clone_lik: per-child clone likelihood (n_children), nullptr if no clone
// clone_mode: "exact", "nudged", or "" (none)
std::vector<double> child_lik(
    int n_children,
    const std::array<ColLik, 4>& cols,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik,
    const std::string& clone_mode);

// Compute total log-likelihood (sum of log(child_lik + FLOOR))
double loglik(
    int n_children,
    const std::array<ColLik, 4>& cols,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik,
    const std::string& clone_mode);

// Generate candidate gene pairs for a display rule and observed value
std::vector<std::vector<std::pair<int, int>>> candidates(
    const std::string& rule, int v, const std::string& rround);

// Fused scan: find best gene pair for one parent on one trait
ScanResult scan_parent(
    const int32_t* y,           // child observations, (n_children, 4), row-major
    int n_children,
    int trait_idx,
    const std::string& rule,
    const std::string& rround,
    const Kernel& kern,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik,
    const std::string& clone_mode,
    const std::array<ColLik, 4>& current_cols,
    GenePair current_a,
    GenePair current_b,
    bool is_parent_a,           // true = scanning parent A, false = parent B
    int parent_displayed_value,
    bool need_both);

} // namespace citrus
