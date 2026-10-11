"""Benchmark native C++ acceleration vs pure Python.

Compares trait_rows, loglik, and single-litter fit times
between native and Python implementations.

Usage:
    uv run python -m citrus_genetics.scripts.bench_native
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from citrus_genetics.core._native import is_cuda_available, is_native_available
from citrus_genetics.core.constants import CLAIM
from citrus_genetics.core.model import LitterFit, kernel, trait_rows


def _bench_trait_rows(n_iters: int = 1000) -> None:
    """Benchmark trait_rows."""
    kern = kernel("uniform", 150)
    a = (400, 600)
    b = (350, 550)

    # Warmup
    for _ in range(10):
        trait_rows("mean", a, b, kern, "halfup")

    start = time.perf_counter()
    for _ in range(n_iters):
        trait_rows("mean", a, b, kern, "halfup")
    elapsed = time.perf_counter() - start

    print(f"  trait_rows x{n_iters}: {elapsed:.3f}s ({elapsed / n_iters * 1000:.2f} ms/call)")


def _bench_fit(df: pd.DataFrame, n_iters: int = 3) -> None:
    """Benchmark single-litter fit."""
    litter_df = df[df["litter"] == df["litter"].iloc[0]]

    # Warmup
    f = LitterFit(litter_df, CLAIM)
    f.fit()

    times = []
    for _ in range(n_iters):
        f = LitterFit(litter_df, CLAIM)
        start = time.perf_counter()
        f.fit()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    mean_t = np.mean(times)
    print(f"  Single litter fit x{n_iters}: {mean_t:.3f}s avg ({np.min(times):.3f}s min)")


def main() -> None:
    """Run benchmarks."""
    print("Native Acceleration Benchmark")
    print("=" * 50)
    print(f"  Native available: {is_native_available()}")
    print(f"  CUDA available:   {is_cuda_available()}")
    print()

    data_path = Path("data/children.csv")
    if not data_path.exists():
        print("ERROR: data/children.csv not found")
        return
    df = pd.read_csv(data_path)
    print(f"  Dataset: {len(df)} children, {df['litter'].nunique()} litters")
    print()

    print("trait_rows benchmark:")
    _bench_trait_rows()
    print()

    print("Single litter fit benchmark:")
    _bench_fit(df)
    print()

    print("Full 14-litter fit benchmark:")
    start = time.perf_counter()
    for _, litter_df in df.groupby("litter", sort=False):
        f = LitterFit(litter_df, CLAIM)
        f.fit()
    elapsed = time.perf_counter() - start
    print(f"  All 14 litters: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
