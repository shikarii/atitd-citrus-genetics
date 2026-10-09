"""30-model comparison pipeline (pure compute, no IO).

Fits each model to all litters, computes in-sample and cross-validated
log-scores, and returns structured results.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from citrus_genetics.core.constants import CLAIM, MODEL_MANIFEST, TRAITS
from citrus_genetics.core.model import LitterFit

IMPOSSIBLE_THRESHOLD = 1e-9


def run_single_model(
    name: str,
    model: dict[str, Any],
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Fit a single model and compute scores.

    Args:
        name: Model display name.
        model: Model specification dict.
        df: Full dataset DataFrame.

    Returns:
        Dict with model name, fit_ll, cv_ll, children_impossible,
        and per-litter log-scores.
    """
    fit_ll = 0.0
    cv_ll = 0.0
    bad = 0
    per: dict[str, float] = {}
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, model)
        ll = f.fit()
        fit_ll += ll
        bad += int((f.child_lik() < IMPOSSIBLE_THRESHOLD).sum())
        per[str(lit)] = ll
        odd = d.iloc[0::2]
        even = d.iloc[1::2]
        for tr, te in ((odd, even), (even, odd)):
            g = LitterFit(tr, model)
            g.fit()
            cv_ll += g.score_other(te)[0]
    return {
        "model": name,
        "fit_ll": round(fit_ll, 1),
        "cv_ll": round(cv_ll, 1),
        "children_impossible": bad,
        **{f"ll_{k}": round(x, 1) for k, x in per.items()},
    }


def run_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full 30-model comparison pipeline.

    Args:
        df: Full dataset DataFrame.

    Returns:
        DataFrame with model comparison results, sorted by cv_ll descending.
    """
    rows = []
    for entry in MODEL_MANIFEST:
        result = run_single_model(entry["display_name"], entry["spec"], df)
        result["model_id"] = entry["model_id"]
        rows.append(result)
    res = pd.DataFrame(rows)
    claim_cv = res.loc[res.model_id == "claim", "cv_ll"].iloc[0]
    res.insert(3, "cv_vs_claim", (res.cv_ll - claim_cv).round(1))
    return res.sort_values("cv_ll", ascending=False).reset_index(drop=True)


def fit_claim_genes(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Fit the CLAIM model and extract gene information per litter.

    Args:
        df: Full dataset DataFrame.

    Returns:
        List of dicts with litter name, child count, clone share,
        log-likelihood, and fitted gene pairs.
    """
    out: list[dict[str, Any]] = []
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, CLAIM)
        f.fit()
        row: dict[str, Any] = {
            "litter": str(lit),
            "n": len(d),
            "clone_share": round(f.c, 3),
            "loglik": round(f.loglik(), 1),
        }
        for t, tr in enumerate(TRAITS):
            row[f"A_{tr}_genes"] = f"{f.genes[('A', t)][0]}/{f.genes[('A', t)][1]}"
            row[f"B_{tr}_genes"] = f"{f.genes[('B', t)][0]}/{f.genes[('B', t)][1]}"
        out.append(row)
    return out
