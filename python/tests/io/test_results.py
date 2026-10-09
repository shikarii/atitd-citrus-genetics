"""Tests for citrus_genetics.io.results."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from citrus_genetics.io.results import (
    write_fitted_genes,
    write_model_comparison,
    write_ppc_distributions,
    write_ppc_summary,
)


class TestWriteModelComparison:
    def test_writes_csv(self, tmp_path):
        df = pd.DataFrame({"model": ["A", "B"], "fit_ll": [-100.0, -200.0]})
        out = tmp_path / "comparison.csv"
        write_model_comparison(df, out)
        assert out.exists()
        loaded = pd.read_csv(out)
        assert len(loaded) == 2


class TestWriteFittedGenes:
    def test_writes_csv(self, tmp_path):
        data = [{"litter": "Hive1", "n": 10, "A_color_genes": "500/500"}]
        out = tmp_path / "genes.csv"
        write_fitted_genes(data, out)
        assert out.exists()
        loaded = pd.read_csv(out)
        assert loaded.iloc[0]["litter"] == "Hive1"


class TestWritePPCSummary:
    def test_writes_json(self, tmp_path):
        obs_k = np.array([100.0, 50.0, 20.0])
        obs_tr = np.array([30.0, 40.0, 50.0, 60.0])
        sim_k = np.random.default_rng(42).random((10, 3)) * 100
        sim_tr = np.random.default_rng(42).random((10, 4)) * 50
        out = tmp_path / "ppc.json"
        write_ppc_summary(obs_k, obs_tr, sim_k, sim_tr, 10, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["n_simulations"] == 10
        assert len(data["metrics"]) == 7  # 3 change-count + 4 trait


class TestWritePPCDistributions:
    def test_writes_parquet(self, tmp_path):
        obs_k = np.array([100.0, 50.0, 20.0])
        obs_tr = np.array([30.0, 40.0, 50.0, 60.0])
        sim_k = np.random.default_rng(42).random((10, 3)) * 100
        sim_tr = np.random.default_rng(42).random((10, 4)) * 50
        out = tmp_path / "distributions.parquet"
        write_ppc_distributions(obs_k, obs_tr, sim_k, sim_tr, out)
        assert out.exists()
        loaded = pd.read_parquet(out)
        assert len(loaded) == 7
