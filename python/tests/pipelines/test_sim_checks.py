"""Tests for citrus_genetics.pipelines.sim_checks."""

from __future__ import annotations

import numpy as np

from citrus_genetics.pipelines.sim_checks import fake_dataset, ppc


class TestFakeDataset:
    def test_preserves_shape(self, single_litter_df):
        fake, _truth = fake_dataset(single_litter_df, "CLAIM", seed=42)
        assert len(fake) == len(single_litter_df)
        assert set(fake.columns) == set(single_litter_df.columns)

    def test_produces_truth_dict(self, single_litter_df):
        _fake, truth = fake_dataset(single_litter_df, "CLAIM", seed=42)
        assert "Hive1" in truth
        assert ("A", 0) in truth["Hive1"]

    def test_deterministic(self, single_litter_df):
        fake1, _ = fake_dataset(single_litter_df, "CLAIM", seed=42)
        fake2, _ = fake_dataset(single_litter_df, "CLAIM", seed=42)
        np.testing.assert_array_equal(
            fake1[["color", "sweet", "size", "length"]].values,
            fake2[["color", "sweet", "size", "length"]].values,
        )


class TestPPC:
    def test_output_shapes(self, single_litter_df):
        obs_k, obs_tr, sim_k, sim_tr = ppc(single_litter_df, n_sims=5, seed=1)
        assert obs_k.shape == (3,)
        assert obs_tr.shape == (4,)
        assert sim_k.shape == (5, 3)
        assert sim_tr.shape == (5, 4)

    def test_non_negative(self, single_litter_df):
        obs_k, obs_tr, sim_k, sim_tr = ppc(single_litter_df, n_sims=5, seed=1)
        assert (obs_k >= 0).all()
        assert (obs_tr >= 0).all()
        assert (sim_k >= 0).all()
        assert (sim_tr >= 0).all()
