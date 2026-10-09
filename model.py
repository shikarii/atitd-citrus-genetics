"""Exact likelihood model for ATITD citrus-tree (Indonesian hive) inheritance.

A model is a dict:
  rules  : display rule per trait, each one of 'mean', 'min', 'max', 'g1'
           (the value shown for a trait, computed from its 2 genes)
  mut    : 'one8'  -> exactly one of the 8 genes is nudged in every child
           'one_g1'-> exactly one of the 4 gene-1 slots is nudged (a 1-gene-per-trait world)
           'indep' -> every gene is nudged independently with probability p
  p      : per-gene nudge probability (only for 'indep')
  shape  : 'uniform' or 'triangular' nudge distribution on the integers -R..R
  R      : maximum nudge size
  rround : 'halfup' or 'floor' rounding of the mean rule
  clone  : True -> allow a per-litter share c of children that are exact copies of a parent

Genes are integers 0..1000, clamped after a nudge. Each gene of a child is copied from a
random parent (fair coin per gene, slot kept), so a trait has 4 equally likely gene pairs:
(A1,A2), (B1,B2), (A1,B2), (B1,A2).

Per litter, the unknowns are the parents' hidden genes. They are fitted by maximum
likelihood (coordinate ascent over exact integer grids), separately for every litter and
every model, so no model gets values tuned for another.
"""
import numpy as np

TRAITS = ["color", "sweet", "size", "length"]
V = 1001  # gene / display values 0..1000
FLOOR = 1e-15  # likelihood floor: a child the model cannot produce at all scores log(1e-15)

CLAIM = dict(rules=("mean", "min", "max", "g1"), mut="one8", p=None, shape="uniform",
             R=150, rround="halfup", clone=True)


def kernel(shape, R):
    offs = np.arange(-R, R + 1)
    w = np.ones(len(offs)) if shape == "uniform" else (R + 1 - np.abs(offs)).astype(float)
    return offs, w / w.sum()


def display(rule, g1, g2, rround="halfup"):
    if rule == "mean":
        s = g1 + g2
        return (s + 1) // 2 if rround == "halfup" else s // 2
    if rule == "min":
        return np.minimum(g1, g2)
    if rule == "max":
        return np.maximum(g1, g2)
    return g1 + 0 * g2  # 'g1'


def trait_rows(rule, A, B, kern, rround, need_both=False):
    """Distribution of the child's shown value (array over 0..1000) for one trait:
    'none' = no nudge on this trait, 's1'/'s2' = the nudge hit gene slot 1/2,
    'both' = both slots nudged (only needed for the 'indep' model)."""
    offs, kp = kern
    pairs = [(A[0], A[1]), (B[0], B[1]), (A[0], B[1]), (B[0], A[1])]
    rows = {k: np.zeros(V) for k in ("none", "s1", "s2")}
    if need_both:
        rows["both"] = np.zeros(V)
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


def candidates(rule, v, rround="halfup"):
    """All (g1, g2) gene pairs a parent showing v can carry under a display rule,
    as a list of groups (each group is an ordered array, so a coarse-to-fine scan works)."""
    if rule == "mean":
        sums = (2 * v - 1, 2 * v) if rround == "halfup" else (2 * v, 2 * v + 1)
        groups = []
        for s in sums:
            if 0 <= s <= 2000:
                g1 = np.arange(max(0, s - 1000), min(1000, s) + 1)
                groups.append(np.stack([g1, s - g1], 1))
        return groups
    if rule == "min":
        h = np.arange(v, 1001)
    elif rule == "max":
        h = np.arange(0, v + 1)
    else:  # 'g1': gene 2 is never shown and never affects anything shown
        return [np.array([[v, 500]])]
    return [np.stack([np.full_like(h, v), h], 1), np.stack([h, np.full_like(h, v)], 1)]


class LitterFit:
    def __init__(self, df, model):
        self.m = model
        self.kern = kernel(model["shape"], model["R"])
        self.y = df[TRAITS].to_numpy()
        self.A = df[[f"A_{t}" for t in TRAITS]].iloc[0].to_numpy()
        self.B = df[[f"B_{t}" for t in TRAITS]].iloc[0].to_numpy()
        self.need_both = model["mut"] == "indep"
        isA = (self.y == self.A).all(1)
        isB = (self.y == self.B).all(1)
        self.clone_lik = 0.5 * isA + 0.5 * isB
        self.c = 0.0
        # start: mean rule -> genes split evenly; min/max -> two copies of the shown gene
        self.genes = {}
        for t, rule in enumerate(model["rules"]):
            for P, vals in (("A", self.A), ("B", self.B)):
                grp = candidates(rule, int(vals[t]), model["rround"])
                if rule == "mean":
                    g = grp[-1][len(grp[-1]) // 2]
                elif rule in ("min", "max"):
                    g = np.array([vals[t], vals[t]])
                else:
                    g = grp[0][0]
                self.genes[(P, t)] = tuple(int(x) for x in g)
        self.cols = [self._cols(t) for t in range(4)]

    def _cols(self, t, gA=None, gB=None):
        gA = gA or self.genes[("A", t)]
        gB = gB or self.genes[("B", t)]
        r = trait_rows(self.m["rules"][t], gA, gB, self.kern, self.m["rround"], self.need_both)
        yt = self.y[:, t]
        out = {"none": r["none"][yt], "s1": r["s1"][yt], "s2": r["s2"][yt]}
        if self.need_both:
            out["both"] = r["both"][yt]
        return out

    def child_lik(self, cols=None, c=None):
        cols = cols or self.cols
        c = self.c if c is None else c
        mut = self.m["mut"]
        if mut == "indep":
            p = self.m["p"]
            L = np.ones(len(self.y))
            for k in cols:
                L *= (1 - p) ** 2 * k["none"] + p * (1 - p) * (k["s1"] + k["s2"]) + p * p * k["both"]
        else:
            none = np.stack([k["none"] for k in cols])
            if mut == "one8":
                hit = np.stack([k["s1"] + k["s2"] for k in cols]) / 8
            else:  # one_g1
                hit = np.stack([k["s1"] for k in cols]) / 4
            L = np.zeros(len(self.y))
            for t in range(4):
                L += hit[t] * np.prod(np.delete(none, t, 0), 0)
        if self.m["clone"] == "nudged":
            # a copy of one parent's 8 genes that then gets the usual single nudge
            # (uses the current genes; during a scan the scanned trait lags one step,
            # the final log-likelihood is exact)
            L = (1 - c) * L + c * 0.5 * (self._self_lik("A") + self._self_lik("B"))
        elif self.m["clone"]:
            L = (1 - c) * L + c * self.clone_lik
        return L

    def _self_lik(self, P):
        none, hit = [], []
        for t in range(4):
            g = self.genes[(P, t)]
            r = trait_rows(self.m["rules"][t], g, g, self.kern, self.m["rround"])
            yt = self.y[:, t]
            none.append(r["none"][yt])
            hit.append((r["s1"][yt] + r["s2"][yt]) / 8)
        none = np.stack(none)
        return sum(hit[t] * np.prod(np.delete(none, t, 0), 0) for t in range(4))

    def loglik(self, cols=None, c=None):
        return float(np.log(self.child_lik(cols, c) + FLOOR).sum())

    def _scan_parent(self, P, t):
        rule = self.m["rules"][t]
        vals = self.A if P == "A" else self.B
        groups = candidates(rule, int(vals[t]), self.m["rround"])

        def score(g):
            g = tuple(int(x) for x in g)
            cols = list(self.cols)
            cols[t] = self._cols(t, *((g, None) if P == "A" else (None, g)))
            return self.loglik(cols), g

        # The likelihood is spiky (children land on exact values), so a plain coarse grid can
        # step over the right hidden gene. Always try every gene value that would let some
        # child's value appear exactly, plus a coarse grid, then refine around the best.
        ys = np.unique(self.y[:, t])
        other = self.genes[("B" if P == "A" else "A", t)]
        key = set(ys.tolist())
        if rule == "mean":
            for x in other:
                key |= set((2 * ys - x).tolist()) | set((2 * ys - 1 - x).tolist())
        key = np.array(sorted(key))
        best = (self.loglik(), self.genes[(P, t)])
        for grp in groups:
            step = max(1, len(grp) // 60)
            idx = set(range(0, len(grp), step)) | set(np.flatnonzero(
                np.isin(grp[:, 0], key) | np.isin(grp[:, 1], key)).tolist())
            coarse = [(score(grp[i]), i) for i in sorted(idx)]
            (s, g), i = max(coarse, key=lambda z: z[0][0])
            for j in range(max(0, i - step), min(len(grp), i + step + 1)):
                s2, g2 = score(grp[j])
                if s2 > s:
                    s, g = s2, g2
            if s > best[0] + 1e-9:
                best = (s, g)
        self.genes[(P, t)] = best[1]
        self.cols[t] = self._cols(t)

    def _scan_joint(self, t):
        """For min/max rules a value below/above both parents needs BOTH parents' hidden
        genes to move at once, which one-parent-at-a-time scans cannot find. Try every
        combination of hidden genes taken from the values seen in the children."""
        rule = self.m["rules"][t]
        if rule == "mean":
            # the parents' gene sums are only known to +-1 (rounding); try each of B's sums,
            # re-scanning A for each, and keep the best
            start = (self.loglik(), self.genes[("A", t)], self.genes[("B", t)])
            best = start
            for grp in candidates(rule, int(self.B[t]), self.m["rround"]):
                s = int(grp[0].sum())
                b1 = min(max(self.genes[("B", t)][0], s - 1000), min(1000, s))
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
        opts = {}
        for P, vals in (("A", self.A), ("B", self.B)):
            v = int(vals[t])
            hs = [h for h in ys if (h >= v if rule == "min" else h <= v)]
            opts[P] = {(v, int(h)) for h in hs} | {(int(h), v) for h in hs}
        best = (self.loglik(), self.genes[("A", t)], self.genes[("B", t)])
        cols = list(self.cols)
        for gA in opts["A"]:
            for gB in opts["B"]:
                cols[t] = self._cols(t, gA, gB)
                s = self.loglik(cols)
                if s > best[0] + 1e-9:
                    best = (s, gA, gB)
        self.genes[("A", t)], self.genes[("B", t)] = best[1], best[2]
        self.cols[t] = self._cols(t)

    def fit(self, rounds=8):
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
                self.c = float(grid[np.argmax([self.loglik(c=c) for c in grid])])
            ll = self.loglik()
            if ll - prev < 1e-6:
                break
            prev = ll
        return ll

    def score_other(self, df):
        """Log-likelihood of other children (held-out) under this litter's fitted genes."""
        other = LitterFit(df, self.m)
        other.genes, other.c = dict(self.genes), self.c
        other.cols = [other._cols(t) for t in range(4)]
        return other.loglik(), other.child_lik()


def fit_all(df, model):
    fits = {}
    for name, d in df.groupby("litter", sort=False):
        f = LitterFit(d, model)
        f.fit()
        fits[name] = f
    return fits


def simulate(fit, n, rng):
    """Draw n children from a fitted litter (its genes, nudge model and clone share)."""
    m = fit.m
    offs, kp = fit.kern
    out = np.zeros((n, 4), dtype=int)
    for i in range(n):
        if m["clone"] and rng.random() < fit.c:
            out[i] = fit.A if rng.random() < 0.5 else fit.B
            continue
        genes = np.zeros((4, 2), dtype=int)
        for t in range(4):
            for s in range(2):
                src = fit.genes[("A" if rng.random() < 0.5 else "B", t)]
                genes[t, s] = src[s]
        if m["mut"] == "one8":
            hits = [divmod(rng.integers(8), 2)]
        elif m["mut"] == "one_g1":
            hits = [(rng.integers(4), 0)]
        else:
            hits = [(t, s) for t in range(4) for s in range(2) if rng.random() < m["p"]]
        for t, s in hits:
            genes[t, s] = np.clip(genes[t, s] + rng.choice(offs, p=kp), 0, 1000)
        out[i] = [display(m["rules"][t], genes[t, 0], genes[t, 1], m["rround"]) for t in range(4)]
    return out
