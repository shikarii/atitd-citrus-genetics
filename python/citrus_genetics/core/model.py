"""Exact likelihood model for ATITD citrus-tree inheritance.

A model is a dict:
  rules  : display rule per trait, each one of 'mean', 'min', 'max', 'g1'
  mut    : 'one8'  -> exactly one of the 8 genes is nudged in every child
           'one_g1'-> exactly one of the 4 gene-1 slots is nudged
           'indep' -> every gene is nudged independently with probability p
  p      : per-gene nudge probability (only for 'indep')
  shape  : 'uniform' or 'triangular' nudge distribution on the integers -R..R
  R      : maximum nudge size
  rround : 'halfup' or 'floor' rounding of the mean rule
  clone  : True -> allow a per-litter share c of children that are exact copies
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import pandas as pd
    from numpy.typing import NDArray

TRAITS: list[str] = ["color", "sweet", "size", "length"]
V: int = 1001  # gene / display values 0..1000
FLOOR: float = 1e-15  # likelihood floor
CONVERGENCE_THRESHOLD: float = 1e-6  # log-likelihood improvement below which fitting stops
PARENT_COIN: float = 0.5  # probability of inheriting from each parent


def kernel(shape: str, r: int) -> tuple[NDArray[np.intp], NDArray[np.float64]]:
    """Compute the nudge kernel for a given shape and radius.

    Args:
        shape: 'uniform' or 'triangular'.
        r: Maximum nudge magnitude.

    Returns:
        Tuple of (offsets, probabilities).
    """
    offs = np.arange(-r, r + 1)
    w: NDArray[np.float64] = (
        np.ones(len(offs), dtype=np.float64) if shape == "uniform" else (r + 1 - np.abs(offs)).astype(np.float64)
    )
    return offs, w / w.sum()


def display(rule: str, g1: Any, g2: Any, rround: str = "halfup") -> Any:
    """Compute the displayed trait value from two genes.

    Args:
        rule: Display rule ('mean', 'min', 'max', 'g1').
        g1: Gene 1 value(s).
        g2: Gene 2 value(s).
        rround: Rounding mode for mean rule.

    Returns:
        Displayed trait value(s).
    """
    if rule == "mean":
        s = g1 + g2
        return (s + 1) // 2 if rround == "halfup" else s // 2
    if rule == "min":
        return np.minimum(g1, g2)
    if rule == "max":
        return np.maximum(g1, g2)
    return g1 + 0 * g2  # 'g1'


def trait_rows(
    rule: str,
    a: tuple[int, int],
    b: tuple[int, int],
    kern: tuple[NDArray[np.intp], NDArray[np.float64]],
    rround: str,
    *,
    need_both: bool = False,
) -> dict[str, NDArray[np.float64]]:
    """Distribution of the child's shown value for one trait.

    Args:
        rule: Display rule for this trait.
        a: Parent A gene pair (g1, g2).
        b: Parent B gene pair (g1, g2).
        kern: Nudge kernel (offsets, probabilities).
        rround: Rounding mode.
        need_both: Whether to compute the 'both slots nudged' case.

    Returns:
        Dict with keys 'none', 's1', 's2' (and optionally 'both'),
        each an array of length V (1001).
    """
    offs, kp = kern
    pairs = [(a[0], a[1]), (b[0], b[1]), (a[0], b[1]), (b[0], a[1])]
    rows: dict[str, NDArray[np.float64]] = {k: np.zeros(V, dtype=np.float64) for k in ("none", "s1", "s2")}
    if need_both:
        rows["both"] = np.zeros(V, dtype=np.float64)
    for g1, g2 in pairs:
        rows["none"][display(rule, np.array(g1), np.array(g2), rround)] += 0.25
        n1 = np.clip(g1 + offs, 0, 1000)
        np.add.at(rows["s1"], display(rule, n1, np.full_like(n1, g2), rround), 0.25 * kp)
        n2 = np.clip(g2 + offs, 0, 1000)
        np.add.at(rows["s2"], display(rule, np.full_like(n2, g1), n2, rround), 0.25 * kp)
        if need_both:
            d = display(rule, n1[:, None], n2[None, :], rround)
            rows["both"] += 0.25 * np.bincount(d.ravel(), weights=np.outer(kp, kp).ravel(), minlength=V)
    return rows


def candidates(rule: str, v: int, rround: str = "halfup") -> list[NDArray[np.intp]]:
    """All (g1, g2) gene pairs a parent showing v can carry under a display rule.

    Args:
        rule: Display rule.
        v: Displayed trait value.
        rround: Rounding mode.

    Returns:
        List of arrays, each of shape (N, 2) with valid gene pairs.
    """
    if rule == "mean":
        sums = (2 * v - 1, 2 * v) if rround == "halfup" else (2 * v, 2 * v + 1)
        groups: list[NDArray[np.intp]] = []
        for s in sums:
            if 0 <= s <= 2000:  # noqa: PLR2004
                g1 = np.arange(max(0, s - 1000), min(1000, s) + 1)
                groups.append(np.stack([g1, s - g1], axis=1))
        return groups
    if rule == "min":
        h = np.arange(v, 1001)
    elif rule == "max":
        h = np.arange(0, v + 1)
    else:  # 'g1': gene 2 is never shown and never affects anything shown
        return [np.array([[v, 500]])]
    return [np.stack([np.full_like(h, v), h], axis=1), np.stack([h, np.full_like(h, v)], axis=1)]


ModelSpec = dict[str, Any]


class LitterFit:
    """Fit a model's hidden genes to a single litter by maximum likelihood.

    Attributes:
        m: Model specification dict.
        kern: Nudge kernel (offsets, probabilities).
        y: Child trait observations, shape (n_children, 4).
        A: Parent A observed traits, shape (4,).
        B: Parent B observed traits, shape (4,).
        genes: Fitted gene pairs, keyed by (parent, trait_index).
        c: Fitted clone fraction.
        cols: Per-trait precomputed column likelihoods.
    """

    def __init__(self, df: pd.DataFrame, model: ModelSpec) -> None:
        """Initialize fitter for a single litter.

        Args:
            df: DataFrame for one litter with parent and child traits.
            model: Model specification dict.
        """
        self.m = model
        self.kern = kernel(model["shape"], model["R"])
        self.y: NDArray[np.intp] = df[TRAITS].to_numpy()
        self.A: NDArray[np.intp] = df[[f"A_{t}" for t in TRAITS]].iloc[0].to_numpy()
        self.B: NDArray[np.intp] = df[[f"B_{t}" for t in TRAITS]].iloc[0].to_numpy()
        self.need_both: bool = model["mut"] == "indep"
        is_a = (self.y == self.A).all(1)
        is_b = (self.y == self.B).all(1)
        self.clone_lik: NDArray[np.float64] = 0.5 * is_a + 0.5 * is_b
        self.c: float = 0.0
        # Initialize genes
        self.genes: dict[tuple[str, int], tuple[int, int]] = {}
        for t, rule in enumerate(model["rules"]):
            for p_name, vals in (("A", self.A), ("B", self.B)):
                grp = candidates(rule, int(vals[t]), model["rround"])
                if rule == "mean":
                    g = grp[-1][len(grp[-1]) // 2]
                elif rule in ("min", "max"):
                    g = np.array([vals[t], vals[t]])
                else:
                    g = grp[0][0]
                self.genes[(p_name, t)] = (int(g[0]), int(g[1]))
        self.cols: list[dict[str, NDArray[np.float64]]] = [self._cols(t) for t in range(4)]

    def _cols(
        self,
        t: int,
        g_a: tuple[int, int] | None = None,
        g_b: tuple[int, int] | None = None,
    ) -> dict[str, NDArray[np.float64]]:
        g_a = g_a or self.genes[("A", t)]
        g_b = g_b or self.genes[("B", t)]
        r = trait_rows(self.m["rules"][t], g_a, g_b, self.kern, self.m["rround"], need_both=self.need_both)
        yt = self.y[:, t]
        out: dict[str, NDArray[np.float64]] = {"none": r["none"][yt], "s1": r["s1"][yt], "s2": r["s2"][yt]}
        if self.need_both:
            out["both"] = r["both"][yt]
        return out

    def child_lik(
        self,
        cols: list[dict[str, NDArray[np.float64]]] | None = None,
        c: float | None = None,
    ) -> NDArray[np.float64]:
        """Compute per-child likelihood under the current model.

        Args:
            cols: Optional precomputed column likelihoods.
            c: Optional clone fraction override.

        Returns:
            Array of per-child likelihoods, shape (n_children,).
        """
        cols = cols or self.cols
        c = self.c if c is None else c
        mut = self.m["mut"]
        if mut == "indep":
            p = self.m["p"]
            big_l = np.ones(len(self.y), dtype=np.float64)
            for k in cols:
                big_l *= (1 - p) ** 2 * k["none"] + p * (1 - p) * (k["s1"] + k["s2"]) + p * p * k["both"]
        else:
            none = np.stack([k["none"] for k in cols])
            if mut == "one8":
                hit = np.stack([k["s1"] + k["s2"] for k in cols]) / 8
            else:  # one_g1
                hit = np.stack([k["s1"] for k in cols]) / 4
            big_l = np.zeros(len(self.y), dtype=np.float64)
            for t in range(4):
                big_l += hit[t] * np.prod(np.delete(none, t, 0), 0)
        if self.m["clone"] == "nudged":
            big_l = (1 - c) * big_l + c * 0.5 * (self._self_lik("A") + self._self_lik("B"))
        elif self.m["clone"]:
            big_l = (1 - c) * big_l + c * self.clone_lik
        return big_l

    def _self_lik(self, parent: str) -> NDArray[np.float64]:
        none_arr: list[NDArray[np.float64]] = []
        hit_arr: list[NDArray[np.float64]] = []
        for t in range(4):
            g = self.genes[(parent, t)]
            r = trait_rows(self.m["rules"][t], g, g, self.kern, self.m["rround"])
            yt = self.y[:, t]
            none_arr.append(r["none"][yt])
            hit_arr.append((r["s1"][yt] + r["s2"][yt]) / 8)
        none_stk = np.stack(none_arr)
        return sum(hit_arr[t] * np.prod(np.delete(none_stk, t, 0), 0) for t in range(4))  # type: ignore[return-value]

    def loglik(
        self,
        cols: list[dict[str, NDArray[np.float64]]] | None = None,
        c: float | None = None,
    ) -> float:
        """Compute total floored log-likelihood for the litter.

        Args:
            cols: Optional precomputed column likelihoods.
            c: Optional clone fraction override.

        Returns:
            Sum of log(max(child_lik, FLOOR)) over all children.
        """
        return float(np.log(self.child_lik(cols, c) + FLOOR).sum())

    def _scan_parent(self, parent: str, t: int) -> None:
        """Scan one parent's genes for one trait to maximize log-likelihood."""
        rule = self.m["rules"][t]
        vals = self.A if parent == "A" else self.B
        groups = candidates(rule, int(vals[t]), self.m["rround"])

        def score(g: NDArray[np.intp]) -> tuple[float, tuple[int, int]]:
            g_tup = (int(g[0]), int(g[1]))
            new_cols = list(self.cols)
            new_cols[t] = self._cols(t, *((g_tup, None) if parent == "A" else (None, g_tup)))
            return self.loglik(new_cols), g_tup

        ys = np.unique(self.y[:, t])
        other = self.genes[("B" if parent == "A" else "A", t)]
        key: set[int] = set(ys.tolist())
        if rule == "mean":
            for x in other:
                key |= set((2 * ys - x).tolist()) | set((2 * ys - 1 - x).tolist())
        key_arr = np.array(sorted(key))
        best = (self.loglik(), self.genes[(parent, t)])
        for grp in groups:
            step = max(1, len(grp) // 60)
            idx = set(range(0, len(grp), step)) | set(
                np.flatnonzero(np.isin(grp[:, 0], key_arr) | np.isin(grp[:, 1], key_arr)).tolist()
            )
            coarse = [(score(grp[i]), i) for i in sorted(idx)]
            (s, g), i = max(coarse, key=lambda z: z[0][0])
            for j in range(max(0, i - step), min(len(grp), i + step + 1)):
                s2, g2 = score(grp[j])
                if s2 > s:
                    s, g = s2, g2
            if s > best[0] + 1e-9:
                best = (s, g)
        self.genes[(parent, t)] = best[1]
        self.cols[t] = self._cols(t)

    def _scan_joint(self, t: int) -> None:
        """Joint scan of both parents' genes for one trait."""
        rule = self.m["rules"][t]
        if rule == "mean":
            start = (self.loglik(), self.genes[("A", t)], self.genes[("B", t)])
            best = start
            for grp in candidates(rule, int(self.B[t]), self.m["rround"]):
                s = int(grp[0].sum())
                b1_lo = max(self.genes[("B", t)][0], s - 1000)
                b1 = min(b1_lo, 1000, s)
                self.genes[("B", t)] = (b1, s - b1)
                self.cols[t] = self._cols(t)
                self._scan_parent("A", t)
                ll = self.loglik()
                if ll > best[0] + 1e-9:
                    best = (ll, self.genes[("A", t)], self.genes[("B", t)])
            self.genes[("A", t)], self.genes[("B", t)] = best[1], best[2]
            self.cols[t] = self._cols(t)
            return
        if rule not in ("min", "max"):
            return
        ys = np.unique(self.y[:, t])
        opts: dict[str, set[tuple[int, int]]] = {}
        for p_name, vals in (("A", self.A), ("B", self.B)):
            v = int(vals[t])
            hs = [h for h in ys if (h >= v if rule == "min" else h <= v)]
            opts[p_name] = {(v, int(h)) for h in hs} | {(int(h), v) for h in hs}
        best_joint = (self.loglik(), self.genes[("A", t)], self.genes[("B", t)])
        new_cols = list(self.cols)
        for g_a in opts["A"]:
            for g_b in opts["B"]:
                new_cols[t] = self._cols(t, g_a, g_b)
                ll = self.loglik(new_cols)
                if ll > best_joint[0] + 1e-9:
                    best_joint = (ll, g_a, g_b)
        self.genes[("A", t)], self.genes[("B", t)] = best_joint[1], best_joint[2]
        self.cols[t] = self._cols(t)

    def fit(self, rounds: int = 8) -> float:
        """Run coordinate-ascent fitting.

        Args:
            rounds: Maximum number of optimization rounds.

        Returns:
            Final floored log-score.
        """
        prev = -np.inf
        for _ in range(rounds):
            for t in range(4):
                if self.m["rules"][t] == "g1":
                    continue
                self._scan_joint(t)
                self._scan_parent("A", t)
                self._scan_parent("B", t)
            if self.m["clone"]:
                grid = np.r_[0, np.linspace(0.005, 0.6, 120)]
                self.c = float(grid[np.argmax([self.loglik(c=c_val) for c_val in grid])])
            ll = self.loglik()
            if ll - prev < CONVERGENCE_THRESHOLD:
                break
            prev = ll
        return ll

    def score_other(self, df: pd.DataFrame) -> tuple[float, NDArray[np.float64]]:
        """Log-likelihood of held-out children under this litter's fitted genes.

        Args:
            df: DataFrame of held-out children.

        Returns:
            Tuple of (log-likelihood, per-child likelihoods).
        """
        other = LitterFit(df, self.m)
        other.genes = dict(self.genes)
        other.c = self.c
        other.cols = [other._cols(t) for t in range(4)]
        return other.loglik(), other.child_lik()


def fit_all(df: pd.DataFrame, model: ModelSpec) -> dict[str, LitterFit]:
    """Fit a model to all litters in the dataset.

    Args:
        df: Full dataset DataFrame.
        model: Model specification dict.

    Returns:
        Dict of litter_name -> fitted LitterFit.
    """
    fits: dict[str, LitterFit] = {}
    for name, d in df.groupby("litter", sort=False):
        f = LitterFit(d, model)
        f.fit()
        fits[str(name)] = f
    return fits


def simulate(fit: LitterFit, n: int, rng: np.random.Generator) -> NDArray[np.intp]:
    """Draw n children from a fitted litter.

    Args:
        fit: Fitted litter.
        n: Number of children to simulate.
        rng: Random number generator.

    Returns:
        Array of shape (n, 4) with simulated trait values.
    """
    m = fit.m
    offs, kp = fit.kern
    out = np.zeros((n, 4), dtype=int)
    for i in range(n):
        if m["clone"] and rng.random() < fit.c:
            out[i] = fit.A if rng.random() < PARENT_COIN else fit.B
            continue
        genes = np.zeros((4, 2), dtype=int)
        for t in range(4):
            for s in range(2):
                src = fit.genes[("A" if rng.random() < PARENT_COIN else "B", t)]
                genes[t, s] = src[s]
        hit_list: list[tuple[int, int]]
        if m["mut"] == "one8":
            t_hit, s_hit = divmod(int(rng.integers(8)), 2)
            hit_list = [(t_hit, s_hit)]
        elif m["mut"] == "one_g1":
            hit_list = [(int(rng.integers(4)), 0)]
        else:
            hit_list = [(t, s) for t in range(4) for s in range(2) if rng.random() < m["p"]]
        for t, s in hit_list:
            genes[t, s] = np.clip(genes[t, s] + rng.choice(offs, p=kp), 0, 1000)
        out[i] = [display(m["rules"][t], genes[t, 0], genes[t, 1], m["rround"]) for t in range(4)]
    return out
