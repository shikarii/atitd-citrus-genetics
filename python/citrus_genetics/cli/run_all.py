"""Authoritative orchestrator: run all pipelines and publish atomically.

This is the single entry point for producing a complete, validated
analytics run. It:
1. Allocates a UUID v4 run_id
2. Snapshots children.csv into the run directory
3. Runs all pipelines against the snapshot (including all analysis modules)
4. Writes artifacts and manifest
5. Publishes atomically via directory rename + symlink swap

Flags:
    --allow-dirty   Allow running with an uncommitted worktree (development)
    --fast          Skip slow profile-likelihood computation
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from pathlib import Path

import pandas as pd

from citrus_genetics.analysis.anomaly import run_claim_anomaly
from citrus_genetics.analysis.distribution_tests import run_distribution_tests
from citrus_genetics.analysis.mi_matrix import run_mi_matrix
from citrus_genetics.analysis.mixture import run_mixture
from citrus_genetics.analysis.profile import run_profile_likelihoods
from citrus_genetics.analysis.residuals import run_residuals
from citrus_genetics.analysis.r_sweep import run_r_sweep
from citrus_genetics.io.provenance import build_manifest, is_worktree_dirty, sha256_file
from citrus_genetics.io.results import (
    write_fitted_genes,
    write_model_comparison,
    write_ppc_distributions,
    write_ppc_summary,
)
from citrus_genetics.pipelines.compare import fit_claim_genes, run_comparison
from citrus_genetics.pipelines.sim_checks import ppc

BASE = Path()


def _guard_preconditions(*, allow_dirty: bool, data_path: Path) -> None:
    """Abort with a message if pre-run conditions are not met.

    Args:
        allow_dirty: If False, abort when the worktree is dirty.
        data_path: Path to children.csv that must exist before running.
    """
    if not allow_dirty and is_worktree_dirty():
        print("ERROR: Working tree is dirty. Use --allow-dirty for development runs.", file=sys.stderr)
        sys.exit(1)
    if not data_path.exists():
        print(f"ERROR: {data_path} not found", file=sys.stderr)
        sys.exit(1)


def _snapshot_and_load(data_path: Path, tmp_dir: Path) -> pd.DataFrame:
    """Copy children.csv into tmp_dir, fsync it, and load it.

    Args:
        data_path: Source children.csv path.
        tmp_dir: Staging run directory.

    Returns:
        The children DataFrame loaded from the snapshot.
    """
    snapshot_path = tmp_dir / "children.csv"
    shutil.copy2(data_path, snapshot_path)
    _fsync_file(snapshot_path)
    source_hash = sha256_file(snapshot_path)
    print(f"Snapshot children.csv (SHA-256: {source_hash[:16]}...)")
    df = pd.read_csv(snapshot_path)
    print(f"Loaded {len(df)} children from snapshot")
    return df


def _run_pipelines(df: pd.DataFrame, tmp_dir: Path, *, fast: bool = False) -> list[str]:
    """Execute all analytics pipelines and write their output artifacts.

    Args:
        df: Children DataFrame loaded from the snapshot.
        tmp_dir: Staging run directory to write artifacts into.
        fast: If True, skip slow profile-likelihood computation.

    Returns:
        List of artifact filenames written.
    """
    artifacts: list[str] = []

    # --- Core pipelines ---
    print("Running 30-model comparison...")
    comparison = run_comparison(df)
    write_model_comparison(comparison, tmp_dir / "model_comparison.csv")
    artifacts.append("model_comparison.csv")
    print("Model comparison complete")

    print("Fitting CLAIM genes...")
    genes = fit_claim_genes(df)
    write_fitted_genes(genes, tmp_dir / "fitted_genes_claim.csv")
    artifacts.append("fitted_genes_claim.csv")

    print("Running plug-in predictive check (300 simulations)...")
    obs_k, obs_tr, sim_k, sim_tr = ppc(df, n_sims=300, seed=1)
    write_ppc_summary(obs_k, obs_tr, sim_k, sim_tr, 300, tmp_dir / "ppc_summary.json")
    write_ppc_distributions(obs_k, obs_tr, sim_k, sim_tr, tmp_dir / "ppc_distributions.parquet")
    artifacts.extend(["ppc_summary.json", "ppc_distributions.parquet"])
    print("PPC complete")

    # --- Analysis pipelines (Tier 1-2 from methodology spec) ---
    print("Computing per-child anomaly scores under CLAIM...")
    anomaly_df = run_claim_anomaly(df)
    anomaly_df.to_csv(tmp_dir / "anomaly_scores.csv", index=False)
    artifacts.append("anomaly_scores.csv")
    print(f"  Worst child log-lik: {anomaly_df['log_lik'].iloc[0]:.2f}")

    print("Computing mutual information matrix...")
    mi_df = run_mi_matrix(df)
    mi_df.to_csv(tmp_dir / "mi_matrix.csv", index=False)
    artifacts.append("mi_matrix.csv")
    # Log top off-diagonal entries
    off_diag = mi_df[~mi_df["is_diagonal"]].nlargest(3, "mi_excess")
    for _, row in off_diag.iterrows():
        print(f"  Off-diagonal MI: {row['parent_var']} -> {row['child_var']}: {row['mi_excess']:.4f}")

    print("Computing residuals and sibling correlations...")
    residuals_df, sib_corr_df, cooccurrence_df = run_residuals(df)
    residuals_df.to_csv(tmp_dir / "residuals.csv", index=False)
    sib_corr_df.to_csv(tmp_dir / "sibling_correlations.csv", index=False)
    cooccurrence_df.to_csv(tmp_dir / "trait_cooccurrence.csv")
    artifacts.extend(["residuals.csv", "sibling_correlations.csv", "trait_cooccurrence.csv"])
    print("  Residuals complete")

    print("Running R parameter sweep (R=50..300)...")
    sweep_df = run_r_sweep(df)
    sweep_df.to_csv(tmp_dir / "r_sweep.csv", index=False)
    artifacts.append("r_sweep.csv")
    best_r = sweep_df.loc[sweep_df["fit_ll"].idxmax(), "R"]
    print(f"  Best R by fit_ll: {best_r} (CLAIM uses R=150)")

    print("Running distribution tests (KS + AD, 56 litter×trait pairs)...")
    dist_df = run_distribution_tests(df)
    dist_df.to_csv(tmp_dir / "distribution_tests.csv", index=False)
    artifacts.append("distribution_tests.csv")
    n_sig = int(dist_df["ks_sig_fdr"].sum())
    print(f"  Significant after BH-FDR (alpha=0.05): {n_sig}/56")

    print("Fitting CLAIM+INDEP mixture models...")
    mixture_df = run_mixture(df)
    mixture_df.to_csv(tmp_dir / "mixture_weights.csv", index=False)
    artifacts.append("mixture_weights.csv")
    min_pi = mixture_df["pi_claim"].min()
    print(f"  Lowest CLAIM mixture weight: {min_pi:.3f} ({mixture_df.iloc[0]['litter']})")

    if not fast:
        print("Computing profile likelihoods (slow — use --fast to skip)...")
        profile_df = run_profile_likelihoods(df)
        profile_df.to_parquet(tmp_dir / "profile_likelihoods.parquet", index=False)
        artifacts.append("profile_likelihoods.parquet")
        print(f"  Profile curves computed: {len(profile_df)} points")
    else:
        print("Skipping profile likelihoods (--fast mode)")

    return artifacts


def _write_manifest(run_id: str, tmp_dir: Path, artifact_names: list[str]) -> None:
    """Build, validate, and write run_manifest.json into tmp_dir.

    Args:
        run_id: UUID string identifying this run.
        tmp_dir: Staging run directory containing all artifacts.
        artifact_names: List of artifact filenames to include in manifest.

    Raises:
        RuntimeError: If source_data_hash does not match the children.csv artifact hash.
    """
    manifest = build_manifest(run_id, tmp_dir, artifact_names)
    if manifest["source_data_hash"] != manifest["artifacts"]["children.csv"]:
        msg = "FATAL: source_data_hash != artifacts['children.csv']"
        raise RuntimeError(msg)
    manifest_path = tmp_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main(*, allow_dirty: bool = False, fast: bool = False) -> None:
    """Execute the full pipeline and publish atomically.

    Args:
        allow_dirty: If False, refuse to run with a dirty worktree.
        fast: If True, skip slow profile-likelihood computation.
    """
    data_path = BASE / "data" / "children.csv"
    _guard_preconditions(allow_dirty=allow_dirty, data_path=data_path)

    run_id = str(uuid.uuid4())
    runs_dir = BASE / "results" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = runs_dir / f".tmp-{run_id}"
    tmp_dir.mkdir()
    print(f"Run {run_id}: staging in {tmp_dir.name}")

    df = _snapshot_and_load(data_path, tmp_dir)
    artifacts = _run_pipelines(df, tmp_dir, fast=fast)
    all_artifacts = ["children.csv", *artifacts]
    _write_manifest(run_id, tmp_dir, all_artifacts)

    _fsync_dir(tmp_dir)

    final_dir = runs_dir / run_id
    tmp_dir.rename(final_dir)
    print(f"Published run directory: {final_dir}")

    _swap_current_symlink(final_dir)
    print(f"Updated results/current -> {run_id}")
    print("Done.")


def _swap_current_symlink(final_dir: Path) -> None:
    """Atomically replace results/current symlink to point at final_dir."""
    current = BASE / "results" / "current"
    current_new = BASE / "results" / "current.new"
    if current_new.exists() or current_new.is_symlink():
        current_new.unlink()
    current_new.symlink_to(final_dir.resolve())
    current_new.replace(current)


def _fsync_file(path: Path) -> None:
    """Fsync a file to ensure durability."""
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    """Fsync a directory to ensure durability."""
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass  # Windows doesn't support fsync on directories


if __name__ == "__main__":
    allow = "--allow-dirty" in sys.argv
    fast_mode = "--fast" in sys.argv
    main(allow_dirty=allow, fast=fast_mode)
