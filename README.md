# Citrus Genetics

Statistical model validation and breeding analytics for *A Tale in the Desert* citrus tree genetics.

Tests whether the proposed 8-gene inheritance model explains all 692 logged children from 14 litters,
comparing the claimed mechanism against 30 rival models via maximum likelihood estimation.

**Live dashboard:** [shikarii.github.io/atitd-citrus-genetics](https://shikarii.github.io/atitd-citrus-genetics)

## Research Design

### The Claimed Model

Every citrus tree has 8 hidden genes (2 per trait), integers 0--1000. Observable traits are derived
from gene pairs by deterministic display rules:

| Trait  | Display Rule         | Identifiability |
|--------|----------------------|-----------------|
| Color  | mean(g1, g2) half-up | Sum only        |
| Sweet  | min(g1, g2)          | Full            |
| Size   | max(g1, g2)          | Full            |
| Length | g1 only              | Lower bound     |

**Inheritance:** each of a child's 8 genes is copied from one parent (fair coin flip, slot-preserving).
Then exactly one of the 8 genes receives a uniform integer nudge in [-150, +150], clamped to [0, 1000].

### Validation Approach

1. **In-sample fit (log-likelihood):** fit hidden genes per litter by coordinate-ascent MLE; rank all 30
   model variants by total log-likelihood
2. **Synthetic ground-truth:** generate 9 fake datasets from 3 known models, confirm the fitter recovers
   the true model 9/9 times
3. **Posterior-predictive checks:** simulate 300 datasets from the fitted model, compare summary statistics
   against real data
4. **Pedigree consistency:** parents appearing in multiple litters yield consistent hidden-gene estimates
5. **Sensitivity analyses:** nudge-range sweep, mutual information, residual diagnostics, distribution
   tests, mixture-model exploration, anomaly scoring

### Key Results

The claimed model explains all 692 children with log-likelihood -5462.5. Selected comparisons:

| Rival                          | LL       | Gap   |
|--------------------------------|----------|-------|
| Independent per-gene nudges    | -5609.8  | -147  |
| Triangular nudge +/-150        | -5548.1  | -86   |
| Uniform +/-200                 | -5528.0  | -65   |
| Sweet = max (swapped rule)     | -5531.5  | -69   |
| One gene per trait (no hidden) | -10487.0 | -5024 |

Full results and interactive charts on the [live dashboard](https://shikarii.github.io/atitd-citrus-genetics).

## Architecture

```
atitd-citrus-genetics/
  python/citrus_genetics/        Python package (core engine + API + dashboard)
  native/                        C++20/AVX2 acceleration (pybind11)
  web/                           React/TypeScript frontend
  data/                          Dataset (692 children, 14 litters)
  results/                       Pipeline outputs
  docs/                          Research methodology & systems engineering spec
```

### Compute Layer

```
model.py  --->  _native.py  --->  _citrus_native.{pyd,so}
   |                ^                      ^
   |          try/except fallback     C++20 / AVX2 / CUDA
   v
analysis/     7 pluggable modules (MI, anomaly, residuals, r-sweep, etc.)
pipelines/    30-model comparison, synthetic validation, sim checks
cli/          run_all, run_compare, run_simchecks, export_web_data
```

The statistical engine in `core/model.py` computes exact per-child likelihoods given parents' hidden
genes. Hidden genes are recovered by coordinate-ascent MLE (coarse grid scan + fine refinement),
separately per litter. The native C++ layer accelerates the hot path (`trait_rows`, `child_lik`,
`loglik`, `scan_parent`) via AVX2 intrinsics with transparent fallback to pure NumPy.

### Analysis Modules

| Module              | Output                                              |
|---------------------|-----------------------------------------------------|
| `mi_matrix`         | Mutual information heatmap (parent -> child traits)  |
| `anomaly`           | Per-child anomaly scores (high-residual outliers)    |
| `residuals`         | Residual distributions, sibling correlations         |
| `r_sweep`           | Nudge-range sensitivity (R = 100..200)               |
| `distribution_tests`| KS and Anderson-Darling goodness-of-fit per litter   |
| `mixture`           | CLAIM + INDEP mixture-weight exploration             |
| `profile`           | Profile likelihood for parameter sensitivity         |

### API and Frontend

- **FastAPI** backend serves fitted results, model comparisons, and per-litter details
- **React + TypeScript** dashboard with Plotly charts (9 pages: models, MI matrix, anomalies,
  residuals, R-sweep, distribution tests, mixture, gene landscape)
- **Streamlit** exploratory UI for interactive analysis

### Native Acceleration

C++20 with AVX2 intrinsics targeting Skylake (i7-6700K). Optional CUDA stubs for future GPU support.
Builds via CMake + pybind11; the extension is optional -- pure Python works without it.

```
native/
  src/          model.cpp, avx2.cpp, dispatch.cpp, bindings.cpp
  include/      model.h, avx2.h, dispatch.h, kernels.h
  cuda/         trait_rows.cu, scan_parent.cu, loglik.cu (stubs)
  CMakeLists.txt
```

## Quick Start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
make sync

# Run the full pipeline (30-model comparison + validation)
make run-all

# Or skip profile likelihoods for faster iteration
make run-all-fast

# Launch the Streamlit dashboard
make dashboard

# Build and serve the web dashboard
make build-web
```

### Native Extension (optional)

Requires CMake 3.18+, a C++20 compiler, and pybind11.

```bash
make build-native       # Compile and install .pyd/.so
make bench-native       # Run performance benchmark
make clean-native       # Remove build artifacts
```

### Quality Gates

```bash
make quality            # format-check + lint + test (all must pass)
make lint               # ruff + mypy (strict) + import-linter + LOC check
make test               # pytest with 80% branch coverage gate
```

### Docker

```bash
make docker-build       # Build API + web containers
make docker-up          # Start services (API :8000, web :5173)
make docker-down        # Stop services
```

## Data

`data/children.csv` -- 692 children from 14 litters, both parents known for each:

```
litter, parent1_color, parent1_sweet, parent1_size, parent1_length,
        parent2_color, parent2_sweet, parent2_size, parent2_length,
        child_color,   child_sweet,   child_size,   child_length
```

## Documentation

- [Research Methodology](docs/research_methodology.md) -- statistical methods, model specification,
  validation procedures (v27, 26 adversarial review rounds)
- [Systems Engineering Spec](docs/systems_engineering.md) -- architecture, requirements (R-01 through
  R-11), V&V, risk register, native acceleration layer

## Technology Stack

| Layer         | Technology                             |
|---------------|----------------------------------------|
| Compute       | Python 3.12, NumPy, SciPy, Pandas     |
| Acceleration  | C++20, AVX2/FMA3, CUDA (optional)     |
| API           | FastAPI, Uvicorn, Pydantic             |
| Web           | React 18, TypeScript, Vite, TailwindCSS, Plotly |
| Exploratory   | Streamlit                              |
| Build         | uv, CMake, Make, npm                   |
| Quality       | Ruff, MyPy (strict), pytest, import-linter |
| Deploy        | Docker, GitHub Pages                   |

## Authors

**Shikari** (primary) and **Catote** (secondary), with data contributions from
[ATITD Wiki contributors](https://atitd.wiki/tale11/Guides/Indonesian_Beehives).

## Caveats

- **Held-out scoring** prefers the independent-nudge rival, but this is a known bias: strict models
  penalize children showing hidden genes unseen in the training fold. Confirmed on synthetic data where
  held-out scoring picks the wrong model even when the claimed model generated the data.
- **Length display rule** (g1 vs min/max) is non-identifiable by fit alone; the rival gains ~59 on real
  data and ~54--66 on synthetic data from the true g1 model.
- **Color gene split** is non-identifiable; only the sum of the two genes is observable.
- **Hive1b** shows ~34% cloning behavior (full parent copy + nudge); no other litter exhibits this.
- This is a fit to observed data. It does not prove this is the game's code.
