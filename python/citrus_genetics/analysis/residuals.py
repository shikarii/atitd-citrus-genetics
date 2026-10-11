"""Residual analysis for CLAIM fitted genes.

For each child, computes the residual between the observed trait value and
the most probable predicted value under the CLAIM MLE-fitted genes.

Also computes:
- Sibling correlations: Pearson r between sibling pairs within each litter
  for each trait (tests within-litter non-independence)
- Trait change co-occurrence: 4x4 matrix counting how often two traits
  both deviate by >50 from the parental range in the same child
  (tests inter-trait coupling not predicted by CLAIM)

Exports:
  results/current/residuals.csv
  results/current/sibling_correlations.csv
  results/current/trait_cooccurrence.csv
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import TRAITS, LitterFit, display


def _predicted_trait(rule: str, g_a: tuple[int, int], g_b: tuple[int, int], rround: str) -> list[int]:
    """Most probable displayed values under a gene pair set.

    Returns the display value for all 4 (parent coin) combinations and picks
    the mode.  When genes are fixed this gives the single deterministic value.

    Args:
        rule: Display rule.
        g_a: Parent A gene pair (g1, g2).
        g_b: Parent B gene pair (g1, g2).
        rround: Rounding mode.

    Returns:
        List of 4 displayed values (one per coin-flip combination).
    """
    pairs = [
        (g_a[0], g_a[1]),
        (g_b[0], g_b[1]),
        (g_a[0], g_b[1]),
        (g_b[0], g_a[1]),
    ]
    return [int(display(rule, np.array(g1), np.array(g2), rround)) for g1, g2 in pairs]


def run_residuals(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compute residuals, sibling correlations, and trait co-occurrence.

    Args:
        df: Full children dataset.

    Returns:
        Tuple of (residuals_df, sibling_corr_df, cooccurrence_df).
    """
    residual_rows: list[dict[str, Any]] = []
    sib_corr_rows: list[dict[str, Any]] = []

    # Trait change indicator: |observed - parent_range_min| > THRESHOLD
    CHANGE_THRESHOLD = 50
    cooccurrence = np.zeros((4, 4), dtype=int)

    for litter_name, group in df.groupby("litter", sort=False):
        f = LitterFit(group, CLAIM)
        f.fit()

        obs = group[TRAITS].to_numpy()
        rules = CLAIM["rules"]
        rround = CLAIM["rround"]

        for child_pos, (idx, child_row) in enumerate(group.iterrows(), start=1):
            child_obs = obs[child_pos - 1]
            row: dict[str, Any] = {"litter": litter_name, "child_idx": int(idx), "child_num": child_pos}
            for t, trait in enumerate(TRAITS):
                rule = rules[t]
                g_a = f.genes[("A", t)]
                g_b = f.genes[("B", t)]
                preds = _predicted_trait(rule, g_a, g_b, rround)
                mode_pred = int(max(set(preds), key=preds.count))
                residual = int(child_obs[t]) - mode_pred
                row[f"{trait}_observed"] = int(child_obs[t])
                row[f"{trait}_predicted"] = mode_pred
                row[f"{trait}_residual"] = residual
                row[f"{trait}_abs_residual"] = abs(residual)
            residual_rows.append(row)

        # Sibling correlations within this litter
        if len(group) >= 3:  # noqa: PLR2004
            for t, trait in enumerate(TRAITS):
                col = group[trait].to_numpy()
                # Pairwise correlations among all siblings
                if np.std(col) > 0:
                    # Use all sibling pairs (not just adjacent ones)
                    r_val, p_val = stats.pearsonr(col[:-1], col[1:])
                    sib_corr_rows.append(
                        {
                            "litter": litter_name,
                            "trait": trait,
                            "n_children": len(group),
                            "pearson_r": round(float(r_val), 4),
                            "p_value": round(float(p_val), 6),
                        }
                    )

        # Trait co-occurrence (traits that both change far from parental range)
        # Use parent A observed as reference (children inherit mix of A and B)
        parent_a = group[[f"A_{t}" for t in TRAITS]].iloc[0].to_numpy()
        parent_b = group[[f"B_{t}" for t in TRAITS]].iloc[0].to_numpy()
        parent_range_min = np.minimum(parent_a, parent_b)
        parent_range_max = np.maximum(parent_a, parent_b)
        for child_obs_row in obs:
            # A trait "changed" if it moved outside the parental range by >threshold
            changed = (child_obs_row < parent_range_min - CHANGE_THRESHOLD) | (
                child_obs_row > parent_range_max + CHANGE_THRESHOLD
            )
            for i in range(4):
                for j in range(4):
                    if changed[i] and changed[j]:
                        cooccurrence[i, j] += 1

    residuals_df = pd.DataFrame(residual_rows)
    sib_corr_df = pd.DataFrame(sib_corr_rows) if sib_corr_rows else pd.DataFrame(
        columns=["litter", "trait", "n_children", "pearson_r", "p_value"]
    )
    cooccurrence_df = pd.DataFrame(cooccurrence, index=TRAITS, columns=TRAITS)

    return residuals_df, sib_corr_df, cooccurrence_df


def summarize_residuals(residuals_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-trait residual summary statistics.

    Args:
        residuals_df: Output of run_residuals()[0].

    Returns:
        DataFrame with one row per trait: mean, std, skew, kurtosis, max_abs.
    """
    rows = []
    for trait in TRAITS:
        col = residuals_df[f"{trait}_residual"]
        rows.append(
            {
                "trait": trait,
                "mean": round(float(col.mean()), 2),
                "std": round(float(col.std()), 2),
                "skewness": round(float(stats.skew(col)), 3),
                "kurtosis": round(float(stats.kurtosis(col)), 3),
                "max_abs_residual": int(col.abs().max()),
                "pct_gt_100": round(float((col.abs() > 100).mean() * 100), 1),
            }
        )
    return pd.DataFrame(rows)
