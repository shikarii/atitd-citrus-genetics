#include "citrus/model.h"
#include "citrus/avx2.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <numeric>
#include <set>

namespace citrus {

Kernel kernel(const std::string& shape, int r) {
    Kernel k;
    k.offsets.resize(2 * r + 1);
    k.probs.resize(2 * r + 1);
    double sum = 0.0;
    for (int i = 0; i <= 2 * r; ++i) {
        k.offsets[i] = i - r;
        if (shape == "uniform") {
            k.probs[i] = 1.0;
        } else { // triangular
            k.probs[i] = static_cast<double>(r + 1 - std::abs(i - r));
        }
        sum += k.probs[i];
    }
    for (auto& p : k.probs) p /= sum;
    return k;
}

int display_scalar(const std::string& rule, int g1, int g2, const std::string& rround) {
    if (rule == "mean") {
        int s = g1 + g2;
        return (rround == "halfup") ? (s + 1) / 2 : s / 2;
    }
    if (rule == "min") return std::min(g1, g2);
    if (rule == "max") return std::max(g1, g2);
    return g1; // "g1"
}

void display_batch(const std::string& rule, const int* g1, const int* g2,
                   int* out, int n, const std::string& rround) {
    if (avx2::is_available() && n >= 8) {
        avx2::display_avx2(rule, g1, g2, out, n, rround);
        return;
    }
    // Scalar fallback
    for (int i = 0; i < n; ++i) {
        out[i] = display_scalar(rule, g1[i], g2[i], rround);
    }
}

TraitRows trait_rows(const std::string& rule, GenePair a, GenePair b,
                     const Kernel& kern, const std::string& rround,
                     bool need_both) {
    TraitRows rows;
    rows.has_both = need_both;
    std::memset(rows.none.data(), 0, V * sizeof(double));
    std::memset(rows.s1.data(), 0, V * sizeof(double));
    std::memset(rows.s2.data(), 0, V * sizeof(double));
    if (need_both) {
        std::memset(rows.both.data(), 0, V * sizeof(double));
    }

    const int n_offs = static_cast<int>(kern.offsets.size());

    // 4 parent-pair combinations: (a0,a1), (b0,b1), (a0,b1), (b0,a1)
    const std::array<std::pair<int, int>, 4> pairs = {{
        {a.first, a.second},
        {b.first, b.second},
        {a.first, b.second},
        {b.first, a.second}
    }};

    // Preallocate work buffers
    std::vector<int> n1_buf(n_offs);
    std::vector<int> n2_buf(n_offs);
    std::vector<int> g2_full(n_offs);
    std::vector<int> g1_full(n_offs);
    std::vector<int> disp_buf(n_offs);

    for (const auto& [pg1, pg2] : pairs) {
        // "none" case: no nudge
        int d = display_scalar(rule, pg1, pg2, rround);
        rows.none[d] += 0.25;

        // "s1" case: nudge gene 1
        for (int i = 0; i < n_offs; ++i) {
            n1_buf[i] = std::clamp(pg1 + static_cast<int>(kern.offsets[i]), 0, 1000);
            g2_full[i] = pg2;
        }
        display_batch(rule, n1_buf.data(), g2_full.data(), disp_buf.data(), n_offs, rround);
        for (int i = 0; i < n_offs; ++i) {
            rows.s1[disp_buf[i]] += 0.25 * kern.probs[i];
        }

        // "s2" case: nudge gene 2
        for (int i = 0; i < n_offs; ++i) {
            n2_buf[i] = std::clamp(pg2 + static_cast<int>(kern.offsets[i]), 0, 1000);
            g1_full[i] = pg1;
        }
        display_batch(rule, g1_full.data(), n2_buf.data(), disp_buf.data(), n_offs, rround);
        for (int i = 0; i < n_offs; ++i) {
            rows.s2[disp_buf[i]] += 0.25 * kern.probs[i];
        }

        // "both" case: nudge both genes
        if (need_both) {
            for (int i = 0; i < n_offs; ++i) {
                for (int j = 0; j < n_offs; ++j) {
                    int d_both = display_scalar(rule, n1_buf[i], n2_buf[j], rround);
                    rows.both[d_both] += 0.25 * kern.probs[i] * kern.probs[j];
                }
            }
        }
    }

    return rows;
}

ColLik index_trait_rows(const TraitRows& rows, const int32_t* y_trait, int n_children) {
    ColLik col;
    col.none.resize(n_children);
    col.s1.resize(n_children);
    col.s2.resize(n_children);
    col.has_both = rows.has_both;
    if (rows.has_both) {
        col.both.resize(n_children);
    }

    for (int i = 0; i < n_children; ++i) {
        int v = y_trait[i];
        col.none[i] = rows.none[v];
        col.s1[i] = rows.s1[v];
        col.s2[i] = rows.s2[v];
        if (rows.has_both) {
            col.both[i] = rows.both[v];
        }
    }
    return col;
}

std::vector<double> child_lik(
    int n_children,
    const std::array<ColLik, 4>& cols,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik,
    const std::string& clone_mode) {

    std::vector<double> big_l(n_children);

    if (mut == "indep") {
        // big_l = product over traits of:
        //   (1-p)^2 * none + p*(1-p)*(s1+s2) + p^2 * both
        double q = 1.0 - p;
        double qq = q * q;
        double pq = p * q;
        double pp = p * p;
        std::fill(big_l.begin(), big_l.end(), 1.0);
        for (int t = 0; t < 4; ++t) {
            for (int i = 0; i < n_children; ++i) {
                big_l[i] *= qq * cols[t].none[i]
                          + pq * (cols[t].s1[i] + cols[t].s2[i])
                          + pp * cols[t].both[i];
            }
        }
    } else {
        // one8 or one_g1
        // For each trait t: hit[t] = (s1+s2)/8 (one8) or s1/4 (one_g1)
        // big_l = sum_t hit[t] * prod(none[u] for u != t)
        //
        // Optimized: precompute none_product = prod(none[t] for all t)
        // then big_l = sum_t hit[t] * none_product / none[t]
        // But division by zero when none[t] == 0, so use the safe approach:
        // precompute prefix and suffix products

        // Compute none products excluding each trait using prefix/suffix
        // none_excl[t][i] = product of none[u][i] for u != t
        std::vector<double> prefix(n_children, 1.0);
        std::vector<double> suffix(n_children, 1.0);
        std::array<std::vector<double>, 4> none_excl;
        for (int t = 0; t < 4; ++t) {
            none_excl[t].resize(n_children);
        }

        // Prefix products: prefix[t] = product of none[0..t-1]
        // We'll compute none_excl directly
        // none_excl[0] = none[1] * none[2] * none[3]
        // none_excl[1] = none[0] * none[2] * none[3]
        // none_excl[2] = none[0] * none[1] * none[3]
        // none_excl[3] = none[0] * none[1] * none[2]
        for (int i = 0; i < n_children; ++i) {
            double n0 = cols[0].none[i], n1 = cols[1].none[i];
            double n2 = cols[2].none[i], n3 = cols[3].none[i];
            none_excl[0][i] = n1 * n2 * n3;
            none_excl[1][i] = n0 * n2 * n3;
            none_excl[2][i] = n0 * n1 * n3;
            none_excl[3][i] = n0 * n1 * n2;
        }

        std::fill(big_l.begin(), big_l.end(), 0.0);
        if (mut == "one8") {
            for (int t = 0; t < 4; ++t) {
                for (int i = 0; i < n_children; ++i) {
                    double hit = (cols[t].s1[i] + cols[t].s2[i]) / 8.0;
                    big_l[i] += hit * none_excl[t][i];
                }
            }
        } else { // one_g1
            for (int t = 0; t < 4; ++t) {
                for (int i = 0; i < n_children; ++i) {
                    double hit = cols[t].s1[i] / 4.0;
                    big_l[i] += hit * none_excl[t][i];
                }
            }
        }
    }

    // Clone component
    if (!clone_mode.empty() && clone_lik != nullptr && c > 0.0) {
        if (clone_mode == "exact") {
            for (int i = 0; i < n_children; ++i) {
                big_l[i] = (1.0 - c) * big_l[i] + c * clone_lik[i];
            }
        }
        // "nudged" clone mode is handled at the Python level
        // since it requires calling trait_rows with self-genes
    }

    return big_l;
}

double loglik(
    int n_children,
    const std::array<ColLik, 4>& cols,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik,
    const std::string& clone_mode) {

    auto liks = child_lik(n_children, cols, mut, p, c, clone_lik, clone_mode);

    if (avx2::is_available()) {
        return avx2::log_sum_avx2(liks.data(), n_children, FLOOR);
    }

    double sum = 0.0;
    for (int i = 0; i < n_children; ++i) {
        sum += std::log(liks[i] + FLOOR);
    }
    return sum;
}

std::vector<std::vector<std::pair<int, int>>> candidates(
    const std::string& rule, int v, const std::string& rround) {

    std::vector<std::vector<std::pair<int, int>>> groups;

    if (rule == "mean") {
        int s0 = (rround == "halfup") ? (2 * v - 1) : (2 * v);
        int s1 = (rround == "halfup") ? (2 * v) : (2 * v + 1);
        for (int s : {s0, s1}) {
            if (s < 0 || s > 2000) continue;
            std::vector<std::pair<int, int>> grp;
            int lo = std::max(0, s - 1000);
            int hi = std::min(1000, s);
            for (int g = lo; g <= hi; ++g) {
                grp.emplace_back(g, s - g);
            }
            groups.push_back(std::move(grp));
        }
    } else if (rule == "min") {
        std::vector<std::pair<int, int>> grp1, grp2;
        for (int h = v; h <= 1000; ++h) {
            grp1.emplace_back(v, h);
            grp2.emplace_back(h, v);
        }
        groups.push_back(std::move(grp1));
        groups.push_back(std::move(grp2));
    } else if (rule == "max") {
        std::vector<std::pair<int, int>> grp1, grp2;
        for (int h = 0; h <= v; ++h) {
            grp1.emplace_back(v, h);
            grp2.emplace_back(h, v);
        }
        groups.push_back(std::move(grp1));
        groups.push_back(std::move(grp2));
    } else { // "g1"
        groups.push_back({{v, 500}});
    }

    return groups;
}

ScanResult scan_parent(
    const int32_t* y,
    int n_children,
    int trait_idx,
    const std::string& rule,
    const std::string& rround,
    const Kernel& kern,
    const std::string& mut,
    double p,
    double c,
    const double* clone_lik_ptr,
    const std::string& clone_mode,
    const std::array<ColLik, 4>& current_cols,
    GenePair current_a,
    GenePair current_b,
    bool is_parent_a,
    int parent_displayed_value,
    bool need_both) {

    // Get current best
    double best_ll = loglik(n_children, current_cols, mut, p, c, clone_lik_ptr, clone_mode);
    GenePair best_genes = is_parent_a ? current_a : current_b;

    // Collect unique child observations for this trait
    std::set<int> unique_ys;
    for (int i = 0; i < n_children; ++i) {
        unique_ys.insert(y[i * 4 + trait_idx]);
    }

    // Build key set (important gene values to check)
    std::set<int> key_set(unique_ys.begin(), unique_ys.end());
    GenePair other = is_parent_a ? current_b : current_a;
    if (rule == "mean") {
        for (int yv : unique_ys) {
            for (int x : {other.first, other.second}) {
                key_set.insert(2 * yv - x);
                key_set.insert(2 * yv - 1 - x);
            }
        }
    }

    // Get candidate groups
    auto groups = candidates(rule, parent_displayed_value, rround);

    // Extract child trait observations column
    std::vector<int32_t> y_trait(n_children);
    for (int i = 0; i < n_children; ++i) {
        y_trait[i] = y[i * 4 + trait_idx];
    }

    // Lambda to score a gene pair
    auto score = [&](GenePair g) -> double {
        GenePair ga = is_parent_a ? g : current_a;
        GenePair gb = is_parent_a ? current_b : g;
        TraitRows tr = trait_rows(rule, ga, gb, kern, rround, need_both);
        ColLik col = index_trait_rows(tr, y_trait.data(), n_children);

        std::array<ColLik, 4> new_cols = current_cols;
        new_cols[trait_idx] = col;
        return loglik(n_children, new_cols, mut, p, c, clone_lik_ptr, clone_mode);
    };

    for (const auto& grp : groups) {
        int grp_size = static_cast<int>(grp.size());
        int step = std::max(1, grp_size / 60);

        // Build index set: coarse grid + key values
        std::set<int> idx_set;
        for (int i = 0; i < grp_size; i += step) {
            idx_set.insert(i);
        }
        for (int i = 0; i < grp_size; ++i) {
            if (key_set.count(grp[i].first) || key_set.count(grp[i].second)) {
                idx_set.insert(i);
            }
        }

        // Coarse search
        double coarse_best_ll = -1e300;
        int coarse_best_idx = 0;
        GenePair coarse_best_g = grp[0];
        for (int i : idx_set) {
            double ll = score(grp[i]);
            if (ll > coarse_best_ll) {
                coarse_best_ll = ll;
                coarse_best_idx = i;
                coarse_best_g = grp[i];
            }
        }

        // Fine refinement around the coarse best
        double fine_best_ll = coarse_best_ll;
        GenePair fine_best_g = coarse_best_g;
        int lo = std::max(0, coarse_best_idx - step);
        int hi = std::min(grp_size, coarse_best_idx + step + 1);
        for (int j = lo; j < hi; ++j) {
            double ll = score(grp[j]);
            if (ll > fine_best_ll) {
                fine_best_ll = ll;
                fine_best_g = grp[j];
            }
        }

        if (fine_best_ll > best_ll + 1e-9) {
            best_ll = fine_best_ll;
            best_genes = fine_best_g;
        }
    }

    return {best_ll, best_genes};
}

} // namespace citrus
