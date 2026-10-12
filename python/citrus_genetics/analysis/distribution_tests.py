"""KS and Anderson-Darling goodness-of-fit tests for CLAIM.

For each (litter, trait) pair (14 × 4 = 56 tests):
1. Simulate N_SIMS children from the CLAIM MLE fitted genes
2. Run a two-sample KS test comparing observed vs simulated distributions
3. Run a two-sample Anderson-Darling test
4. Apply Benjamini-Hochberg FDR correction across all 56 KS p-values

A significant result means the simulated CLAIM distribution does not match
the observed distribution for that litter and trait, suggesting model misfit.

Exports results/current/distribution_tests.csv with columns:
    litter, trait, n_observed, n_simulated,
    ks_stat, ks_pvalue, ks_pvalue_fdr,
    ad_stat, ad_critical_1pct, ad_critical_5pct, ad_sig_5pct
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import TRAITS, LitterFit, simulate

N_SIMS: int = 500
FDR_ALPHA: float = 0.05


def _bh_correct(pvalues: list[float], alpha: float = FDR_ALPHA) -> list[float]:
    """Apply Benjamini-Hochberg FDR correction.

    Args:
        pvalues: List of raw p-values.
        alpha: FDR threshold.

    Returns:
        List of adjusted p-values (same order as input).
    """
    n = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda x: x[1])
    adjusted = [0.0] * n
    min_adj = 1.0
    for rank, (orig_idx, p) in enumerate(reversed(indexed), start=1):
        adj = min(p * n / (n - rank + 1), 1.0)
        min_adj = min(min_adj, adj)
        adjusted[orig_idx] = min_adj
    return adjusted


def run_distribution_tests(df: pd.DataFrame, n_sims: int = N_SIMS, seed: int = 99) -> pd.DataFrame:
    """Run KS and AD goodness-of-fit tests for each (litter, trait).

    Args:
        df: Full children dataset.
        n_sims: Number of simulated children per litter.
        seed: Random seed for simulations.

    Returns:
        DataFrame with test results, sorted by ks_pvalue_fdr ascending.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    for litter_name, group in df.groupby("litter", sort=False):
        f = LitterFit(group, CLAIM)
        f.fit()
        observed = group[TRAITS].to_numpy()
        simulated = simulate(f, n_sims, rng)

        for t, trait in enumerate(TRAITS):
            obs_t = observed[:, t].astype(float)
            sim_t = simulated[:, t].astype(float)

            ks_stat, ks_p = stats.ks_2samp(obs_t, sim_t, alternative="two-sided")

            # Two-sample AD test
            import warnings as _warnings
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore", UserWarning)
                ad_result = stats.anderson_ksamp([obs_t, sim_t])
            ad_stat = float(ad_result.statistic)
            ad_crit = ad_result.critical_values
            ad_crit_5pct = float(ad_crit[2])
            ad_crit_1pct = float(ad_crit[4]) if len(ad_crit) > 4 else float("nan")  # noqa: PLR2004
            ad_sig_5pct = bool(ad_result.pvalue < 0.05)

            rows.append(
                {
                    "litter": litter_name,
                    "trait": trait,
                    "n_observed": len(group),
                    "n_simulated": n_sims,
                    "ks_stat": round(float(ks_stat), 4),
                    "ks_pvalue": round(float(ks_p), 6),
                    "ad_stat": round(float(ad_stat), 4),
                    "ad_critical_5pct": round(float(ad_crit_5pct), 4),
                    "ad_critical_1pct": round(float(ad_crit_1pct), 4),
                    "ad_sig_5pct": ad_sig_5pct,
                }
            )

    result_df = pd.DataFrame(rows)

    # BH-FDR correction on KS p-values
    result_df["ks_pvalue_fdr"] = [round(p, 6) for p in _bh_correct(result_df["ks_pvalue"].tolist())]
    result_df["ks_sig_fdr"] = result_df["ks_pvalue_fdr"] < FDR_ALPHA

    return result_df.sort_values("ks_pvalue_fdr").reset_index(drop=True)


def summarize_tests(tests_df: pd.DataFrame) -> dict[str, Any]:
    """Summarize distribution test results.

    Args:
        tests_df: Output of run_distribution_tests().

    Returns:
        Dict with counts of significant results.
    """
    return {
        "n_tests": len(tests_df),
        "n_ks_sig_raw": int((tests_df["ks_pvalue"] < FDR_ALPHA).sum()),
        "n_ks_sig_fdr": int(tests_df["ks_sig_fdr"].sum()),
        "n_ad_sig_5pct": int(tests_df["ad_sig_5pct"].sum()),
        "worst_litter": str(tests_df.iloc[0]["litter"]),
        "worst_trait": str(tests_df.iloc[0]["trait"]),
        "worst_ks_stat": float(tests_df.iloc[0]["ks_stat"]),
    }
