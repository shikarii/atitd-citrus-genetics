"""Tests for citrus_genetics.pipelines.compare."""

from __future__ import annotations

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.pipelines.compare import fit_claim_genes, run_single_model


class TestRunSingleModel:
    def test_returns_required_fields(self, single_litter_df):
        result = run_single_model("CLAIM", CLAIM, single_litter_df)
        assert "model" in result
        assert "fit_ll" in result
        assert "cv_ll" in result
        assert "children_impossible" in result

    def test_fit_ll_is_negative(self, single_litter_df):
        result = run_single_model("CLAIM", CLAIM, single_litter_df)
        assert result["fit_ll"] < 0


class TestFitClaimGenes:
    def test_returns_one_row_per_litter(self, single_litter_df):
        genes = fit_claim_genes(single_litter_df)
        assert len(genes) == 1
        assert genes[0]["litter"] == "Hive1"

    def test_has_gene_columns(self, single_litter_df):
        genes = fit_claim_genes(single_litter_df)
        row = genes[0]
        for trait in ("color", "sweet", "size", "length"):
            assert f"A_{trait}_genes" in row
            assert f"B_{trait}_genes" in row
            assert "/" in str(row[f"A_{trait}_genes"])
