"""Tests for citrus_genetics.api.app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from citrus_genetics.api.app import create_app


class TestDegradedMode:
    """API should start in degraded mode when no run is loaded."""

    def test_health_returns_degraded(self, tmp_path):
        app = create_app(results_dir=tmp_path)
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"

    def test_models_returns_no_run(self, tmp_path):
        app = create_app(results_dir=tmp_path)
        client = TestClient(app)
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] == "no_run_loaded"

    def test_litters_returns_no_run(self, tmp_path):
        app = create_app(results_dir=tmp_path)
        client = TestClient(app)
        resp = client.get("/api/litters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] == "no_run_loaded"

    def test_ppc_returns_no_run(self, tmp_path):
        app = create_app(results_dir=tmp_path)
        client = TestClient(app)
        resp = client.get("/api/ppc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"] == "no_run_loaded"
