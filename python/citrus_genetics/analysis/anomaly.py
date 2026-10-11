"""Per-child anomaly scoring across all 30 models.

For each of the 692 children, compute its log-likelihood under every model
in MODEL_MANIFEST using the MLE-fitted genes for that litter. Children with
very low likelihoods under all models are informative anomalies — they suggest
that no tested model can explain that child's observed traits given its parents.

The anomaly score for a child is the mean log-likelihood across models (lower = worse).
A rank of 1 means the child is the hardest for all models to explain.

Exports results/current/anomaly_scores.csv with columns:
    litter, child_idx, model_id, log_lik, child_rank_by_model,
    mean_log_lik, overall_rank
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd

from citrus_genetics.core.constants import CLAIM, MODEL_MANIFEST
from citrus_genetics.core.model import FLOOR, TRAITS, LitterFit


def _score_litter(args: tuple[str, pd.DataFrame, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Score all children in one litter under all models.

    Args:
        args: Tuple of (litter_name, litter_df, model_manifest).

    Returns:
        List of dicts with litter, child_idx, model_id, log_lik.
    """
    litter_name, df, manifest = args
    rows: list[dict[str, Any]] = []
    for entry in manifest:
        f = LitterFit(df, entry["spec"])
        f.fit()
        liks = f.child_lik()
        for i, lik in enumerate(liks):
            rows.append(
                {
                    "litter": litter_name,
                    "child_idx": int(df.index[i]),
                    "model_id": entry["model_id"],
                    "log_lik": float(np.log(max(lik, FLOOR))),
                }
            )
    return rows


def run_anomaly(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-child anomaly scores across all 30 models.

    Args:
        df: Full dataset with columns: litter, child, A_*/B_* parents, color/sweet/size/length.

    Returns:
        DataFrame with per-child per-model log-likelihoods and summary anomaly ranks.
        Columns: litter, child_idx, child_num, model_id, log_lik, mean_log_lik, overall_rank.
    """
    litters = [(name, group, MODEL_MANIFEST) for name, group in df.groupby("litter", sort=False)]

    all_rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor() as ex:
        for rows in ex.map(_score_litter, litters):
            all_rows.extend(rows)

    long = pd.DataFrame(all_rows)

    # Add child_num (position within litter, 1-indexed)
    child_num_map = {}
    for name, group in df.groupby("litter", sort=False):
        for pos, idx in enumerate(group.index, start=1):
            child_num_map[idx] = pos
    long["child_num"] = long["child_idx"].map(child_num_map)

    # Summary: mean log-lik across all models per child
    summary = (
        long.groupby(["litter", "child_idx", "child_num"])["log_lik"]
        .mean()
        .reset_index()
        .rename(columns={"log_lik": "mean_log_lik"})
    )
    summary["overall_rank"] = summary["mean_log_lik"].rank(method="first", ascending=True).astype(int)

    result = long.merge(summary, on=["litter", "child_idx", "child_num"])
    return result.sort_values(["overall_rank", "model_id"]).reset_index(drop=True)


def get_worst_children(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Return the N children with worst mean log-likelihood across all models.

    Args:
        df: Output of run_anomaly().
        n: Number of worst children to return.

    Returns:
        DataFrame with one row per child (worst first), with parent traits attached.
    """
    summary = (
        df.groupby(["litter", "child_idx", "child_num"])[["mean_log_lik", "overall_rank"]]
        .first()
        .reset_index()
    )
    return summary.nsmallest(n, "mean_log_lik").reset_index(drop=True)


def run_claim_anomaly(df: pd.DataFrame) -> pd.DataFrame:
    """Faster single-model anomaly scoring using only CLAIM.

    Args:
        df: Full dataset.

    Returns:
        DataFrame with per-child CLAIM log-likelihoods, sorted worst-first.
        Columns: litter, child_idx, child_num, log_lik, rank.
    """
    rows: list[dict[str, Any]] = []
    for name, group in df.groupby("litter", sort=False):
        f = LitterFit(group, CLAIM)
        f.fit()
        liks = f.child_lik()
        for pos, (idx, lik) in enumerate(zip(group.index, liks), start=1):
            rows.append(
                {
                    "litter": name,
                    "child_idx": int(idx),
                    "child_num": pos,
                    "log_lik": float(np.log(max(float(lik), FLOOR))),
                }
            )
    result = pd.DataFrame(rows)
    result["rank"] = result["log_lik"].rank(method="first", ascending=True).astype(int)
    # Attach parent and child trait values
    trait_cols = [f"A_{t}" for t in TRAITS] + [f"B_{t}" for t in TRAITS] + list(TRAITS)
    result = result.merge(
        df.reset_index()[["index", *trait_cols]].rename(columns={"index": "child_idx"}),
        on="child_idx",
        how="left",
    )
    return result.sort_values("rank").reset_index(drop=True)
