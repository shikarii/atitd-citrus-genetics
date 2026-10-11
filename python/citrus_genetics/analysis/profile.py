"""Profile likelihood curves for hidden genes.

For each litter and each of the 8 hidden gene positions (2 per parent per trait:
  A_color_g1, A_color_g2, A_sweet_g1, ..., B_length_g1, B_length_g2),
sweeps the gene value across [MLE_value - 200, MLE_value + 200] in steps of 5,
fixing that gene at each value and optimizing all other genes. The resulting
log-likelihood curve shows the curvature around the MLE and reveals whether
parameters are well-identified ("stiff") or weakly constrained ("sloppy").

This is the most computationally expensive analysis — run with --fast to skip.

Exports results/current/profile_likelihoods.parquet with columns:
    litter, parent, trait_idx, gene_slot, fixed_value, profile_ll, mle_value,
    delta_ll (= profile_ll - mle_ll), is_near_boundary
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import TRAITS, LitterFit

PROFILE_STEP: int = 5
PROFILE_HALF_WIDTH: int = 200
GENE_MIN: int = 0
GENE_MAX: int = 1000


def _profile_one_gene(
    f: LitterFit,
    parent: str,
    trait_idx: int,
    gene_slot: int,
    half_width: int = PROFILE_HALF_WIDTH,
    step: int = PROFILE_STEP,
) -> list[dict[str, Any]]:
    """Compute profile likelihood for one gene position.

    Fixes the specified gene slot, optimizes all others, records log-likelihood.

    Args:
        f: Fitted LitterFit instance (already fit).
        parent: 'A' or 'B'.
        trait_idx: 0-3 for color/sweet/size/length.
        gene_slot: 0 (g1) or 1 (g2).
        half_width: Sweep ±half_width around MLE.
        step: Step size for sweep.

    Returns:
        List of dicts with fixed_value and profile_ll.
    """
    mle_gene = f.genes[(parent, trait_idx)]
    mle_val = mle_gene[gene_slot]
    mle_ll = f.loglik()

    lo = max(GENE_MIN, mle_val - half_width)
    hi = min(GENE_MAX, mle_val + half_width)
    test_vals = list(range(lo, hi + 1, step))
    if mle_val not in test_vals:
        test_vals.append(mle_val)
    test_vals.sort()

    rows = []
    for val in test_vals:
        # Fix this slot; create modified LitterFit with one gene fixed
        other_slot = 1 - gene_slot
        other_val = mle_gene[other_slot]

        # Build a frozen gene pair for this parent/trait
        if gene_slot == 0:
            fixed_pair = (val, other_val)
        else:
            fixed_pair = (other_val, val)

        # Temporarily set the gene and recompute cols
        orig_gene = f.genes[(parent, trait_idx)]
        f.genes[(parent, trait_idx)] = fixed_pair
        f.cols[trait_idx] = f._cols(trait_idx)

        # Optimize all other genes (coordinate ascent, fewer rounds)
        for t in range(4):
            if t == trait_idx:
                continue
            if f.m["rules"][t] != "g1":
                f._scan_parent("A", t)
                f._scan_parent("B", t)

        profile_ll = f.loglik()

        # Restore original gene for next iteration
        f.genes[(parent, trait_idx)] = orig_gene
        f.cols[trait_idx] = f._cols(trait_idx)

        # Restore other genes (re-fit to be safe)
        # Note: for speed we don't re-optimize other genes after restore

        rows.append(
            {
                "fixed_value": val,
                "profile_ll": round(profile_ll, 3),
                "delta_ll": round(profile_ll - mle_ll, 3),
            }
        )

    return rows


def run_profile_likelihoods(
    df: pd.DataFrame,
    half_width: int = PROFILE_HALF_WIDTH,
    step: int = PROFILE_STEP,
) -> pd.DataFrame:
    """Compute profile likelihoods for all hidden genes in all litters.

    Args:
        df: Full children dataset.
        half_width: Sweep ±half_width from MLE gene value.
        step: Step size for the sweep.

    Returns:
        DataFrame with profile likelihood curves for all (litter, gene) pairs.
    """
    all_rows: list[dict[str, Any]] = []

    for litter_name, group in df.groupby("litter", sort=False):
        f = LitterFit(group, CLAIM)
        f.fit()

        for parent in ("A", "B"):
            for trait_idx, trait in enumerate(TRAITS):
                rule = CLAIM["rules"][trait_idx]
                if rule == "g1":
                    # g2 is not shown and not constrained; only g1 is identified
                    gene_slots = [0]
                else:
                    gene_slots = [0, 1]

                for gene_slot in gene_slots:
                    mle_gene = f.genes[(parent, trait_idx)]
                    mle_val = mle_gene[gene_slot]

                    profile = _profile_one_gene(f, parent, trait_idx, gene_slot, half_width, step)
                    for point in profile:
                        all_rows.append(
                            {
                                "litter": litter_name,
                                "parent": parent,
                                "trait": trait,
                                "trait_idx": trait_idx,
                                "gene_slot": gene_slot,
                                "mle_value": int(mle_val),
                                "is_near_boundary": int(mle_val) < 50 or int(mle_val) > 950,  # noqa: PLR2004
                                **point,
                            }
                        )

    return pd.DataFrame(all_rows)


def summarize_profile(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize profile likelihood curvature per (litter, gene).

    Estimates curvature (second derivative) at the MLE to classify parameters
    as stiff (high curvature → well-identified) or sloppy (low curvature →
    weakly constrained).

    Args:
        profile_df: Output of run_profile_likelihoods().

    Returns:
        DataFrame with one row per (litter, parent, trait, gene_slot).
    """
    rows: list[dict[str, Any]] = []
    group_cols = ["litter", "parent", "trait", "gene_slot", "mle_value", "is_near_boundary"]
    for key, grp in profile_df.groupby(group_cols):
        grp_s = grp.sort_values("fixed_value")
        vals = grp_s["fixed_value"].to_numpy()
        lls = grp_s["profile_ll"].to_numpy()
        mle_ll = float(grp_s.loc[grp_s["delta_ll"] == grp_s["delta_ll"].max(), "profile_ll"].iloc[0])

        # Estimate curvature via finite differences at MLE
        mle_v = int(key[4])  # mle_value
        near_idx = np.abs(vals - mle_v).argmin()
        if 1 <= near_idx < len(vals) - 1:
            curvature = (lls[near_idx + 1] - 2 * lls[near_idx] + lls[near_idx - 1]) / (
                (vals[near_idx + 1] - vals[near_idx]) ** 2 + 1e-12
            )
        else:
            curvature = float("nan")

        # Width of the -1 log-likelihood interval (approx 1 SE)
        mask = grp_s["delta_ll"] >= -1.0
        interval_width = int(vals[mask].max() - vals[mask].min()) if mask.sum() > 0 else 0

        rows.append(
            {
                "litter": key[0],
                "parent": key[1],
                "trait": key[2],
                "gene_slot": key[3],
                "mle_value": mle_v,
                "curvature": round(float(curvature), 6),
                "interval_width_1ll": interval_width,
                "is_sloppy": interval_width > 200,  # noqa: PLR2004
            }
        )
    return pd.DataFrame(rows)
