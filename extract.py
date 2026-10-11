"""Legacy entry point — delegates to citrus_genetics.io.extract.

All functionality has been moved to python/citrus_genetics/io/extract.py.
Run via:
    python -m citrus_genetics.io.extract <path_to_xlsx>
"""

import sys
import warnings
from pathlib import Path

warnings.warn(
    "extract.py is a legacy wrapper. Use citrus_genetics.io.extract directly.",
    DeprecationWarning,
    stacklevel=1,
)

sys.path.insert(0, str(Path(__file__).parent / "python"))

if __name__ == "__main__":
    src = Path(__file__).parent.parent / "IndoHives 2026 Data.xlsx"
    from citrus_genetics.io.extract import read_litters as _read
    import pandas as _pd
    df = _read(src)
    out_csv = Path(__file__).parent / "data" / "children.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {len(df)} rows to {out_csv}")
    try:
        out_parquet = out_csv.with_suffix(".parquet")
        df.to_parquet(out_parquet, index=False)
        print(f"Wrote {out_parquet}")
    except Exception:
        pass
