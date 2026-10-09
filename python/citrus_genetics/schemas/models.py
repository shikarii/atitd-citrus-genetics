"""Pydantic response schemas for the citrus genetics API.

These schemas define the normative API contract. The generated OpenAPI
schema is derived from these definitions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TraitName(StrEnum):
    """Enumeration of the four observable citrus traits."""

    COLOR = "color"
    SWEET = "sweet"
    SIZE = "size"
    LENGTH = "length"


class GenePair(BaseModel):
    """A pair of gene values for a single trait."""

    g1: int = Field(ge=0, le=1000)
    g2: int = Field(ge=0, le=1000)


class ChildTraits(BaseModel):
    """Observed trait values for a single child."""

    color: int = Field(ge=0, le=1000)
    sweet: int = Field(ge=0, le=1000)
    size: int = Field(ge=0, le=1000)
    length: int = Field(ge=0, le=1000)


class TraitGenes(BaseModel):
    """Fitted gene pairs for all four traits of a single parent."""

    color: GenePair
    sweet: GenePair
    size: GenePair
    length: GenePair


class HealthyResponse(BaseModel):
    """Health response when a valid run is loaded."""

    status: Literal["ok"]
    run_id: str
    source_data_hash: str
    code_commit: str
    fitted_at: str
    artifact_count: int = Field(gt=0)


class DegradedResponse(BaseModel):
    """Health response when no run is loaded."""

    status: Literal["degraded"]


HealthResponse = Annotated[
    HealthyResponse | DegradedResponse,
    Field(discriminator="status"),
]


class NoRunLoadedResponse(BaseModel):
    """Error response for data endpoints when no run is loaded (HTTP 503)."""

    error: Literal["no_run_loaded"]
    message: str


class ModelComparison(BaseModel):
    """Summary comparison result for a single model."""

    model_id: str
    display_name: str
    fit_ll: float
    cv_ll: float
    cv_vs_claim: float
    children_below_threshold: int


class ModelDetail(ModelComparison):
    """Detailed model result with per-litter scores."""

    per_litter: dict[str, float]


class LitterSummary(BaseModel):
    """Summary of a single litter's fit."""

    litter: str
    n: int
    clone_share: float
    loglik: float


class FittedGenes(BaseModel):
    """Fitted gene pairs for both parents in a litter."""

    litter: str
    parent_a: TraitGenes
    parent_b: TraitGenes


class LitterDetail(LitterSummary):
    """Detailed litter result with genes and children."""

    genes: FittedGenes
    children: list[ChildTraits]


class PPCMetric(BaseModel):
    """A single plug-in predictive check metric."""

    name: str
    observed: int
    simulated_mean: float
    simulated_p2_5: float
    simulated_p97_5: float


class PPCResult(BaseModel):
    """Summary of plug-in predictive check results."""

    n_simulations: int
    metrics: list[PPCMetric]


class PPCDistribution(BaseModel):
    """Full simulated distribution for a single PPC metric."""

    metric: str
    observed: int
    simulated_values: list[int]
