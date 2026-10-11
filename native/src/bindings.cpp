#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "citrus/model.h"
#include "citrus/dispatch.h"

namespace py = pybind11;

// Convert TraitRows to Python dict of numpy arrays
static py::dict trait_rows_to_dict(const citrus::TraitRows& rows) {
    py::dict result;

    auto make_array = [](const std::array<double, citrus::V>& arr) {
        py::array_t<double> out(citrus::V);
        auto buf = out.mutable_unchecked<1>();
        for (int i = 0; i < citrus::V; ++i) buf(i) = arr[i];
        return out;
    };

    result["none"] = make_array(rows.none);
    result["s1"] = make_array(rows.s1);
    result["s2"] = make_array(rows.s2);
    if (rows.has_both) {
        result["both"] = make_array(rows.both);
    }
    return result;
}

// Extract ColLik from Python dict
static citrus::ColLik collik_from_dict(const py::dict& d, int n) {
    citrus::ColLik col;
    col.none.resize(n);
    col.s1.resize(n);
    col.s2.resize(n);

    auto none_arr = d["none"].cast<py::array_t<double>>();
    auto s1_arr = d["s1"].cast<py::array_t<double>>();
    auto s2_arr = d["s2"].cast<py::array_t<double>>();

    auto none_buf = none_arr.unchecked<1>();
    auto s1_buf = s1_arr.unchecked<1>();
    auto s2_buf = s2_arr.unchecked<1>();

    for (int i = 0; i < n; ++i) {
        col.none[i] = none_buf(i);
        col.s1[i] = s1_buf(i);
        col.s2[i] = s2_buf(i);
    }

    col.has_both = d.contains("both");
    if (col.has_both) {
        col.both.resize(n);
        auto both_arr = d["both"].cast<py::array_t<double>>();
        auto both_buf = both_arr.unchecked<1>();
        for (int i = 0; i < n; ++i) {
            col.both[i] = both_buf(i);
        }
    }

    return col;
}

// Python-facing trait_rows
static py::dict py_trait_rows(
    const std::string& rule,
    std::pair<int, int> a,
    std::pair<int, int> b,
    py::array_t<int64_t> offsets,
    py::array_t<double> probs,
    const std::string& rround,
    bool need_both) {

    citrus::Kernel kern;
    auto off_buf = offsets.unchecked<1>();
    auto prob_buf = probs.unchecked<1>();
    int n = static_cast<int>(off_buf.shape(0));
    kern.offsets.resize(n);
    kern.probs.resize(n);
    for (int i = 0; i < n; ++i) {
        kern.offsets[i] = off_buf(i);
        kern.probs[i] = prob_buf(i);
    }

    auto rows = citrus::trait_rows(rule, a, b, kern, rround, need_both);
    return trait_rows_to_dict(rows);
}

// Python-facing child_lik
static py::array_t<double> py_child_lik(
    py::array_t<int32_t> y,
    py::list cols_list,
    const std::string& mut,
    double p,
    double c,
    py::object clone_lik_obj,
    const std::string& clone_mode) {

    auto y_buf = y.unchecked<2>();
    int n = static_cast<int>(y_buf.shape(0));

    std::array<citrus::ColLik, 4> cols;
    for (int t = 0; t < 4; ++t) {
        cols[t] = collik_from_dict(cols_list[t].cast<py::dict>(), n);
    }

    const double* clone_ptr = nullptr;
    py::array_t<double> clone_arr;
    if (!clone_lik_obj.is_none()) {
        clone_arr = clone_lik_obj.cast<py::array_t<double>>();
        clone_ptr = clone_arr.data();
    }

    auto result = citrus::child_lik(n, cols, mut, p, c, clone_ptr, clone_mode);

    py::array_t<double> out(n);
    auto out_buf = out.mutable_unchecked<1>();
    for (int i = 0; i < n; ++i) out_buf(i) = result[i];
    return out;
}

// Python-facing loglik
static double py_loglik(
    py::array_t<int32_t> y,
    py::list cols_list,
    const std::string& mut,
    double p,
    double c,
    py::object clone_lik_obj,
    const std::string& clone_mode) {

    auto y_buf = y.unchecked<2>();
    int n = static_cast<int>(y_buf.shape(0));

    std::array<citrus::ColLik, 4> cols;
    for (int t = 0; t < 4; ++t) {
        cols[t] = collik_from_dict(cols_list[t].cast<py::dict>(), n);
    }

    const double* clone_ptr = nullptr;
    py::array_t<double> clone_arr;
    if (!clone_lik_obj.is_none()) {
        clone_arr = clone_lik_obj.cast<py::array_t<double>>();
        clone_ptr = clone_arr.data();
    }

    return citrus::loglik(n, cols, mut, p, c, clone_ptr, clone_mode);
}

// Python-facing scan_parent
static py::tuple py_scan_parent(
    py::array_t<int32_t> y,
    int trait_idx,
    const std::string& rule,
    const std::string& rround,
    py::array_t<int64_t> offsets,
    py::array_t<double> probs,
    const std::string& mut,
    double p,
    double c,
    py::object clone_lik_obj,
    const std::string& clone_mode,
    py::list cols_list,
    std::pair<int, int> current_a,
    std::pair<int, int> current_b,
    bool is_parent_a,
    int parent_displayed_value,
    bool need_both) {

    auto y_buf = y.unchecked<2>();
    int n = static_cast<int>(y_buf.shape(0));

    citrus::Kernel kern;
    auto off_buf = offsets.unchecked<1>();
    auto prob_buf = probs.unchecked<1>();
    int kn = static_cast<int>(off_buf.shape(0));
    kern.offsets.resize(kn);
    kern.probs.resize(kn);
    for (int i = 0; i < kn; ++i) {
        kern.offsets[i] = off_buf(i);
        kern.probs[i] = prob_buf(i);
    }

    std::array<citrus::ColLik, 4> cols;
    for (int t = 0; t < 4; ++t) {
        cols[t] = collik_from_dict(cols_list[t].cast<py::dict>(), n);
    }

    const double* clone_ptr = nullptr;
    py::array_t<double> clone_arr;
    if (!clone_lik_obj.is_none()) {
        clone_arr = clone_lik_obj.cast<py::array_t<double>>();
        clone_ptr = clone_arr.data();
    }

    auto result = citrus::scan_parent(
        y.data(), n, trait_idx, rule, rround, kern, mut, p, c,
        clone_ptr, clone_mode, cols, current_a, current_b,
        is_parent_a, parent_displayed_value, need_both);

    return py::make_tuple(result.loglik, result.genes);
}

PYBIND11_MODULE(_citrus_native, m) {
    m.doc() = "C++/CUDA acceleration for citrus genetics model fitting";

    m.def("trait_rows", &py_trait_rows,
          py::arg("rule"), py::arg("a"), py::arg("b"),
          py::arg("offsets"), py::arg("probs"),
          py::arg("rround"), py::arg("need_both") = false,
          "Compute trait row probability distributions");

    m.def("child_lik", &py_child_lik,
          py::arg("y"), py::arg("cols"),
          py::arg("mut"), py::arg("p"), py::arg("c"),
          py::arg("clone_lik"), py::arg("clone_mode"),
          "Compute per-child likelihoods");

    m.def("loglik", &py_loglik,
          py::arg("y"), py::arg("cols"),
          py::arg("mut"), py::arg("p"), py::arg("c"),
          py::arg("clone_lik"), py::arg("clone_mode"),
          "Compute total log-likelihood");

    m.def("scan_parent", &py_scan_parent,
          py::arg("y"), py::arg("trait_idx"),
          py::arg("rule"), py::arg("rround"),
          py::arg("offsets"), py::arg("probs"),
          py::arg("mut"), py::arg("p"), py::arg("c"),
          py::arg("clone_lik"), py::arg("clone_mode"),
          py::arg("cols"),
          py::arg("current_a"), py::arg("current_b"),
          py::arg("is_parent_a"),
          py::arg("parent_displayed_value"),
          py::arg("need_both"),
          "Fused scan for best gene pair (one parent, one trait)");

    m.def("has_avx2", &citrus::dispatch::has_avx2,
          "Check if AVX2 is available");
    m.def("has_cuda", &citrus::dispatch::has_cuda,
          "Check if CUDA is available");
    m.def("cuda_device_name", &citrus::dispatch::cuda_device_name,
          "Get CUDA device name");
}
