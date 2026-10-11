"""Cached data loading for the Streamlit dashboard.

All functions are decorated with @st.cache_data so results are cached
for the session. The dashboard can be launched before running all pipelines;
missing artifact files degrade gracefully with None returns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

RESULTS_DIR = Path("results/current")
DATA_DIR = Path("data")


def _safe_read_csv(path: Path) -> pd.DataFrame | None:
    """Read a CSV file, returning None if it does not exist."""
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return None


def _safe_read_parquet(path: Path) -> pd.DataFrame | None:
    """Read a Parquet file, returning None if it does not exist."""
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception:  # noqa: BLE001
        return None


@st.cache_data(ttl=300)
def load_children() -> pd.DataFrame | None:
    """Load the raw children dataset."""
    p = RESULTS_DIR / "children.csv"
    if not p.exists():
        p = DATA_DIR / "children.csv"
    return _safe_read_csv(p)


@st.cache_data(ttl=300)
def load_model_comparison() -> pd.DataFrame | None:
    """Load 30-model comparison results."""
    return _safe_read_csv(RESULTS_DIR / "model_comparison.csv")


@st.cache_data(ttl=300)
def load_fitted_genes() -> pd.DataFrame | None:
    """Load CLAIM MLE-fitted genes per litter."""
    return _safe_read_csv(RESULTS_DIR / "fitted_genes_claim.csv")


@st.cache_data(ttl=300)
def load_anomaly_scores() -> pd.DataFrame | None:
    """Load per-child anomaly scores under CLAIM."""
    return _safe_read_csv(RESULTS_DIR / "anomaly_scores.csv")


@st.cache_data(ttl=300)
def load_mi_matrix() -> pd.DataFrame | None:
    """Load mutual information matrix (long format)."""
    return _safe_read_csv(RESULTS_DIR / "mi_matrix.csv")


@st.cache_data(ttl=300)
def load_residuals() -> pd.DataFrame | None:
    """Load per-child residuals under CLAIM."""
    return _safe_read_csv(RESULTS_DIR / "residuals.csv")


@st.cache_data(ttl=300)
def load_sibling_correlations() -> pd.DataFrame | None:
    """Load sibling correlation results."""
    return _safe_read_csv(RESULTS_DIR / "sibling_correlations.csv")


@st.cache_data(ttl=300)
def load_trait_cooccurrence() -> pd.DataFrame | None:
    """Load trait co-occurrence matrix (4x4)."""
    df = _safe_read_csv(RESULTS_DIR / "trait_cooccurrence.csv")
    if df is not None and "Unnamed: 0" in df.columns:
        df = df.set_index("Unnamed: 0")
        df.index.name = "trait"
    return df


@st.cache_data(ttl=300)
def load_r_sweep() -> pd.DataFrame | None:
    """Load R parameter sweep results."""
    return _safe_read_csv(RESULTS_DIR / "r_sweep.csv")


@st.cache_data(ttl=300)
def load_distribution_tests() -> pd.DataFrame | None:
    """Load KS/AD distribution test results."""
    return _safe_read_csv(RESULTS_DIR / "distribution_tests.csv")


@st.cache_data(ttl=300)
def load_mixture_weights() -> pd.DataFrame | None:
    """Load CLAIM+INDEP mixture weights per litter."""
    return _safe_read_csv(RESULTS_DIR / "mixture_weights.csv")


@st.cache_data(ttl=600)
def load_profile_likelihoods() -> pd.DataFrame | None:
    """Load profile likelihood curves (large file)."""
    return _safe_read_parquet(RESULTS_DIR / "profile_likelihoods.parquet")


@st.cache_data(ttl=300)
def load_ppc_summary() -> dict[str, Any] | None:
    """Load PPC summary JSON."""
    import json
    p = RESULTS_DIR / "ppc_summary.json"
    if not p.exists():
        return None
    try:
        return dict(json.loads(p.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        return None


def results_available() -> bool:
    """Check if results/current exists and has the model comparison CSV."""
    return (RESULTS_DIR / "model_comparison.csv").exists()


def missing_artifacts() -> list[str]:
    """Return list of expected artifact names that are not yet present."""
    expected = [
        "model_comparison.csv",
        "fitted_genes_claim.csv",
        "anomaly_scores.csv",
        "mi_matrix.csv",
        "residuals.csv",
        "r_sweep.csv",
        "distribution_tests.csv",
        "mixture_weights.csv",
    ]
    return [name for name in expected if not (RESULTS_DIR / name).exists()]
