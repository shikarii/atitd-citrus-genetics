"""Tests for citrus_genetics.core.constants."""

from __future__ import annotations

import re

from citrus_genetics.core.constants import (
    CLAIM,
    LITTER_NAMES,
    MODEL_MANIFEST,
    get_model_by_id,
    get_variants,
)


class TestModelManifest:
    def test_exactly_30_models(self):
        assert len(MODEL_MANIFEST) == 30

    def test_unique_model_ids(self):
        ids = [m["model_id"] for m in MODEL_MANIFEST]
        assert len(ids) == len(set(ids))

    def test_model_ids_url_safe(self):
        for m in MODEL_MANIFEST:
            assert re.match(r"^[a-z0-9_]+$", m["model_id"]), f"model_id not URL-safe: {m['model_id']}"

    def test_claim_is_first(self):
        assert MODEL_MANIFEST[0]["model_id"] == "claim"

    def test_all_have_required_keys(self):
        for m in MODEL_MANIFEST:
            assert "model_id" in m
            assert "display_name" in m
            assert "spec" in m

    def test_spec_has_required_fields(self):
        for m in MODEL_MANIFEST:
            spec = m["spec"]
            assert "rules" in spec
            assert "mut" in spec
            assert "shape" in spec
            assert "R" in spec
            assert "rround" in spec
            assert "clone" in spec

    def test_get_model_by_id_found(self):
        result = get_model_by_id("claim")
        assert result is not None
        assert result["model_id"] == "claim"

    def test_get_model_by_id_not_found(self):
        assert get_model_by_id("nonexistent") is None

    def test_get_variants_matches_manifest(self):
        variants = get_variants()
        assert len(variants) == 30
        for m in MODEL_MANIFEST:
            assert m["display_name"] in variants


class TestLitterNames:
    def test_exactly_14_litters(self):
        assert len(LITTER_NAMES) == 14

    def test_known_litters_present(self):
        assert "Hive1" in LITTER_NAMES
        assert "Hive11" in LITTER_NAMES
        assert "Hive1a" in LITTER_NAMES
        assert "Hive1c" in LITTER_NAMES


class TestClaim:
    def test_claim_rules(self):
        assert CLAIM["rules"] == ("mean", "min", "max", "g1")

    def test_claim_mut(self):
        assert CLAIM["mut"] == "one8"

    def test_claim_r(self):
        assert CLAIM["R"] == 150
