"""Fit the claimed model and a set of rival models to the same 692 children, and score each
two ways:
  fit_ll : log-likelihood with every litter's hidden genes fitted on all its children
  cv_ll  : 2-fold held-out log-likelihood (fit on odd children, score even ones, and the
           reverse), so a model with more freedom gets no free credit
Higher is better for both. A difference of 10 in log-likelihood means the data are
e^10 (about 22,000) times more probable under the better model.

Writes results/model_comparison.csv and results/fitted_genes_claim.csv.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from model import CLAIM, TRAITS, LitterFit

HERE = Path(__file__).parent


def variants():
    v = {"CLAIM: 1 of 8 genes, uniform +-150": CLAIM}
    for R in (100, 125, 140, 160, 175, 200):
        v[f"uniform +-{R}"] = {**CLAIM, "R": R}
    for R in (150, 200, 250):
        v[f"triangular +-{R}"] = {**CLAIM, "shape": "triangular", "R": R}
    for p in (0.08, 0.11, 0.14, 0.17, 0.20):
        v[f"each gene nudged independently, p={p}"] = {**CLAIM, "mut": "indep", "p": p}
    v["1 gene per trait (no hidden genes)"] = {**CLAIM, "rules": ("g1",) * 4, "mut": "one_g1"}
    for t, trait in enumerate(TRAITS):
        for alt in ("mean", "min", "max", "g1"):
            if alt != CLAIM["rules"][t]:
                rules = list(CLAIM["rules"]); rules[t] = alt
                v[f"{trait} shown as {alt}"] = {**CLAIM, "rules": tuple(rules)}
    v["color rounds down"] = {**CLAIM, "rround": "floor"}
    v["no clone component"] = {**CLAIM, "clone": False}
    return v


def run(args):
    name, model = args
    df = pd.read_csv(HERE / "data" / "children.csv")
    fit_ll, cv_ll, bad, per = 0.0, 0.0, 0, {}
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, model)
        ll = f.fit()
        fit_ll += ll
        bad += int((f.child_lik() < 1e-9).sum())
        per[lit] = ll
        odd, even = d.iloc[0::2], d.iloc[1::2]
        for tr, te in ((odd, even), (even, odd)):
            g = LitterFit(tr, model)
            g.fit()
            cv_ll += g.score_other(te)[0]
    return dict(model=name, fit_ll=round(fit_ll, 1), cv_ll=round(cv_ll, 1),
                children_impossible=bad, **{f"ll_{k}": round(x, 1) for k, x in per.items()})


if __name__ == "__main__":
    (HERE / "results").mkdir(exist_ok=True)
    jobs = list(variants().items())
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(run, jobs))
    res = pd.DataFrame(rows)
    best = res.loc[res.model.str.startswith("CLAIM")].iloc[0]
    res.insert(3, "cv_vs_claim", (res.cv_ll - best.cv_ll).round(1))
    res = res.sort_values("cv_ll", ascending=False)
    res.to_csv(HERE / "results" / "model_comparison.csv", index=False)
    print(res[["model", "fit_ll", "cv_ll", "cv_vs_claim", "children_impossible"]].to_string(index=False))

    df = pd.read_csv(HERE / "data" / "children.csv")
    out = []
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, CLAIM)
        f.fit()
        row = {"litter": lit, "n": len(d), "clone_share": round(f.c, 3), "loglik": round(f.loglik(), 1)}
        for t, tr in enumerate(TRAITS):
            row[f"A_{tr}_genes"] = "%d/%d" % f.genes[("A", t)]
            row[f"B_{tr}_genes"] = "%d/%d" % f.genes[("B", t)]
        out.append(row)
    pd.DataFrame(out).to_csv(HERE / "results" / "fitted_genes_claim.csv", index=False)
