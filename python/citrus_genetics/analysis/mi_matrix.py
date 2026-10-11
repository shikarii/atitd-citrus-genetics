"""Mutual information matrix between parent and child traits.

Computes the mutual information (MI) between each of the 8 parent trait
variables (A_color, A_sweet, A_size, A_length, B_color, B_sweet, B_size,
B_length) and each of the 4 child trait variables (color, sweet, size, length).

Under CLAIM, the MI matrix should be block-diagonal: each parent trait pair
influences only the corresponding child trait. Off-diagonal entries indicate
unexplained inter-trait coupling that CLAIM does not predict.

A shuffled baseline is computed by permuting child columns to estimate MI
under the null hypothesis of independence.

Exports results/current/mi_matrix.csv with columns:
    parent_var, child_var, mi_observed, mi_shuffled, mi_excess
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression  # type: ignore[import-untyped]

from citrus_genetics.core.constants import TRAITS

PARENT_VARS: list[str] = [f"{p}_{t}" for p in ("A", "B") for t in TRAITS]
N_SHUFFLES: int = 10


def _mi_matrix_from_arrays(X: np.ndarray, Y: np.ndarray, random_state: int = 0) -> np.ndarray:
    """Compute MI between each column of X and each column of Y.

    Args:
        X: Feature matrix of shape (n, p).
        Y: Target matrix of shape (n, q).
        random_state: Seed for sklearn MI estimator.

    Returns:
        MI matrix of shape (p, q).
    """
    p = X.shape[1]
    q = Y.shape[1]
    mi = np.zeros((p, q))
    for j in range(q):
        mi[:, j] = mutual_info_regression(X, Y[:, j], discrete_features=False, n_neighbors=3, random_state=random_state)
    return mi


def run_mi_matrix(df: pd.DataFrame, n_shuffles: int = N_SHUFFLES, seed: int = 42) -> pd.DataFrame:
    """Compute the observed MI matrix and shuffled baseline.

    Args:
        df: Full children dataset.
        n_shuffles: Number of shuffle repetitions for baseline.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with one row per (parent_var, child_var) pair.
        Columns: parent_var, child_var, mi_observed, mi_shuffled_mean,
                 mi_shuffled_std, mi_excess, mi_excess_z.
    """
    X = df[PARENT_VARS].to_numpy(dtype=float)
    Y = df[TRAITS].to_numpy(dtype=float)

    observed = _mi_matrix_from_arrays(X, Y, random_state=seed)

    rng = np.random.default_rng(seed)
    shuffled_runs = []
    for i in range(n_shuffles):
        Y_shuf = Y.copy()
        for j in range(Y_shuf.shape[1]):
            rng.shuffle(Y_shuf[:, j])
        shuffled_runs.append(_mi_matrix_from_arrays(X, Y_shuf, random_state=seed + i))

    shuffled_mean = np.mean(shuffled_runs, axis=0)
    shuffled_std = np.std(shuffled_runs, axis=0) + 1e-12

    rows = []
    for pi, pvar in enumerate(PARENT_VARS):
        for ci, cvar in enumerate(TRAITS):
            mi_obs = float(observed[pi, ci])
            mi_sh = float(shuffled_mean[pi, ci])
            mi_std = float(shuffled_std[pi, ci])
            rows.append(
                {
                    "parent_var": pvar,
                    "child_var": cvar,
                    "mi_observed": round(mi_obs, 6),
                    "mi_shuffled_mean": round(mi_sh, 6),
                    "mi_shuffled_std": round(mi_std, 6),
                    "mi_excess": round(mi_obs - mi_sh, 6),
                    "mi_excess_z": round((mi_obs - mi_sh) / mi_std, 3),
                    "is_diagonal": _is_diagonal(pvar, cvar),
                }
            )

    return pd.DataFrame(rows)


def _is_diagonal(parent_var: str, child_var: str) -> bool:
    """Return True if this (parent, child) pair is on-diagonal under CLAIM.

    Under CLAIM, each trait is controlled by 2 genes (one per parent), so
    A_color and B_color both causally influence child color only.

    Args:
        parent_var: e.g. 'A_color' or 'B_sweet'.
        child_var: e.g. 'color' or 'sweet'.

    Returns:
        True if the parent trait matches the child trait.
    """
    return parent_var.endswith(child_var)


def pivot_mi_matrix(df: pd.DataFrame, value_col: str = "mi_observed") -> pd.DataFrame:
    """Pivot MI results into a parent × child matrix for heatmap display.

    Args:
        df: Output of run_mi_matrix().
        value_col: Which MI column to pivot.

    Returns:
        DataFrame with parent_var rows and child_var columns.
    """
    return df.pivot(index="parent_var", columns="child_var", values=value_col)[TRAITS].loc[PARENT_VARS]
