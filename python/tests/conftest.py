"""Shared test fixtures for citrus genetics tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from citrus_genetics.core.constants import CLAIM, TRAITS


@pytest.fixture
def claim_model() -> dict:
    """The CLAIM model spec."""
    return dict(CLAIM)


@pytest.fixture
def single_litter_df() -> pd.DataFrame:
    """A frozen 10-child single-litter fixture for fast tests.

    Uses Hive1 parent traits with synthetic child values
    designed to exercise all display rules.
    """
    a_traits = {"A_color": 587, "A_sweet": 197, "A_size": 599, "A_length": 752}
    b_traits = {"B_color": 368, "B_sweet": 308, "B_size": 731, "B_length": 552}
    children = [
        {"color": 650, "sweet": 197, "size": 492, "length": 584},
        {"color": 650, "sweet": 197, "size": 599, "length": 729},
        {"color": 368, "sweet": 197, "size": 654, "length": 552},
        {"color": 304, "sweet": 308, "size": 737, "length": 552},
        {"color": 650, "sweet": 216, "size": 731, "length": 752},
        {"color": 368, "sweet": 197, "size": 599, "length": 552},
        {"color": 368, "sweet": 308, "size": 657, "length": 752},
        {"color": 304, "sweet": 231, "size": 731, "length": 752},
        {"color": 587, "sweet": 197, "size": 652, "length": 752},
        {"color": 622, "sweet": 197, "size": 599, "length": 552},
    ]
    rows = []
    for i, child in enumerate(children, 1):
        rows.append(
            {
                "litter": "Hive1",
                "child": i,
                **a_traits,
                **b_traits,
                **child,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def full_dataset_df() -> pd.DataFrame:
    """Load the full 692-child dataset. Skip if file not found."""
    path = Path("data/children.csv")
    if not path.exists():
        pytest.skip("data/children.csv not found")
    return pd.read_csv(path)


@pytest.fixture
def trait_names() -> list[str]:
    """The four trait names."""
    return list(TRAITS)
