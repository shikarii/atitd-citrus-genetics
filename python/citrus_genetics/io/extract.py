"""Excel -> CSV ingestion for citrus breeding data.

Reads the 'Data' tab from the source Excel workbook and produces
a flat table with one row per child.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import openpyxl
import pandas as pd

from citrus_genetics.core.constants import LITTER_NAMES, TRAITS


def read_litters(path: Path) -> pd.DataFrame:
    """Read litter data from an Excel workbook.

    Args:
        path: Path to the Excel file.

    Returns:
        DataFrame with columns: litter, child, A_color..A_length,
        B_color..B_length, color, sweet, size, length.

    Raises:
        AssertionError: If data format is unexpected or litter count is wrong.
    """
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["Data"]
    rows: list[list[Any]] = [list(r) for r in ws.iter_rows(values_only=True)]
    out: list[dict[str, Any]] = []
    for i, r in enumerate(rows):
        if len(r) > 1 and r[1] == "Color" and isinstance(r[2], (int, float)):
            block = rows[i : i + 4]
            trait_labels = [b[1] for b in block]
            expected = ["Color", "Sweet", "Size", "Length"]
            if trait_labels != expected:
                msg = f"Unexpected trait labels at row {i}: {trait_labels}"
                raise ValueError(msg)
            name = str(r[0]).replace(" ", "")
            parent_a = [int(b[2]) for b in block]
            parent_b = [int(b[3]) for b in block]
            n = 0
            for col in range(5, max(len(b) for b in block)):
                vals = [b[col] if col < len(b) else None for b in block]
                if all(v is None for v in vals):
                    continue
                if not all(isinstance(v, (int, float)) for v in vals):
                    msg = f"Non-numeric values in litter {name}, column {col}: {vals}"
                    raise ValueError(msg)
                n += 1
                out.append(
                    {
                        "litter": name,
                        "child": n,
                        **{f"A_{t}": a for t, a in zip(TRAITS, parent_a, strict=True)},
                        **{f"B_{t}": b for t, b in zip(TRAITS, parent_b, strict=True)},
                        **{t: int(v) for t, v in zip(TRAITS, vals, strict=True)},  # type: ignore[arg-type]
                    }
                )
    df = pd.DataFrame(out)
    actual_litters = sorted(df["litter"].unique())
    expected_litters = sorted(LITTER_NAMES)
    if actual_litters != expected_litters:
        msg = (
            f"Expected {len(expected_litters)} litters {expected_litters}, "
            f"got {len(actual_litters)} litters {actual_litters}"
        )
        raise ValueError(msg)
    return df
