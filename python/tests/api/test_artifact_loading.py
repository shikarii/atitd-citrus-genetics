"""Tests for API artifact loading and run validation."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path  # noqa: TC003

import pandas as pd
from fastapi.testclient import TestClient

from citrus_genetics.api.app import create_app
from citrus_genetics.io.provenance import sha256_file


def _write_csv_artifacts(run_dir: Path) -> None:
    children = pd.DataFrame(
        [
            {
                "litter": "Hive1",
                "child": 1,
                "A_color": 500,
                "A_sweet": 300,
                "A_size": 600,
                "A_length": 700,
                "B_color": 400,
                "B_sweet": 200,
                "B_size": 500,
                "B_length": 600,
                "color": 450,
                "sweet": 200,
                "size": 600,
                "length": 700,
            },
        ]
    )
    children.to_csv(run_dir / "children.csv", index=False)

    comparison = pd.DataFrame(
        [
            {
                "model": "CLAIM: 1 of 8 genes, uniform +-150",
                "model_id": "claim",
                "fit_ll": -100.0,
                "cv_ll": -120.0,
                "cv_vs_claim": 0.0,
                "children_impossible": 0,
                "ll_Hive1": -100.0,
            }
        ]
    )
    comparison.to_csv(run_dir / "model_comparison.csv", index=False)

    genes = pd.DataFrame(
        [
            {
                "litter": "Hive1",
                "n": 1,
                "clone_share": 0.0,
                "loglik": -100.0,
                "A_color_genes": "500/500",
                "B_color_genes": "400/400",
                "A_sweet_genes": "300/300",
                "B_sweet_genes": "200/200",
                "A_size_genes": "600/600",
                "B_size_genes": "500/500",
                "A_length_genes": "700/500",
                "B_length_genes": "600/500",
            }
        ]
    )
    genes.to_csv(run_dir / "fitted_genes_claim.csv", index=False)


def _write_ppc_artifacts(run_dir: Path) -> None:
    ppc = {
        "n_simulations": 10,
        "metrics": [
            {
                "name": "0 traits changed",
                "observed": 5,
                "simulated_mean": 4.5,
                "simulated_p2_5": 2.0,
                "simulated_p97_5": 7.0,
            },
        ],
    }
    (run_dir / "ppc_summary.json").write_text(json.dumps(ppc), encoding="utf-8")

    dists = pd.DataFrame(
        [
            {
                "metric": "0 traits changed",
                "observed": 5,
                "simulated_values": [4, 5, 3, 6, 4, 5, 5, 4, 3, 6],
            }
        ]
    )
    dists.to_parquet(run_dir / "ppc_distributions.parquet", index=False)


def _write_manifest_file(run_dir: Path, run_id: str) -> None:
    artifact_names = [
        "children.csv",
        "model_comparison.csv",
        "fitted_genes_claim.csv",
        "ppc_summary.json",
        "ppc_distributions.parquet",
    ]
    artifacts = {name: sha256_file(run_dir / name) for name in artifact_names}
    manifest = {
        "run_id": run_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "source_data_hash": artifacts["children.csv"],
        "code_commit": "abc123",
        "artifacts": artifacts,
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _create_current_link(tmp_path: Path, run_dir: Path) -> None:
    current = tmp_path / "current"
    if platform.system() == "Windows":
        os.system(f'mklink /J "{current}" "{run_dir}"')  # noqa: S605
    else:
        current.symlink_to(run_dir)


def _create_run_dir(tmp_path: Path) -> Path:
    """Create a minimal valid run directory for testing."""
    runs_dir = tmp_path / "runs"
    run_id = "test-run-001"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)

    _write_csv_artifacts(run_dir)
    _write_ppc_artifacts(run_dir)
    _write_manifest_file(run_dir, run_id)
    _create_current_link(tmp_path, run_dir)

    return tmp_path


class TestLoadedAPI:
    def test_health_returns_ok(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["run_id"] == "test-run-001"

    def test_models_returns_list(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_model_detail(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/models/claim")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_id"] == "claim"
        assert "per_litter" in data

    def test_litters(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/litters")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_litter_detail(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/litters/Hive1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["litter"] == "Hive1"
        assert "genes" in data
        assert "children" in data

    def test_litter_genes(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/litters/Hive1/genes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["litter"] == "Hive1"
        assert "parent_a" in data

    def test_ppc(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/ppc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_simulations"] == 10

    def test_ppc_distributions(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/ppc/distributions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_unknown_model_returns_error(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/models/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] == "no_run_loaded"

    def test_unknown_litter_returns_error(self, tmp_path):
        results_dir = _create_run_dir(tmp_path)
        app = create_app(results_dir=results_dir)
        client = TestClient(app)
        resp = client.get("/api/litters/NonexistentHive")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] == "no_run_loaded"
