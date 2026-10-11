"""Legacy entry point — delegates to citrus_genetics.pipelines.sim_checks.

All functionality has been moved to python/citrus_genetics/pipelines/sim_checks.py.
Run via the package CLI:
    python -m citrus_genetics.cli.run_simchecks
    python -m citrus_genetics.cli.run_all
"""

import sys
import warnings
from pathlib import Path

warnings.warn(
    "sim_checks.py is a legacy wrapper. Use 'python -m citrus_genetics.cli.run_simchecks' instead.",
    DeprecationWarning,
    stacklevel=1,
)

sys.path.insert(0, str(Path(__file__).parent / "python"))

from citrus_genetics.pipelines.sim_checks import fake_dataset, ppc, recovery_job  # noqa: F401, E402

if __name__ == "__main__":
    from citrus_genetics.cli.run_simchecks import main
    main()
