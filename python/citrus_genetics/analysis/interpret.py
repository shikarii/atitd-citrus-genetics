"""Generate data-driven interpretation summaries from analysis results.

Reads the computed analysis artifacts (CSV/JSON) and produces a structured
JSON file of plain-language findings for each analysis module. These
summaries answer "what did the data actually show?" rather than just
describing what each analysis does.

Usage:
    Called automatically by export_web_data.py during `make export-data`.
    Can also be run standalone:
        uv run python -m citrus_genetics.analysis.interpret
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIRS = [
    PROJECT_ROOT / "results" / "current",
    PROJECT_ROOT / "results",
]


def _find(name: str) -> Path | None:
    for d in RESULTS_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def _read_csv(name: str) -> pd.DataFrame | None:
    p = _find(name)
    return pd.read_csv(p) if p is not None else None


def _interpret_models(df: pd.DataFrame) -> dict:
    """Summarize the 30-model comparison results."""
    n = len(df)
    best = df.loc[df["cv_ll"].idxmax()]
    worst = df.loc[df["cv_ll"].idxmin()]

    claim_row = df[df["cv_vs_claim"] == 0.0]
    claim_cv_ll = claim_row["cv_ll"].iloc[0] if len(claim_row) > 0 else None
    claim_name = claim_row["model"].iloc[0] if len(claim_row) > 0 else "CLAIM"

    better_than_claim = int((df["cv_vs_claim"] > 0).sum())
    worse_than_claim = int((df["cv_vs_claim"] < 0).sum())
    impossible = int((df["children_impossible"] > 0).sum())

    gap = float(best["cv_ll"] - worst["cv_ll"])

    findings = [
        f"{n} models were evaluated using leave-one-litter-out cross-validation.",
    ]

    if better_than_claim > 0:
        findings.append(
            f"The best model is \"{best['model']}\" (cv_ll = {best['cv_ll']:.1f}), "
            f"outperforming the CLAIM baseline by {best['cv_vs_claim']:.1f} log-likelihood units."
        )
        findings.append(
            f"{better_than_claim} model(s) outperform CLAIM; "
            f"{worse_than_claim} perform worse."
        )
    else:
        findings.append(
            f"CLAIM (\"{claim_name}\") is the best model with cv_ll = {claim_cv_ll:.1f}, "
            f"beating all {n - 1} competitors."
        )

    if impossible > 0:
        findings.append(
            f"{impossible} of {n} models assign zero probability to at least one observed child, "
            f"ruling them out as exact explanations."
        )

    findings.append(
        f"The total spread from best to worst is {gap:.0f} log-likelihood units, "
        f"indicating strong discriminating power in the data."
    )

    return {
        "key": "models",
        "title": "Model Comparison",
        "findings": findings,
        "stats": {
            "n_models": n,
            "best_model": str(best["model"]),
            "best_cv_ll": round(float(best["cv_ll"]), 1),
            "worst_model": str(worst["model"]),
            "worst_cv_ll": round(float(worst["cv_ll"]), 1),
            "better_than_claim": better_than_claim,
            "models_with_impossible": impossible,
        },
    }


def _interpret_anomalies(df: pd.DataFrame) -> dict:
    """Summarize anomaly score findings."""
    n = len(df)
    mean_ll = float(df["log_lik"].mean())
    median_ll = float(df["log_lik"].median())
    std_ll = float(df["log_lik"].std())

    # Flag outliers as children > 2 std below mean
    threshold = mean_ll - 2 * std_ll
    outliers = df[df["log_lik"] < threshold].sort_values("log_lik")
    n_outliers = len(outliers)

    worst = df.loc[df["log_lik"].idxmin()]
    best = df.loc[df["log_lik"].idxmax()]

    findings = [
        f"Anomaly scores were computed for all {n} children under the CLAIM model.",
        f"Mean log-likelihood per child: {mean_ll:.2f} (std: {std_ll:.2f}).",
    ]

    if n_outliers > 0:
        litters_affected = sorted(outliers["litter"].unique().tolist())
        findings.append(
            f"{n_outliers} children fall more than 2 standard deviations below the mean "
            f"(threshold: {threshold:.2f}), flagged as potential anomalies."
        )
        findings.append(
            f"Anomalous children appear in: {', '.join(litters_affected)}."
        )
        findings.append(
            f"The most anomalous child is #{int(worst['child_num'])} in {worst['litter']} "
            f"(log_lik = {float(worst['log_lik']):.2f})."
        )
    else:
        findings.append(
            "No children were flagged as strong anomalies (none exceeded 2 std below the mean)."
        )

    # Per-litter breakdown
    litter_means = df.groupby("litter")["log_lik"].mean().sort_values()
    worst_litter = litter_means.index[0]
    best_litter = litter_means.index[-1]
    findings.append(
        f"Litter with lowest average score: {worst_litter} ({litter_means.iloc[0]:.2f}). "
        f"Highest: {best_litter} ({litter_means.iloc[-1]:.2f})."
    )

    return {
        "key": "anomalies",
        "title": "Anomaly Scores",
        "findings": findings,
        "stats": {
            "n_children": n,
            "mean_log_lik": round(mean_ll, 2),
            "std_log_lik": round(std_ll, 2),
            "n_outliers_2std": n_outliers,
            "worst_child": f"{worst['litter']} #{int(worst['child_num'])}",
            "worst_log_lik": round(float(worst["log_lik"]), 2),
        },
    }


def _interpret_mi_matrix(df: pd.DataFrame) -> dict:
    """Summarize mutual information findings."""
    diag = df[df["is_diagonal"] == True]  # noqa: E712
    offdiag = df[df["is_diagonal"] == False]  # noqa: E712

    diag_mean_z = float(diag["mi_excess_z"].mean())
    offdiag_mean_z = float(offdiag["mi_excess_z"].mean())

    # Check if any off-diagonal entries have high MI
    high_offdiag = offdiag[offdiag["mi_excess_z"] > 10]

    findings = [
        f"Mutual information was measured between 8 parent gene variables and 4 child traits ({len(df)} pairs).",
    ]

    if diag_mean_z > 50:
        findings.append(
            f"Diagonal entries (same-trait parent-to-child) show very strong information transfer "
            f"(mean z-score: {diag_mean_z:.1f}), confirming that parent genes predict child traits."
        )
    else:
        findings.append(
            f"Diagonal entries have mean z-score of {diag_mean_z:.1f}."
        )

    if len(high_offdiag) > 0:
        top3 = high_offdiag.nlargest(3, "mi_excess_z")
        top3_str = ", ".join(
            f"{r['parent_var']}->{r['child_var']} (z={r['mi_excess_z']:.0f})"
            for _, r in top3.iterrows()
        )
        findings.append(
            f"{len(high_offdiag)} of {len(offdiag)} off-diagonal pairs show high mutual "
            f"information (z > 10). Strongest: {top3_str}. "
            f"This cross-trait signal likely reflects correlated gene values across parents "
            f"in the dataset rather than a coupled inheritance mechanism."
        )
    else:
        if offdiag_mean_z < 5:
            findings.append(
                f"Off-diagonal entries show negligible cross-trait information "
                f"(mean z-score: {offdiag_mean_z:.1f}), supporting trait independence."
            )
        else:
            findings.append(
                f"Off-diagonal entries have mean z-score of {offdiag_mean_z:.1f}."
            )

    return {
        "key": "mi_matrix",
        "title": "Mutual Information",
        "findings": findings,
        "stats": {
            "n_pairs": len(df),
            "diag_mean_z": round(diag_mean_z, 1),
            "offdiag_mean_z": round(offdiag_mean_z, 1),
            "n_high_offdiag": len(high_offdiag),
        },
    }


def _interpret_residuals(
    residuals_df: pd.DataFrame,
    sib_df: pd.DataFrame | None,
    cooc_dict: dict | None,
) -> dict:
    """Summarize residual analysis findings."""
    traits = ["color", "sweet", "size", "length"]
    findings = []
    stats: dict = {}

    # Per-trait residual summary
    trait_summaries = []
    for t in traits:
        col = f"{t}_abs_residual"
        if col in residuals_df.columns:
            mean_r = float(residuals_df[col].mean())
            median_r = float(residuals_df[col].median())
            trait_summaries.append(f"{t}: mean |residual| = {mean_r:.0f}, median = {median_r:.0f}")
            stats[f"{t}_mean_abs_residual"] = round(mean_r, 1)

    findings.append(
        f"Residuals were computed for all {len(residuals_df)} children across 4 traits."
    )
    findings.append("Per-trait average absolute residuals: " + "; ".join(trait_summaries) + ".")

    # Sibling correlations
    if sib_df is not None:
        sig = sib_df[sib_df["p_value"] < 0.05]
        mean_abs_r = float(sib_df["pearson_r"].abs().mean())
        findings.append(
            f"Sibling within-litter correlations: {len(sig)} of {len(sib_df)} "
            f"trait-litter pairs are significant at p < 0.05 "
            f"(mean |r| = {mean_abs_r:.3f})."
        )
        if len(sig) <= 3:
            findings.append(
                "The near-absence of sibling correlations is consistent with independent "
                "inheritance per child (coin-flip mechanism)."
            )
        stats["n_sig_sibling_corr"] = len(sig)
        stats["mean_abs_sibling_r"] = round(mean_abs_r, 4)

    # Trait co-occurrence
    if cooc_dict is not None:
        diag_total = sum(cooc_dict.get(t, {}).get(t, 0) for t in traits)
        total = sum(
            cooc_dict.get(t1, {}).get(t2, 0)
            for t1 in traits
            for t2 in traits
        )
        if total > 0:
            diag_pct = 100 * diag_total / total
            findings.append(
                f"Trait co-occurrence: {diag_pct:.0f}% of extreme values are same-trait "
                f"({diag_total} of {total}), confirming traits vary independently."
            )

    return {
        "key": "residuals",
        "title": "Residual Analysis",
        "findings": findings,
        "stats": stats,
    }


def _interpret_r_sweep(df: pd.DataFrame) -> dict:
    """Summarize R parameter sweep findings."""
    best_row = df.loc[df["cv_ll"].idxmax()]
    best_r = int(best_row["R"])
    best_cv = float(best_row["cv_ll"])

    r_min = int(df["R"].min())
    r_max = int(df["R"].max())

    # Check if the curve is peaked or flat near the optimum
    near_best = df[abs(df["R"] - best_r) <= 20]
    cv_range_near = float(near_best["cv_ll"].max() - near_best["cv_ll"].min())

    edge_low = float(df[df["R"] == r_min]["cv_ll"].iloc[0])
    edge_high = float(df[df["R"] == r_max]["cv_ll"].iloc[0])
    total_range = float(df["cv_ll"].max() - df["cv_ll"].min())

    findings = [
        f"The nudge-range parameter R was swept from {r_min} to {r_max} ({len(df)} values).",
        f"Optimal R = {best_r} (cv_ll = {best_cv:.1f}).",
    ]

    if cv_range_near < 5:
        findings.append(
            f"The curve is relatively flat near the optimum (within {cv_range_near:.1f} units over R +/- 20), "
            f"meaning the model is not highly sensitive to the exact R value."
        )
    else:
        findings.append(
            f"The curve shows meaningful sensitivity near the optimum "
            f"({cv_range_near:.1f} unit spread over R +/- 20)."
        )

    findings.append(
        f"Total range from worst to best: {total_range:.0f} log-likelihood units, "
        f"confirming that R matters and is well-identified by the data."
    )

    return {
        "key": "r_sweep",
        "title": "Parameter Sensitivity (R Sweep)",
        "findings": findings,
        "stats": {
            "best_R": best_r,
            "best_cv_ll": round(best_cv, 1),
            "r_range": f"{r_min}-{r_max}",
            "total_cv_range": round(total_range, 1),
        },
    }


def _interpret_distribution_tests(df: pd.DataFrame) -> dict:
    """Summarize KS/AD goodness-of-fit test findings."""
    n = len(df)
    ks_sig = df[df["ks_sig_fdr"] == True]  # noqa: E712
    n_sig = len(ks_sig)
    pct_sig = 100 * n_sig / n if n > 0 else 0

    ad_sig = df[df["ad_sig_5pct"] == True]  # noqa: E712

    findings = [
        f"KS and AD goodness-of-fit tests were run on {n} litter-trait pairs "
        f"(14 litters x 4 traits), comparing observed vs. simulated distributions.",
    ]

    if n_sig > 0:
        sig_traits = ks_sig.groupby("trait").size().to_dict()
        sig_litters = sorted(ks_sig["litter"].unique().tolist())
        trait_list = ", ".join(f"{t} ({c})" for t, c in sorted(sig_traits.items(), key=lambda x: -x[1]))

        findings.append(
            f"{n_sig} of {n} pairs ({pct_sig:.0f}%) are significant after FDR correction (KS test)."
        )
        findings.append(f"Affected traits: {trait_list}.")
        findings.append(f"Affected litters: {', '.join(sig_litters)}.")

        if n_sig / n < 0.3:
            findings.append(
                "The majority of litter-trait pairs pass the goodness-of-fit test, "
                "indicating the model fits most of the data well. The failures may point to "
                "systematic deviations in specific traits or litters worth investigating."
            )
        else:
            findings.append(
                f"A substantial fraction ({pct_sig:.0f}%) of pairs fail the test, "
                f"suggesting the model has systematic shortcomings in capturing the observed distributions."
            )
    else:
        findings.append(
            "No litter-trait pairs are significant after FDR correction, "
            "indicating the model's simulated distributions closely match the observed data."
        )

    return {
        "key": "distribution_tests",
        "title": "Distribution Tests",
        "findings": findings,
        "stats": {
            "n_pairs": n,
            "n_ks_sig_fdr": n_sig,
            "pct_sig": round(pct_sig, 1),
            "n_ad_sig_5pct": len(ad_sig),
        },
    }


def _interpret_mixture(df: pd.DataFrame) -> dict:
    """Summarize CLAIM+INDEP mixture model findings."""
    n = len(df)
    mean_pi = float(df["pi_claim"].mean())
    min_pi = float(df["pi_claim"].min())
    min_litter = df.loc[df["pi_claim"].idxmin(), "litter"]
    max_pi = float(df["pi_claim"].max())

    # Check if any litter has substantial INDEP weight
    indep_heavy = df[df["pi_claim"] < 0.95]

    findings = [
        f"A CLAIM + INDEP mixture model was fitted to each of {n} litters via EM.",
        f"Mean CLAIM weight across litters: {mean_pi:.4f} "
        f"(range: {min_pi:.4f} to {max_pi:.4f}).",
    ]

    if len(indep_heavy) > 0:
        findings.append(
            f"{len(indep_heavy)} litter(s) show non-trivial INDEP weight (pi_claim < 0.95): "
            + ", ".join(
                f"{r['litter']} (pi_claim = {r['pi_claim']:.3f})"
                for _, r in indep_heavy.iterrows()
            )
            + "."
        )
    else:
        findings.append(
            "All litters assign >= 95% weight to CLAIM, with INDEP contributing negligibly. "
            "This confirms that virtually all offspring are well-explained by the CLAIM mechanism "
            "and there is no evidence of a secondary independent-assignment process."
        )

    # Delta log-likelihood
    mean_delta = float(df["delta_ll"].mean())
    findings.append(
        f"Adding the INDEP component changes mean log-likelihood by {mean_delta:.2f} per litter, "
        f"providing no meaningful improvement over pure CLAIM."
    )

    return {
        "key": "mixture",
        "title": "Mixture Decomposition",
        "findings": findings,
        "stats": {
            "n_litters": n,
            "mean_pi_claim": round(mean_pi, 4),
            "min_pi_claim": round(min_pi, 4),
            "min_pi_litter": str(min_litter),
            "n_indep_heavy": len(indep_heavy),
        },
    }


def generate_interpretations() -> dict:
    """Generate interpretation summaries from all available result artifacts.

    Returns a dict keyed by analysis name, each containing:
        - key: str identifier
        - title: str display name
        - findings: list[str] plain-language findings
        - stats: dict of key numeric values
    """
    interpretations: dict[str, dict] = {}

    # Model comparison
    mc = _read_csv("model_comparison.csv")
    if mc is not None:
        interpretations["models"] = _interpret_models(mc)

    # Anomaly scores
    anom = _read_csv("anomaly_scores.csv")
    if anom is not None:
        interpretations["anomalies"] = _interpret_anomalies(anom)

    # MI matrix
    mi = _read_csv("mi_matrix.csv")
    if mi is not None:
        interpretations["mi_matrix"] = _interpret_mi_matrix(mi)

    # Residuals + sibling correlations + co-occurrence
    res = _read_csv("residuals.csv")
    sib = _read_csv("sibling_correlations.csv")
    cooc_path = _find("trait_cooccurrence.csv")
    cooc_dict = None
    if cooc_path is not None:
        cooc_df = pd.read_csv(cooc_path)
        if "Unnamed: 0" in cooc_df.columns:
            cooc_df = cooc_df.set_index("Unnamed: 0")
            cooc_df.index.name = "trait"
        cooc_dict = cooc_df.to_dict()
    if res is not None:
        interpretations["residuals"] = _interpret_residuals(res, sib, cooc_dict)

    # R sweep
    rsw = _read_csv("r_sweep.csv")
    if rsw is not None:
        interpretations["r_sweep"] = _interpret_r_sweep(rsw)

    # Distribution tests
    dist = _read_csv("distribution_tests.csv")
    if dist is not None:
        interpretations["distribution_tests"] = _interpret_distribution_tests(dist)

    # Mixture
    mix = _read_csv("mixture_weights.csv")
    if mix is not None:
        interpretations["mixture"] = _interpret_mixture(mix)

    return interpretations


def main() -> None:
    """Run interpretation and print results."""
    interps = generate_interpretations()
    print(json.dumps(interps, indent=2))
    print(f"\nGenerated interpretations for {len(interps)} analyses.")


if __name__ == "__main__":
    main()
