"""Legacy entry point — delegates to citrus_genetics.core.model.

All functionality has been moved to python/citrus_genetics/core/model.py.
Import from that package directly, or run via the package CLI:
    python -m citrus_genetics.cli.run_compare
"""

import sys
import warnings
from pathlib import Path

warnings.warn(
    "model.py is a legacy wrapper. Import from citrus_genetics.core.model instead.",
    DeprecationWarning,
    stacklevel=1,
)

sys.path.insert(0, str(Path(__file__).parent / "python"))

from citrus_genetics.core.model import (  # noqa: F401, E402
    FLOOR,
    TRAITS,
    V,
    LitterFit,
    candidates,
    display,
    fit_all,
    kernel,
    simulate,
    trait_rows,
)
from citrus_genetics.core.constants import CLAIM  # noqa: F401, E402
