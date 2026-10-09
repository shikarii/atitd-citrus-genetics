"""Export the 'Data' tab of IndoHives 2026 Data.xlsx to one flat table (one row per child).

Output: data/children.csv (and data/children.parquet if pyarrow is installed).
Columns: litter, child, A_color..A_length, B_color..B_length, color, sweet, size, length.
Nothing is cleaned or dropped: every logged child is written as-is.
"""
from pathlib import Path
import openpyxl
import pandas as pd

HERE = Path(__file__).parent
SRC = HERE.parent / "IndoHives 2026 Data.xlsx"
TRAITS = ["color", "sweet", "size", "length"]


def read_litters(path=SRC):
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["Data"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    out = []
    for i, r in enumerate(rows):
        if len(r) > 1 and r[1] == "Color" and isinstance(r[2], (int, float)):
            block = rows[i:i + 4]
            assert [b[1] for b in block] == ["Color", "Sweet", "Size", "Length"], i
            name = str(r[0]).replace(" ", "")
            A = [int(b[2]) for b in block]
            B = [int(b[3]) for b in block]
            n = 0
            for col in range(5, max(len(b) for b in block)):
                vals = [b[col] if col < len(b) else None for b in block]
                if all(v is None for v in vals):
                    continue
                assert all(isinstance(v, (int, float)) for v in vals), (name, col, vals)
                n += 1
                out.append({"litter": name, "child": n,
                            **{f"A_{t}": a for t, a in zip(TRAITS, A)},
                            **{f"B_{t}": b for t, b in zip(TRAITS, B)},
                            **{t: int(v) for t, v in zip(TRAITS, vals)}})
    return pd.DataFrame(out)


if __name__ == "__main__":
    df = read_litters()
    (HERE / "data").mkdir(exist_ok=True)
    df.to_csv(HERE / "data" / "children.csv", index=False)
    try:
        df.to_parquet(HERE / "data" / "children.parquet", index=False)
    except ImportError:
        print("pyarrow not installed: parquet skipped")
    print(df.groupby("litter", sort=False).size().to_string())
    print("total children:", len(df))
