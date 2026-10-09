"""Run manifest generation and validation.

Handles SHA-256 hashing of artifacts, manifest creation, and
startup validation for the API server.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003
from typing import Any

import numpy as np
import pandas as pd
import scipy  # type: ignore[import-untyped]

from citrus_genetics.core.constants import ROOT_BOOTSTRAP_SEED, ROOT_OPTIMIZER_SEED


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        path: File path.

    Returns:
        Hex digest string.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_commit() -> str:
    """Get the current git commit hash.

    Returns:
        Short commit hash, or 'unknown' if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def is_worktree_dirty() -> bool:
    """Check if the git worktree has uncommitted changes.

    Returns:
        True if dirty, False if clean or not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_manifest(
    run_id: str,
    run_dir: Path,
    artifact_names: list[str],
) -> dict[str, Any]:
    """Build a run manifest with hashes and metadata.

    Args:
        run_id: UUID v4 run identifier.
        run_dir: Path to the run directory.
        artifact_names: List of artifact filenames to hash.

    Returns:
        Manifest dict ready to be serialized to JSON.
    """
    artifacts = {name: sha256_file(run_dir / name) for name in artifact_names}
    source_hash = artifacts.get("children.csv", "")
    return {
        "run_id": run_id,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "source_data_hash": source_hash,
        "code_commit": get_git_commit(),
        "code_dirty": is_worktree_dirty(),
        "model_manifest_hash": _manifest_hash(),
        "fold_assignment_hash": "",  # populated by caller after loading data
        "optimization_mode": "single-start",
        "seeds": {
            "ppc": 1,
            "root_optimizer_seed": ROOT_OPTIMIZER_SEED,
            "root_bootstrap_seed": ROOT_BOOTSTRAP_SEED,
        },
        "artifacts": artifacts,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scipy_version": scipy.__version__,
        "platform": f"{platform.system()}-{platform.machine()}",
    }


def _manifest_hash() -> str:
    """Hash the model manifest for provenance tracking."""
    from citrus_genetics.core.constants import MODEL_MANIFEST  # noqa: PLC0415

    serialized = json.dumps(
        [(m["model_id"], m["display_name"], sorted(m["spec"].items())) for m in MODEL_MANIFEST],
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def validate_run_dir(run_dir: Path) -> dict[str, Any]:
    """Validate a run directory's manifest against its artifacts.

    Args:
        run_dir: Path to a run directory.

    Returns:
        The loaded manifest dict.

    Raises:
        FileNotFoundError: If manifest or artifact is missing.
        ValueError: If hash mismatch detected.
    """
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        msg = f"Missing run_manifest.json in {run_dir}"
        raise FileNotFoundError(msg)
    manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts: dict[str, str] = manifest.get("artifacts", {})
    for name, expected_hash in artifacts.items():
        artifact_path = run_dir / name
        if not artifact_path.exists():
            msg = f"Missing artifact {name} in {run_dir}"
            raise FileNotFoundError(msg)
        actual_hash = sha256_file(artifact_path)
        if actual_hash != expected_hash:
            msg = f"Hash mismatch for {name}: expected {expected_hash}, got {actual_hash}"
            raise ValueError(msg)
    source_hash = manifest.get("source_data_hash", "")
    children_hash = artifacts.get("children.csv", "")
    if source_hash and children_hash and source_hash != children_hash:
        msg = (
            f"Manifest invariant violated: source_data_hash ({source_hash}) "
            f"!= artifacts['children.csv'] ({children_hash})"
        )
        raise ValueError(msg)
    return manifest
