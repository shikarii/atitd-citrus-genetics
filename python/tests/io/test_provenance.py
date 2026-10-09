"""Tests for citrus_genetics.io.provenance."""

from __future__ import annotations

import json
import re

import pytest

from citrus_genetics.io.provenance import sha256_file, validate_run_dir


class TestSha256File:
    def test_consistent_hash(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world", encoding="utf-8")
        h1 = sha256_file(p)
        h2 = sha256_file(p)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_content_different_hash(self, tmp_path):
        p1 = tmp_path / "a.txt"
        p2 = tmp_path / "b.txt"
        p1.write_text("hello", encoding="utf-8")
        p2.write_text("world", encoding="utf-8")
        assert sha256_file(p1) != sha256_file(p2)


class TestValidateRunDir:
    def test_missing_manifest_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match=re.escape("run_manifest.json")):
            validate_run_dir(tmp_path)

    def test_missing_artifact_raises(self, tmp_path):
        manifest = {"artifacts": {"missing.csv": "abc123"}}
        (tmp_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(FileNotFoundError, match=re.escape("missing.csv")):
            validate_run_dir(tmp_path)

    def test_hash_mismatch_raises(self, tmp_path):
        artifact = tmp_path / "data.csv"
        artifact.write_text("some data", encoding="utf-8")
        manifest = {"artifacts": {"data.csv": "wrong_hash"}}
        (tmp_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="Hash mismatch"):
            validate_run_dir(tmp_path)

    def test_valid_run_dir(self, tmp_path):
        artifact = tmp_path / "data.csv"
        artifact.write_text("some data", encoding="utf-8")
        h = sha256_file(artifact)
        manifest = {
            "source_data_hash": h,
            "artifacts": {"data.csv": h},
        }
        (tmp_path / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = validate_run_dir(tmp_path)
        assert result["source_data_hash"] == h
