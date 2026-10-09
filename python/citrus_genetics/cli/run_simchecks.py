"""Dev-only: run the validation pipeline to stdout.

Does NOT update results/current or create run directories.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from citrus_genetics.core.constants import TRAITS
from citrus_genetics.pipelines.sim_checks import DEFAULT_MODELS, ppc, recovery_job


def main() -> None:
    """Run validation checks and print results to stdout."""
    data_path = Path("data/children.csv")
    if not data_path.exists():
        print(f"ERROR: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} children")

    print("\n--- Model Recovery ---")
    for gen in DEFAULT_MODELS:
        for seed in (11, 12, 13):
            result = recovery_job(df, gen, seed)
            fit_ll = result["fit_ll"]
            cv_ll = result["cv_ll"]
            for label, scores in (("fit", fit_ll), ("held-out", cv_ll)):
                winner = max(scores, key=lambda k: scores[k])
                status = "OK" if winner == gen else "WRONG"
                score_str = ", ".join(f"{k} {v}" for k, v in scores.items())
                print(f"  {gen:6s} seed {seed}, {label:8s}: {score_str}  -> best: {winner} {status}")

    print("\n--- Plug-In Predictive Check ---")
    obs_k, obs_tr, sim_k, sim_tr = ppc(df)
    labels_k = ["0 traits changed", "1 trait changed", "2+ traits changed"]
    for label, obs, sims in zip(labels_k, obs_k, sim_k.T, strict=False):
        lo = np.percentile(sims, 2.5)
        hi = np.percentile(sims, 97.5)
        print(f"  {label:28s} real {int(obs):4d}   sim mean {sims.mean():6.1f}, 95% range {lo:.0f}-{hi:.0f}")
    for trait, obs, sims in zip(TRAITS, obs_tr, sim_tr.T, strict=False):
        lo = np.percentile(sims, 2.5)
        hi = np.percentile(sims, 97.5)
        sim_mean = sims.mean()
        print(
            f"  {trait:8s} changed"
            f"            real {int(obs):4d}"
            f"   sim mean {sim_mean:6.1f}, 95% range {lo:.0f}-{hi:.0f}"
        )


if __name__ == "__main__":
    main()
