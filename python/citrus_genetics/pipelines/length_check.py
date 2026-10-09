"""Length rule degeneracy test (pure compute, no IO).

Tests whether 'Length shown as min/max' beats the claimed 'Length = gene 1'
only because it has more free values. Fits both to fake data made by the
CLAIM model where gene 1 is the truth.
"""

from __future__ import annotations

from typing import Any

import pandas as pd  # noqa: TC002

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import LitterFit
from citrus_genetics.pipelines.sim_checks import fake_dataset

RIVALS: dict[str, dict[str, Any]] = {
    "CLAIM": CLAIM,
    "length=min": {**CLAIM, "rules": ("mean", "min", "max", "min")},
    "length=max": {**CLAIM, "rules": ("mean", "min", "max", "max")},
}


def run_length_check(
    df: pd.DataFrame,
    seeds: tuple[int, ...] = (11, 12, 13, 14, 15),
) -> list[dict[str, Any]]:
    """Run the length rule degeneracy test.

    Args:
        df: Real dataset DataFrame (used for litter structure).
        seeds: Random seeds for synthetic datasets.

    Returns:
        List of dicts with seed and per-model fit log-scores.
    """
    results: list[dict[str, Any]] = []
    for seed in seeds:
        fake, _ = fake_dataset(df, "CLAIM", seed)
        scores: dict[str, float] = {}
        for name, model in RIVALS.items():
            total = 0.0
            for _lit, d in fake.groupby("litter", sort=False):
                total += LitterFit(d, model).fit()
            scores[name] = round(total, 1)
        results.append({"seed": seed, "scores": scores})
    return results
