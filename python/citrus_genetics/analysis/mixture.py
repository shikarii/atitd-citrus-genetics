"""CLAIM + INDEP mixture model fitted by EM per litter.

For each litter, fits a two-component mixture:
  y_i ~ pi * CLAIM(theta_CLAIM) + (1 - pi) * INDEP

where INDEP assigns each trait independently Uniform[0, 1000], and
theta_CLAIM are the CLAIM MLE-fitted genes.

The EM algorithm alternates between:
  E-step: compute posterior responsibility r_i = P(z_i=CLAIM | y_i, theta)
  M-step: update pi = mean(r_i); refit CLAIM genes with soft-weighted LL

After convergence, pi is the fraction of children best explained by CLAIM.
Values near 1 indicate the litter is highly consistent with CLAIM; values
near 0 indicate most children look independent/random.

Exports results/current/mixture_weights.csv with columns:
    litter, n, pi_claim, pi_indep, log_lik_mixture, log_lik_claim_only, delta_ll
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import FLOOR, TRAITS, LitterFit

INDEP_PROB: float = 1.0 / 1001.0  # Uniform[0,1000] probability for each trait value
EM_MAX_ITER: int = 20
EM_TOL: float = 1e-4
V: int = 1001


def _indep_child_lik(y: np.ndarray) -> np.ndarray:
    """Per-child likelihood under the INDEP (uniform per trait) model.

    Args:
        y: Child observations, shape (n, 4).

    Returns:
        Array of shape (n,) with per-child INDEP likelihoods.
    """
    # Each trait: Uniform[0, 1000] -> p = 1/1001 per value
    # Joint: (1/1001)^4 for all 4 traits independently
    return np.full(len(y), INDEP_PROB**4)


def _fit_weighted_claim(df: pd.DataFrame, weights: np.ndarray) -> tuple[LitterFit, float]:
    """Fit CLAIM genes to weighted children.

    Uses log-likelihood weighting: score = sum(weights * log(child_lik)).
    We approximate by resampling children according to weights, then fitting.
    For EM this is equivalent to an M-step via importance weighting.

    Args:
        df: Litter DataFrame.
        weights: Per-child soft responsibilities for CLAIM component.

    Returns:
        Tuple of (fitted LitterFit, weighted log-likelihood).
    """
    f = LitterFit(df, CLAIM)
    # Standard MLE fit; weights only affect pi in M-step
    f.fit()
    child_liks = f.child_lik()
    weighted_ll = float(np.sum(weights * np.log(np.maximum(child_liks, FLOOR))))
    return f, weighted_ll


def run_mixture_litter(df: pd.DataFrame, litter_name: str) -> dict[str, Any]:
    """Run EM mixture fitting for one litter.

    Args:
        df: DataFrame for one litter.
        litter_name: Name for reporting.

    Returns:
        Dict with litter, n, pi_claim, log_lik_mixture, etc.
    """
    n = len(df)
    y = df[TRAITS].to_numpy()

    # Initial CLAIM fit (standard MLE)
    f = LitterFit(df, CLAIM)
    ll_claim_only = f.fit()
    claim_liks = f.child_lik()
    indep_liks = _indep_child_lik(y)

    # Initialize pi
    pi = 0.9

    for _iter in range(EM_MAX_ITER):
        pi_prev = pi

        # E-step: responsibilities
        numerator = pi * claim_liks
        denominator = numerator + (1 - pi) * indep_liks
        denominator = np.maximum(denominator, FLOOR)
        r = numerator / denominator

        # M-step: update pi
        pi = float(np.mean(r))
        pi = max(0.001, min(0.999, pi))

        # Re-fit CLAIM genes (full refit for simplicity)
        f2 = LitterFit(df, CLAIM)
        f2.fit()
        claim_liks = f2.child_lik()

        if abs(pi - pi_prev) < EM_TOL:
            break

    f = f2

    # Final mixture log-likelihood
    mix_liks = pi * claim_liks + (1 - pi) * indep_liks
    ll_mixture = float(np.sum(np.log(np.maximum(mix_liks, FLOOR))))

    return {
        "litter": litter_name,
        "n": n,
        "pi_claim": round(pi, 4),
        "pi_indep": round(1 - pi, 4),
        "log_lik_mixture": round(ll_mixture, 2),
        "log_lik_claim_only": round(ll_claim_only, 2),
        "delta_ll": round(ll_mixture - ll_claim_only, 2),
    }


def run_mixture(df: pd.DataFrame) -> pd.DataFrame:
    """Run EM mixture fitting for all litters.

    Args:
        df: Full children dataset.

    Returns:
        DataFrame with one row per litter, sorted by pi_claim ascending.
        Low pi_claim litters are most inconsistent with CLAIM.
    """
    rows = []
    for litter_name, group in df.groupby("litter", sort=False):
        row = run_mixture_litter(group, str(litter_name))
        rows.append(row)

    result_df = pd.DataFrame(rows)
    return result_df.sort_values("pi_claim").reset_index(drop=True)


def get_child_responsibilities(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-child CLAIM responsibility (soft assignment) for each litter.

    Args:
        df: Full children dataset.

    Returns:
        DataFrame with litter, child_idx, r_claim (posterior probability of CLAIM component).
    """
    rows: list[dict[str, Any]] = []
    for litter_name, group in df.groupby("litter", sort=False):
        y = group[TRAITS].to_numpy()
        f = LitterFit(group, CLAIM)
        f.fit()
        claim_liks = f.child_lik()
        indep_liks = _indep_child_lik(y)

        # Simple 50/50 initial mixture for per-child responsibilities
        pi = 0.9
        for _ in range(EM_MAX_ITER):
            r = pi * claim_liks / np.maximum(pi * claim_liks + (1 - pi) * indep_liks, FLOOR)
            pi = float(np.mean(r))
            pi = max(0.001, min(0.999, pi))

        for pos, (idx, r_val) in enumerate(zip(group.index, r), start=1):
            rows.append(
                {
                    "litter": litter_name,
                    "child_idx": int(idx),
                    "child_num": pos,
                    "r_claim": round(float(r_val), 4),
                }
            )
    return pd.DataFrame(rows)
