"""Export analysis artifacts as JSON for the React web dashboard.

Reads CSV/parquet artifacts from results/current/ (or results/ fallback),
converts to JSON, copies the research methodology markdown, and writes
run metadata. Output goes to web/public/data/.

Usage:
    uv run python -m citrus_genetics.cli.export_web_data
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIRS = [
    PROJECT_ROOT / "results" / "current",
    PROJECT_ROOT / "results",
]
OUTPUT_DIR = PROJECT_ROOT / "web" / "public" / "data"
METHODOLOGY_SRC = PROJECT_ROOT / "docs" / "research_methodology.md"
CHILDREN_SRC = PROJECT_ROOT / "data" / "children.csv"

CSV_ARTIFACTS = {
    "model_comparison.csv": "model_comparison.json",
    "mi_matrix.csv": "mi_matrix.json",
    "anomaly_scores.csv": "anomaly_scores.json",
    "residuals.csv": "residuals.json",
    "sibling_correlations.csv": "sibling_correlations.json",
    "trait_cooccurrence.csv": "trait_cooccurrence.json",
    "r_sweep.csv": "r_sweep.json",
    "distribution_tests.csv": "distribution_tests.json",
    "mixture_weights.csv": "mixture_weights.json",
    "fitted_genes_claim.csv": "fitted_genes.json",
}


def _find_artifact(name: str) -> Path | None:
    """Find an artifact file in the results directories."""
    for d in RESULTS_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def _csv_to_json(csv_path: Path, json_path: Path) -> None:
    """Convert a CSV file to a JSON array of records."""
    df = pd.read_csv(csv_path)
    # Replace NaN/inf with None for JSON compatibility
    df = df.where(df.notna(), other=None)
    # Handle trait_cooccurrence which has an unnamed index column
    if "Unnamed: 0" in df.columns:
        df = df.set_index("Unnamed: 0")
        df.index.name = "trait"
        # Export as nested dict for cooccurrence
        json_path.write_text(
            json.dumps(df.to_dict(), indent=None),
            encoding="utf-8",
        )
        return
    records = df.to_dict(orient="records")
    json_path.write_text(
        json.dumps(records, indent=None),
        encoding="utf-8",
    )


def _export_children(output_dir: Path) -> int:
    """Export children.csv as JSON. Returns count."""
    # Try results/current first, then data/
    src = _find_artifact("children.csv")
    if src is None:
        src = CHILDREN_SRC
    if not src.exists():
        print(f"  SKIP children.csv (not found)")
        return 0
    df = pd.read_csv(src)
    out = output_dir / "children.json"
    records = df.to_dict(orient="records")
    out.write_text(json.dumps(records, allow_nan=False, indent=None), encoding="utf-8")
    print(f"  children.csv -> children.json ({len(records)} records)")
    return len(records)


def _compute_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    print("Exporting analysis artifacts for web dashboard...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Export CSV artifacts
    exported = 0
    for csv_name, json_name in CSV_ARTIFACTS.items():
        src = _find_artifact(csv_name)
        if src is None:
            print(f"  SKIP {csv_name} (not found)")
            continue
        dst = OUTPUT_DIR / json_name
        _csv_to_json(src, dst)
        df = pd.read_csv(src)
        print(f"  {csv_name} -> {json_name} ({len(df)} records)")
        exported += 1

    # Export children
    n_children = _export_children(OUTPUT_DIR)

    # Copy methodology markdown
    if METHODOLOGY_SRC.exists():
        dst = OUTPUT_DIR / "methodology.md"
        shutil.copy2(METHODOLOGY_SRC, dst)
        print(f"  research_methodology.md -> methodology.md")
    else:
        print(f"  SKIP methodology.md (not found)")

    # Write run metadata
    data_hash = ""
    if CHILDREN_SRC.exists():
        data_hash = _compute_hash(CHILDREN_SRC)

    meta = {
        "run_id": "web-export",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_data_hash": data_hash,
        "n_children": n_children,
        "n_litters": 14,
    }
    meta_path = OUTPUT_DIR / "run_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  run_meta.json written")

    print(f"\nDone: {exported} artifacts exported to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
