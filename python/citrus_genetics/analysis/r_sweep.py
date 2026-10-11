"""Nudge-range (R) parameter sweep analysis.

Sweeps the nudge radius R from 50 to 300 in steps of 5, holding all other
parameters fixed at CLAIM defaults. For each R value, computes:
- fit_ll: in-sample log-likelihood across all 14 litters
- cv_ll: 2-fold cross-validated log-likelihood

This tests the sensitivity of CLAIM's ranking to the R=150 assumption and
identifies the R value that maximizes each score.

Exports results/current/r_sweep.csv with columns:
    R, fit_ll, cv_ll, delta_fit (vs CLAIM R=150), delta_cv (vs CLAIM R=150)
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.pipelines.compare import run_single_model

R_MIN: int = 50
R_MAX: int = 300
R_STEP: int = 5

CLAIM_R: int = 150


def _sweep_single_r(args: tuple[int, pd.DataFrame]) -> dict[str, Any]:
    """Fit one R value and return scores.

    Args:
        args: Tuple of (R_value, children_dataframe).

    Returns:
        Dict with R, fit_ll, cv_ll.
    """
    r_val, df = args
    spec = {**CLAIM, "R": r_val}
    result = run_single_model(f"uniform +-{r_val}", spec, df)
    return {"R": r_val, "fit_ll": result["fit_ll"], "cv_ll": result["cv_ll"]}


def run_r_sweep(df: pd.DataFrame, r_min: int = R_MIN, r_max: int = R_MAX, r_step: int = R_STEP) -> pd.DataFrame:
    """Sweep nudge radius R and compute fit/cv scores.

    Args:
        df: Full children dataset.
        r_min: Minimum R to test.
        r_max: Maximum R to test (inclusive).
        r_step: Step size between R values.

    Returns:
        DataFrame sorted by R with columns: R, fit_ll, cv_ll, delta_fit, delta_cv.
    """
    r_values = list(range(r_min, r_max + 1, r_step))
    jobs = [(r, df) for r in r_values]

    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor() as ex:
        for result in ex.map(_sweep_single_r, jobs):
            rows.append(result)

    result_df = pd.DataFrame(rows).sort_values("R").reset_index(drop=True)

    # Reference scores at CLAIM's R=150
    claim_row = result_df[result_df["R"] == CLAIM_R]
    if len(claim_row) > 0:
        ref_fit = float(claim_row["fit_ll"].iloc[0])
        ref_cv = float(claim_row["cv_ll"].iloc[0])
    else:
        # Run CLAIM R=150 explicitly if not in sweep
        ref = run_single_model("CLAIM", CLAIM, df)
        ref_fit = float(ref["fit_ll"])
        ref_cv = float(ref["cv_ll"])

    result_df["delta_fit"] = (result_df["fit_ll"] - ref_fit).round(1)
    result_df["delta_cv"] = (result_df["cv_ll"] - ref_cv).round(1)

    return result_df


def find_optimal_r(sweep_df: pd.DataFrame) -> dict[str, Any]:
    """Find the R value that maximizes fit_ll and cv_ll.

    Args:
        sweep_df: Output of run_r_sweep().

    Returns:
        Dict with best_r_fit, best_fit_ll, best_r_cv, best_cv_ll.
    """
    best_fit_idx = sweep_df["fit_ll"].idxmax()
    best_cv_idx = sweep_df["cv_ll"].idxmax()
    return {
        "best_r_fit": int(sweep_df.loc[best_fit_idx, "R"]),
        "best_fit_ll": float(sweep_df.loc[best_fit_idx, "fit_ll"]),
        "best_r_cv": int(sweep_df.loc[best_cv_idx, "R"]),
        "best_cv_ll": float(sweep_df.loc[best_cv_idx, "cv_ll"]),
        "claim_r": CLAIM_R,
        "n_r_values": len(sweep_df),
    }


def compute_r_sensitivity(sweep_df: pd.DataFrame, window: int = 3) -> float:
    """Compute local sensitivity of fit_ll to R changes near CLAIM_R=150.

    Args:
        sweep_df: Output of run_r_sweep().
        window: Number of R steps on each side to include.

    Returns:
        Max absolute change in fit_ll per unit R change near CLAIM_R.
    """
    near = sweep_df[
        (sweep_df["R"] >= CLAIM_R - window * R_STEP) & (sweep_df["R"] <= CLAIM_R + window * R_STEP)
    ].sort_values("R")
    if len(near) < 2:  # noqa: PLR2004
        return float("nan")
    diffs = np.abs(np.diff(near["fit_ll"].to_numpy()))
    steps = np.diff(near["R"].to_numpy())
    return float(np.max(diffs / steps))
