"""Legacy entry point — delegates to citrus_genetics.pipelines.compare.

All functionality has been moved to python/citrus_genetics/pipelines/compare.py.
Run via the package CLI:
    python -m citrus_genetics.cli.run_compare
    python -m citrus_genetics.cli.run_all
"""

import sys
import warnings
from pathlib import Path

warnings.warn(
    "compare.py is a legacy wrapper. Use 'python -m citrus_genetics.cli.run_compare' instead.",
    DeprecationWarning,
    stacklevel=1,
)

sys.path.insert(0, str(Path(__file__).parent / "python"))

from citrus_genetics.core.constants import CLAIM, TRAITS, get_variants  # noqa: F401, E402

if __name__ == "__main__":
    from citrus_genetics.cli.run_compare import main
    main()
