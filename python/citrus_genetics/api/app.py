"""FastAPI application factory for the citrus genetics API.

Loads the current run directory at startup, validates artifact hashes,
and serves analytics results from memory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI

from citrus_genetics.core.constants import MODEL_MANIFEST, TRAITS
from citrus_genetics.io.provenance import validate_run_dir
from citrus_genetics.schemas.models import (
    ChildTraits,
    DegradedResponse,
    FittedGenes,
    GenePair,
    HealthyResponse,
    LitterDetail,
    LitterSummary,
    ModelComparison,
    ModelDetail,
    NoRunLoadedResponse,
    PPCDistribution,
    PPCMetric,
    PPCResult,
    TraitGenes,
)

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("results")


class RunData:
    """Loaded run data, held in memory for serving."""

    def __init__(self) -> None:
        """Initialise all data fields to empty defaults."""
        self.manifest: dict[str, Any] = {}
        self.comparison: pd.DataFrame = pd.DataFrame()
        self.genes: pd.DataFrame = pd.DataFrame()
        self.children: pd.DataFrame = pd.DataFrame()
        self.ppc_summary: dict[str, Any] = {}
        self.ppc_distributions: pd.DataFrame = pd.DataFrame()
        self.loaded: bool = False


def _load_run(results_dir: Path) -> RunData:
    """Load the current run directory into memory.

    Args:
        results_dir: Base results directory.

    Returns:
        Populated RunData, or empty RunData if no run exists.
    """
    data = RunData()
    current = results_dir / "current"
    if not current.exists():
        logger.warning("No results/current symlink found; starting in degraded mode")
        return data
    run_dir = current.resolve()
    if not run_dir.is_dir():
        logger.warning("results/current target %s is not a directory; degraded mode", run_dir)
        return data
    try:
        data.manifest = validate_run_dir(run_dir)
    except (FileNotFoundError, ValueError):
        logger.exception("Run validation failed for %s; degraded mode", run_dir)
        return data
    data.comparison = pd.read_csv(run_dir / "model_comparison.csv")
    data.genes = pd.read_csv(run_dir / "fitted_genes_claim.csv")
    data.children = pd.read_csv(run_dir / "children.csv")
    ppc_path = run_dir / "ppc_summary.json"
    if ppc_path.exists():
        data.ppc_summary = json.loads(ppc_path.read_text(encoding="utf-8"))
    dist_path = run_dir / "ppc_distributions.parquet"
    if dist_path.exists():
        data.ppc_distributions = pd.read_parquet(dist_path)
    data.loaded = True
    return data


def _parse_genes(row: Any, prefix: str) -> TraitGenes:
    """Parse fitted gene pairs for one parent from a DataFrame row.

    Args:
        row: A pandas Series (one row from the genes DataFrame).
        prefix: Parent prefix, either 'A' or 'B'.

    Returns:
        TraitGenes with gene pairs for all four traits.
    """
    pairs = {}
    for trait in TRAITS:
        g1, g2 = str(row[f"{prefix}_{trait}_genes"]).split("/")
        pairs[trait] = GenePair(g1=int(g1), g2=int(g2))
    return TraitGenes(**pairs)


def _route_health(run_data: RunData) -> HealthyResponse | DegradedResponse:
    """Handle GET /api/health."""
    if not run_data.loaded:
        return DegradedResponse(status="degraded")
    return HealthyResponse(
        status="ok",
        run_id=run_data.manifest.get("run_id", ""),
        source_data_hash=run_data.manifest.get("source_data_hash", ""),
        code_commit=run_data.manifest.get("code_commit", ""),
        fitted_at=run_data.manifest.get("timestamp", "1970-01-01T00:00:00"),
        artifact_count=len(run_data.manifest.get("artifacts", {})),
    )


def _route_get_models(run_data: RunData) -> list[ModelComparison] | NoRunLoadedResponse:
    """Handle GET /api/models."""
    if not run_data.loaded:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    id_lookup = {m["display_name"]: m["model_id"] for m in MODEL_MANIFEST}
    results: list[ModelComparison] = []
    for _, row in run_data.comparison.iterrows():
        results.append(
            ModelComparison(
                model_id=id_lookup.get(row["model"], row.get("model_id", "")),
                display_name=row["model"],
                fit_ll=row["fit_ll"],
                cv_ll=row["cv_ll"],
                cv_vs_claim=row["cv_vs_claim"],
                children_below_threshold=row["children_impossible"],
            )
        )
    return results


def _route_get_model(run_data: RunData, model_id: str) -> ModelDetail | NoRunLoadedResponse:
    """Handle GET /api/models/{model_id}."""
    if not run_data.loaded:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    id_lookup = {m["display_name"]: m["model_id"] for m in MODEL_MANIFEST}
    for _, row in run_data.comparison.iterrows():
        mid = id_lookup.get(row["model"], row.get("model_id", ""))
        if mid == model_id:
            per_litter = {
                col.replace("ll_", ""): float(row[col])
                for col in run_data.comparison.columns
                if col.startswith("ll_")
            }
            return ModelDetail(
                model_id=mid,
                display_name=row["model"],
                fit_ll=row["fit_ll"],
                cv_ll=row["cv_ll"],
                cv_vs_claim=row["cv_vs_claim"],
                children_below_threshold=row["children_impossible"],
                per_litter=per_litter,
            )
    return NoRunLoadedResponse(error="no_run_loaded", message=f"Model {model_id} not found.")


def _route_get_litters(run_data: RunData) -> list[LitterSummary] | NoRunLoadedResponse:
    """Handle GET /api/litters."""
    if not run_data.loaded:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    results: list[LitterSummary] = []
    for _, row in run_data.genes.iterrows():
        results.append(
            LitterSummary(
                litter=row["litter"],
                n=row["n"],
                clone_share=row["clone_share"],
                loglik=row["loglik"],
            )
        )
    return results


def _route_get_litter(run_data: RunData, name: str) -> LitterDetail | NoRunLoadedResponse:
    """Handle GET /api/litters/{name}."""
    if not run_data.loaded:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    gene_row = run_data.genes[run_data.genes["litter"] == name]
    if gene_row.empty:
        return NoRunLoadedResponse(error="no_run_loaded", message=f"Litter {name} not found.")
    row = gene_row.iloc[0]
    children_df = run_data.children[run_data.children["litter"] == name]
    children = [
        ChildTraits(color=r["color"], sweet=r["sweet"], size=r["size"], length=r["length"])
        for _, r in children_df.iterrows()
    ]
    return LitterDetail(
        litter=row["litter"],
        n=row["n"],
        clone_share=row["clone_share"],
        loglik=row["loglik"],
        genes=FittedGenes(
            litter=row["litter"],
            parent_a=_parse_genes(row, "A"),
            parent_b=_parse_genes(row, "B"),
        ),
        children=children,
    )


def _route_get_litter_genes(run_data: RunData, name: str) -> FittedGenes | NoRunLoadedResponse:
    """Handle GET /api/litters/{name}/genes."""
    if not run_data.loaded:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    gene_row = run_data.genes[run_data.genes["litter"] == name]
    if gene_row.empty:
        return NoRunLoadedResponse(error="no_run_loaded", message=f"Litter {name} not found.")
    row = gene_row.iloc[0]
    return FittedGenes(
        litter=row["litter"],
        parent_a=_parse_genes(row, "A"),
        parent_b=_parse_genes(row, "B"),
    )


def _route_get_ppc(run_data: RunData) -> PPCResult | NoRunLoadedResponse:
    """Handle GET /api/ppc."""
    if not run_data.loaded or not run_data.ppc_summary:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    return PPCResult(
        n_simulations=run_data.ppc_summary["n_simulations"],
        metrics=[PPCMetric(**m) for m in run_data.ppc_summary["metrics"]],
    )


def _route_get_ppc_distributions(run_data: RunData) -> list[PPCDistribution] | NoRunLoadedResponse:
    """Handle GET /api/ppc/distributions."""
    if not run_data.loaded or run_data.ppc_distributions.empty:
        return NoRunLoadedResponse(error="no_run_loaded", message="No analytics run is currently loaded.")
    return [
        PPCDistribution(
            metric=row["metric"],
            observed=row["observed"],
            simulated_values=row["simulated_values"],
        )
        for _, row in run_data.ppc_distributions.iterrows()
    ]


def _register_routes(app: FastAPI, run_data: RunData) -> None:
    """Register all API route handlers onto the FastAPI app.

    Args:
        app: The FastAPI application instance.
        run_data: Loaded run data to serve.
    """

    @app.get("/api/health")
    def health() -> HealthyResponse | DegradedResponse:
        return _route_health(run_data)

    @app.get("/api/models")
    def get_models() -> list[ModelComparison] | NoRunLoadedResponse:
        return _route_get_models(run_data)

    @app.get("/api/models/{model_id}")
    def get_model(model_id: str) -> ModelDetail | NoRunLoadedResponse:
        return _route_get_model(run_data, model_id)

    @app.get("/api/litters")
    def get_litters() -> list[LitterSummary] | NoRunLoadedResponse:
        return _route_get_litters(run_data)

    @app.get("/api/litters/{name}")
    def get_litter(name: str) -> LitterDetail | NoRunLoadedResponse:
        return _route_get_litter(run_data, name)

    @app.get("/api/litters/{name}/genes")
    def get_litter_genes(name: str) -> FittedGenes | NoRunLoadedResponse:
        return _route_get_litter_genes(run_data, name)

    @app.get("/api/ppc")
    def get_ppc() -> PPCResult | NoRunLoadedResponse:
        return _route_get_ppc(run_data)

    @app.get("/api/ppc/distributions")
    def get_ppc_distributions() -> list[PPCDistribution] | NoRunLoadedResponse:
        return _route_get_ppc_distributions(run_data)


def create_app(results_dir: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        results_dir: Override for the results directory path.

    Returns:
        Configured FastAPI app.
    """
    app = FastAPI(
        title="Citrus Genetics API",
        description="Statistical model validation for ATITD citrus tree genetics",
        version="1.0.0",
    )
    rd = results_dir or RESULTS_DIR
    run_data = _load_run(rd)
    _register_routes(app, run_data)
    return app
