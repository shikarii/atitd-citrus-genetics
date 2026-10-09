"""Tests for citrus_genetics.core.model."""

from __future__ import annotations

import numpy as np

from citrus_genetics.core.model import (
    LitterFit,
    candidates,
    display,
    kernel,
    simulate,
    trait_rows,
)


class TestKernel:
    def test_uniform_sums_to_one(self):
        _, kp = kernel("uniform", 150)
        assert abs(kp.sum() - 1.0) < 1e-12

    def test_triangular_sums_to_one(self):
        _, kp = kernel("triangular", 200)
        assert abs(kp.sum() - 1.0) < 1e-12

    def test_uniform_length(self):
        _offs, kp = kernel("uniform", 10)
        assert len(_offs) == 21
        assert len(kp) == 21

    def test_triangular_peak(self):
        _offs, kp = kernel("triangular", 5)
        assert kp[5] == kp.max()  # center is the peak

    def test_kernel_symmetry(self):
        _, kp = kernel("triangular", 100)
        np.testing.assert_allclose(kp, kp[::-1])


class TestDisplay:
    def test_mean_halfup(self):
        assert display("mean", 500, 501, "halfup") == 501
        assert display("mean", 0, 1, "halfup") == 1

    def test_mean_floor(self):
        assert display("mean", 500, 501, "floor") == 500
        assert display("mean", 0, 1, "floor") == 0

    def test_min(self):
        assert display("min", 300, 700) == 300
        assert display("min", 0, 1000) == 0

    def test_max(self):
        assert display("max", 300, 700) == 700
        assert display("max", 0, 1000) == 1000

    def test_g1(self):
        assert display("g1", 42, 999) == 42

    def test_mean_edge_cases(self):
        assert display("mean", 0, 0, "halfup") == 0
        assert display("mean", 1000, 1000, "halfup") == 1000

    def test_display_numpy_arrays(self):
        g1 = np.array([100, 200, 300])
        g2 = np.array([200, 400, 600])
        result = display("min", g1, g2)
        np.testing.assert_array_equal(result, [100, 200, 300])

    def test_display_always_in_range(self):
        for rule in ("mean", "min", "max", "g1"):
            for g1 in (0, 500, 1000):
                for g2 in (0, 500, 1000):
                    v = display(rule, g1, g2)
                    assert 0 <= v <= 1000


class TestCandidates:
    def test_mean_roundtrip(self):
        for v in (0, 250, 500, 750, 1000):
            groups = candidates("mean", v, "halfup")
            for grp in groups:
                for row in grp:
                    assert display("mean", row[0], row[1], "halfup") == v

    def test_min_roundtrip(self):
        for v in (0, 500, 1000):
            groups = candidates("min", v)
            for grp in groups:
                for row in grp:
                    assert display("min", row[0], row[1]) == v

    def test_max_roundtrip(self):
        for v in (0, 500, 1000):
            groups = candidates("max", v)
            for grp in groups:
                for row in grp:
                    assert display("max", row[0], row[1]) == v

    def test_g1_single(self):
        groups = candidates("g1", 42)
        assert len(groups) == 1
        assert groups[0].shape == (1, 2)
        assert groups[0][0, 0] == 42
        assert groups[0][0, 1] == 500


class TestTraitRows:
    def test_none_sums_to_one(self):
        kern = kernel("uniform", 10)
        r = trait_rows("mean", (500, 500), (500, 500), kern, "halfup")
        assert abs(r["none"].sum() - 1.0) < 1e-10

    def test_s1_sums_to_one(self):
        kern = kernel("uniform", 10)
        r = trait_rows("min", (300, 700), (300, 400), kern, "halfup")
        assert abs(r["s1"].sum() - 1.0) < 1e-10

    def test_s2_sums_to_one(self):
        kern = kernel("triangular", 20)
        r = trait_rows("max", (300, 700), (300, 400), kern, "halfup")
        assert abs(r["s2"].sum() - 1.0) < 1e-10

    def test_both_sums_to_one(self):
        kern = kernel("uniform", 10)
        r = trait_rows("mean", (500, 500), (500, 500), kern, "halfup", need_both=True)
        assert "both" in r
        assert abs(r["both"].sum() - 1.0) < 1e-10

    def test_non_negative(self):
        kern = kernel("uniform", 150)
        r = trait_rows("mean", (0, 1000), (500, 500), kern, "halfup", need_both=True)
        for key in r:
            assert (r[key] >= 0).all()


class TestLitterFit:
    def test_fit_converges(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        ll = f.fit()
        assert np.isfinite(ll)
        assert ll < 0  # log-score is negative

    def test_loglik_is_finite(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        ll = f.loglik()
        assert np.isfinite(ll)

    def test_child_lik_positive(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        f.fit()
        lik = f.child_lik()
        assert (lik >= 0).all()

    def test_determinism(self, single_litter_df, claim_model):
        f1 = LitterFit(single_litter_df, claim_model)
        ll1 = f1.fit()
        f2 = LitterFit(single_litter_df, claim_model)
        ll2 = f2.fit()
        assert ll1 == ll2
        assert f1.genes == f2.genes
        assert f1.c == f2.c

    def test_score_other(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        f.fit()
        ll, lik = f.score_other(single_litter_df)
        assert np.isfinite(ll)
        assert len(lik) == len(single_litter_df)


class TestSimulate:
    def test_output_shape(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        f.fit()
        rng = np.random.default_rng(42)
        out = simulate(f, 20, rng)
        assert out.shape == (20, 4)

    def test_values_in_range(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        f.fit()
        rng = np.random.default_rng(42)
        out = simulate(f, 100, rng)
        assert (out >= 0).all()
        assert (out <= 1000).all()

    def test_determinism(self, single_litter_df, claim_model):
        f = LitterFit(single_litter_df, claim_model)
        f.fit()
        out1 = simulate(f, 10, np.random.default_rng(42))
        out2 = simulate(f, 10, np.random.default_rng(42))
        np.testing.assert_array_equal(out1, out2)
