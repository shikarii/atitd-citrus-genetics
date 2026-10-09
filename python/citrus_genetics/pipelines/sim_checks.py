"""Ground-truth validation with synthetic data (pure compute, no IO).

1. Model recovery: build fake datasets from fitted models, fit all three
   competing models, verify the true generator wins.
2. Hidden-gene recovery: on fake CLAIM datasets, check how often the fit
   recovers the planted hidden Sweet/Size genes exactly.
3. Plug-in predictive check: simulate from the fitted CLAIM model and
   compare summary statistics with real data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from numpy.typing import NDArray

from citrus_genetics.core.constants import CLAIM, TRAITS
from citrus_genetics.core.model import LitterFit, kernel, simulate, trait_rows

ModelSpec = dict[str, Any]

DEFAULT_MODELS: dict[str, ModelSpec] = {
    "CLAIM": CLAIM,
    "INDEP": {**CLAIM, "mut": "indep", "p": 0.11},
    "TRI150": {**CLAIM, "shape": "triangular"},
}


def fake_dataset(
    df: pd.DataFrame,
    gen_name: str,
    seed: int,
    models: dict[str, ModelSpec] | None = None,
) -> tuple[pd.DataFrame, dict[str, dict[tuple[str, int], tuple[int, int]]]]:
    """Generate a synthetic dataset from a fitted model.

    Args:
        df: Real dataset DataFrame.
        gen_name: Name of the generating model.
        seed: Random seed.
        models: Model specs dict (defaults to DEFAULT_MODELS).

    Returns:
        Tuple of (synthetic DataFrame, truth dict of genes per litter).
    """
    models = models or DEFAULT_MODELS
    rng = np.random.default_rng(seed)
    parts: list[pd.DataFrame] = []
    truth: dict[str, dict[tuple[str, int], tuple[int, int]]] = {}
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, models[gen_name])
        f.fit()
        y = simulate(f, len(d), rng)
        dd = d.copy()
        dd[TRAITS] = y
        parts.append(dd)
        truth[str(lit)] = dict(f.genes)
    return pd.concat(parts), truth


def recovery_job(
    df: pd.DataFrame,
    gen_name: str,
    seed: int,
    models: dict[str, ModelSpec] | None = None,
) -> dict[str, Any]:
    """Run model recovery for a single (generator, seed) pair.

    Args:
        df: Real dataset DataFrame.
        gen_name: Name of the generating model.
        seed: Random seed.
        models: Model specs dict.

    Returns:
        Dict with generator, seed, fit/cv scores, and gene recovery stats.
    """
    models = models or DEFAULT_MODELS
    fake, truth = fake_dataset(df, gen_name, seed, models)
    ll: dict[str, float] = {}
    cv: dict[str, float] = {}
    hits = 0
    tot = 0
    for name, m in models.items():
        s_val = 0.0
        c_val = 0.0
        for lit, d in fake.groupby("litter", sort=False):
            f = LitterFit(d, m)
            s_val += f.fit()
            for tr, te in ((d.iloc[0::2], d.iloc[1::2]), (d.iloc[1::2], d.iloc[0::2])):
                g = LitterFit(tr, m)
                g.fit()
                c_val += g.score_other(te)[0]
            if name == gen_name == "CLAIM":
                for t in (1, 2):
                    for parent in ("A", "B"):
                        tot += 1
                        hits += int(sorted(f.genes[(parent, t)]) == sorted(truth[str(lit)][(parent, t)]))
        ll[name] = round(s_val, 1)
        cv[name] = round(c_val, 1)
    return {
        "generator": gen_name,
        "seed": seed,
        "fit_ll": ll,
        "cv_ll": cv,
        "gene_hits": hits,
        "gene_total": tot,
    }


def _support(f: LitterFit, t: int) -> set[int]:
    """Get the set of possible trait values without nudging."""
    r = trait_rows(
        f.m["rules"][t],
        f.genes[("A", t)],
        f.genes[("B", t)],
        kernel("uniform", 150),
        f.m["rround"],
    )
    return set(np.flatnonzero(r["none"] > 0).tolist())


def _changed(f: LitterFit, y: NDArray[np.intp]) -> NDArray[np.bool_]:
    """Per child and trait: True if the shown value requires a nudge."""
    sup = [_support(f, t) for t in range(4)]
    return np.array([[y[i, t] not in sup[t] for t in range(4)] for i in range(len(y))])


def ppc(
    df: pd.DataFrame,
    n_sims: int = 300,
    seed: int = 1,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Run plug-in predictive check.

    Args:
        df: Full dataset DataFrame.
        n_sims: Number of simulations.
        seed: Random seed.

    Returns:
        Tuple of (obs_k, obs_tr, sim_k, sim_tr) arrays.
        obs_k: shape (3,) counts of children with 0/1/2+ changed traits.
        obs_tr: shape (4,) per-trait count of visible changes.
        sim_k: shape (n_sims, 3) simulated change-count distributions.
        sim_tr: shape (n_sims, 4) simulated per-trait distributions.
    """
    rng = np.random.default_rng(seed)
    obs_k = np.zeros(3, dtype=np.float64)
    obs_tr = np.zeros(4, dtype=np.float64)
    sim_k = np.zeros((n_sims, 3), dtype=np.float64)
    sim_tr = np.zeros((n_sims, 4), dtype=np.float64)
    for _lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, CLAIM)
        f.fit()
        ch = _changed(f, d[TRAITS].to_numpy())
        k = np.minimum(ch.sum(1), 2)
        obs_k += np.bincount(k, minlength=3)
        obs_tr += ch.sum(0)
        for s in range(n_sims):
            cs = _changed(f, simulate(f, len(d), rng))
            sim_k[s] += np.bincount(np.minimum(cs.sum(1), 2), minlength=3)
            sim_tr[s] += cs.sum(0)
    return obs_k, obs_tr, sim_k, sim_tr
