"""Dev-only: run the model comparison pipeline to stdout.

Does NOT update results/current or create run directories.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from citrus_genetics.pipelines.compare import fit_claim_genes, run_comparison


def main() -> None:
    """Run model comparison and print results to stdout."""
    data_path = Path("data/children.csv")
    if not data_path.exists():
        print(f"ERROR: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} children")

    print("\n--- Model Comparison ---")
    comparison = run_comparison(df)
    cols = ["model_id", "model", "fit_ll", "cv_ll", "cv_vs_claim", "children_impossible"]
    print(comparison[cols].to_string(index=False))

    print("\n--- CLAIM Fitted Genes ---")
    genes = fit_claim_genes(df)
    print(pd.DataFrame(genes).to_string(index=False))


if __name__ == "__main__":
    main()
