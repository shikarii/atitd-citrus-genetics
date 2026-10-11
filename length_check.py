"""Legacy entry point — delegates to citrus_genetics.pipelines.length_check.

All functionality has been moved to python/citrus_genetics/pipelines/length_check.py.
Run via:
    python -m citrus_genetics.cli.run_all
"""

import sys
import warnings
from pathlib import Path

warnings.warn(
    "length_check.py is a legacy wrapper. Use the package pipelines directly.",
    DeprecationWarning,
    stacklevel=1,
)

sys.path.insert(0, str(Path(__file__).parent / "python"))

if __name__ == "__main__":
    from pathlib import Path as _Path
    import pandas as _pd
    from citrus_genetics.pipelines.length_check import run_length_check as _run
    _df = _pd.read_csv(_Path("data/children.csv"))
    result = _run(_df)
    print(result)
