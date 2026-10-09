"""Result file serialization for run artifacts."""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003
from typing import Any

import pandas as pd


def write_model_comparison(df: pd.DataFrame, path: Path) -> None:
    """Write model comparison results to CSV.

    Args:
        df: Model comparison DataFrame.
        path: Output file path.
    """
    df.to_csv(path, index=False)


def write_fitted_genes(data: list[dict[str, Any]], path: Path) -> None:
    """Write fitted CLAIM genes to CSV.

    Args:
        data: List of per-litter gene dicts.
        path: Output file path.
    """
    pd.DataFrame(data).to_csv(path, index=False)


def write_ppc_summary(
    obs_k: Any,
    obs_tr: Any,
    sim_k: Any,
    sim_tr: Any,
    n_sims: int,
    path: Path,
) -> None:
    """Write plug-in predictive check summary to JSON.

    Args:
        obs_k: Observed change-count bins, shape (3,).
        obs_tr: Observed per-trait changes, shape (4,).
        sim_k: Simulated change-count bins, shape (n_sims, 3).
        sim_tr: Simulated per-trait changes, shape (n_sims, 4).
        n_sims: Number of simulations.
        path: Output file path.
    """
    import numpy as np  # noqa: PLC0415

    from citrus_genetics.core.constants import TRAITS  # noqa: PLC0415

    metrics = []
    labels_k = ["0 traits changed", "1 trait changed", "2+ traits changed"]
    for label, obs, sims in zip(labels_k, obs_k, sim_k.T, strict=True):
        metrics.append(
            {
                "name": label,
                "observed": int(obs),
                "simulated_mean": round(float(sims.mean()), 1),
                "simulated_p2_5": round(float(np.percentile(sims, 2.5)), 1),
                "simulated_p97_5": round(float(np.percentile(sims, 97.5)), 1),
            }
        )
    for trait, obs, sims in zip(TRAITS, obs_tr, sim_tr.T, strict=True):
        metrics.append(
            {
                "name": f"{trait} changed",
                "observed": int(obs),
                "simulated_mean": round(float(sims.mean()), 1),
                "simulated_p2_5": round(float(np.percentile(sims, 2.5)), 1),
                "simulated_p97_5": round(float(np.percentile(sims, 97.5)), 1),
            }
        )
    summary = {"n_simulations": n_sims, "metrics": metrics}
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_ppc_distributions(
    obs_k: Any,
    obs_tr: Any,
    sim_k: Any,
    sim_tr: Any,
    path: Path,
) -> None:
    """Write full PPC simulated distributions to Parquet.

    Args:
        obs_k: Observed change-count bins.
        obs_tr: Observed per-trait changes.
        sim_k: Simulated change-count bins.
        sim_tr: Simulated per-trait changes.
        path: Output file path.
    """
    import numpy as np  # noqa: PLC0415

    from citrus_genetics.core.constants import TRAITS  # noqa: PLC0415

    records = []
    labels_k = ["0 traits changed", "1 trait changed", "2+ traits changed"]
    for label, obs, sims in zip(labels_k, obs_k, sim_k.T, strict=True):
        records.append(
            {
                "metric": label,
                "observed": int(obs),
                "simulated_values": [int(x) for x in np.asarray(sims)],
            }
        )
    for trait, obs, sims in zip(TRAITS, obs_tr, sim_tr.T, strict=True):
        records.append(
            {
                "metric": f"{trait} changed",
                "observed": int(obs),
                "simulated_values": [int(x) for x in np.asarray(sims)],
            }
        )
    pd.DataFrame(records).to_parquet(path, index=False)
