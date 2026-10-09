"""Constants and model manifest for citrus genetics analysis.

Contains the authoritative 30-model manifest, trait definitions,
litter identifiers, and configuration constants.
"""

from __future__ import annotations

from typing import Any

from citrus_genetics.core.model import FLOOR, TRAITS, V

__all__ = [
    "CLAIM",
    "FLOOR",
    "LITTER_NAMES",
    "MODEL_MANIFEST",
    "ROOT_BOOTSTRAP_SEED",
    "ROOT_OPTIMIZER_SEED",
    "TRAITS",
    "V",
]

LITTER_NAMES: list[str] = [
    "Hive1",
    "Hive2",
    "Hive3",
    "Hive4",
    "Hive5",
    "Hive6",
    "Hive7",
    "Hive8",
    "Hive9",
    "Hive10",
    "Hive11",
    "Hive1a",
    "Hive1b",
    "Hive1c",
]

ROOT_OPTIMIZER_SEED: int = 42
ROOT_BOOTSTRAP_SEED: int = 7

ModelSpec = dict[str, Any]

CLAIM: ModelSpec = {
    "rules": ("mean", "min", "max", "g1"),
    "mut": "one8",
    "p": None,
    "shape": "uniform",
    "R": 150,
    "rround": "halfup",
    "clone": True,
}


def _build_manifest() -> list[dict[str, Any]]:
    """Build the 30-model manifest matching upstream compare.py:variants().

    Returns:
        List of dicts with model_id, display_name, and spec keys.
    """
    models: list[dict[str, Any]] = []

    def add(model_id: str, display_name: str, spec: ModelSpec) -> None:
        models.append({"model_id": model_id, "display_name": display_name, "spec": spec})

    add("claim", "CLAIM: 1 of 8 genes, uniform +-150", CLAIM)

    for r_val in (100, 125, 140, 160, 175, 200):
        add(f"uniform_{r_val}", f"uniform +-{r_val}", {**CLAIM, "R": r_val})

    for r_val in (150, 200, 250):
        add(f"tri_{r_val}", f"triangular +-{r_val}", {**CLAIM, "shape": "triangular", "R": r_val})

    for p_val in (0.08, 0.11, 0.14, 0.17, 0.20):
        p_str = f"{p_val:.2f}".lstrip("0")
        add(
            f"indep_{p_str.replace('.', '')}",
            f"each gene nudged independently, p={p_val}",
            {**CLAIM, "mut": "indep", "p": p_val},
        )

    add("one_gene", "1 gene per trait (no hidden genes)", {**CLAIM, "rules": ("g1",) * 4, "mut": "one_g1"})

    for t, trait in enumerate(TRAITS):
        for alt in ("mean", "min", "max", "g1"):
            if alt != CLAIM["rules"][t]:
                rules = list(CLAIM["rules"])
                rules[t] = alt
                add(f"{trait}_{alt}", f"{trait} shown as {alt}", {**CLAIM, "rules": tuple(rules)})

    add("color_floor", "color rounds down", {**CLAIM, "rround": "floor"})
    add("no_clone", "no clone component", {**CLAIM, "clone": False})

    return models


MODEL_MANIFEST: list[dict[str, Any]] = _build_manifest()
"""Authoritative list of 30 models with model_id, display_name, and spec."""


def get_model_by_id(model_id: str) -> dict[str, Any] | None:
    """Look up a model by its URL-safe slug.

    Args:
        model_id: URL-safe model identifier.

    Returns:
        Model dict with model_id, display_name, and spec, or None.
    """
    for m in MODEL_MANIFEST:
        if m["model_id"] == model_id:
            return m
    return None


def get_variants() -> dict[str, ModelSpec]:
    """Return model specs keyed by display_name, matching upstream variants().

    Returns:
        Dict of display_name -> model spec.
    """
    return {m["display_name"]: m["spec"] for m in MODEL_MANIFEST}
