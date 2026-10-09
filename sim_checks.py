"""Ground-truth checks with synthetic data, where the true answer is known.

1. Model recovery: build fake datasets (same 14 litters, same sizes) from the fitted CLAIM
   model, from the best rival 'independent nudges' model, and from the triangular rival.
   Fit all three models to each fake dataset. If the method works, the true generator wins
   each time; if it cannot tell them apart, the comparison on the real data means little.
2. Hidden-gene recovery: on the fake CLAIM datasets, how often does the fit get the planted
   hidden Sweet/Size genes exactly right?
3. Posterior-predictive check: simulate the real litters many times from the fitted CLAIM
   model and compare simple counts (children with 0 / 1 / 2+ visibly changed traits, and
   which trait changed) with the real data.

Usage: python sim_checks.py [p_indep]   (default 0.11). Writes results/sim_checks.txt.
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from model import CLAIM, TRAITS, LitterFit, simulate, trait_rows, kernel

HERE = Path(__file__).parent
P_INDEP = float(sys.argv[1]) if len(sys.argv) > 1 else 0.11
MODELS = {"CLAIM": CLAIM,
          "INDEP": {**CLAIM, "mut": "indep", "p": P_INDEP},
          "TRI150": {**CLAIM, "shape": "triangular"}}


def fake_dataset(gen_name, seed):
    df = pd.read_csv(HERE / "data" / "children.csv")
    rng = np.random.default_rng(seed)
    parts, truth = [], {}
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, MODELS[gen_name])
        f.fit()
        y = simulate(f, len(d), rng)
        dd = d.copy()
        dd[TRAITS] = y
        parts.append(dd)
        truth[lit] = dict(f.genes)
    return pd.concat(parts), truth


def recovery_job(args):
    gen_name, seed = args
    fake, truth = fake_dataset(gen_name, seed)
    ll, cv, hits, tot = {}, {}, 0, 0
    for name, m in MODELS.items():
        s, c = 0.0, 0.0
        for lit, d in fake.groupby("litter", sort=False):
            f = LitterFit(d, m)
            s += f.fit()
            for tr, te in ((d.iloc[0::2], d.iloc[1::2]), (d.iloc[1::2], d.iloc[0::2])):
                g = LitterFit(tr, m)
                g.fit()
                c += g.score_other(te)[0]
            if name == gen_name == "CLAIM":
                for t in (1, 2):
                    for P in "AB":
                        tot += 1
                        hits += sorted(f.genes[(P, t)]) == sorted(truth[lit][(P, t)])
        ll[name], cv[name] = round(s, 1), round(c, 1)
    return gen_name, seed, ll, cv, (hits, tot)


def support(f, t):
    r = trait_rows(f.m["rules"][t], f.genes[("A", t)], f.genes[("B", t)], kernel("uniform", 150), f.m["rround"])
    return set(np.flatnonzero(r["none"] > 0).tolist())


def changed(f, y):
    """Per child and trait: True if the shown value cannot come from the 4 gene pairs
    without a nudge (a visibly nudged trait), given the fitted genes."""
    sup = [support(f, t) for t in range(4)]
    return np.array([[y[i, t] not in sup[t] for t in range(4)] for i in range(len(y))])


def ppc(n_sims=300, seed=1):
    df = pd.read_csv(HERE / "data" / "children.csv")
    rng = np.random.default_rng(seed)
    obs_k, obs_tr = np.zeros(3), np.zeros(4)
    sim_k, sim_tr = np.zeros((n_sims, 3)), np.zeros((n_sims, 4))
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, CLAIM)
        f.fit()
        ch = changed(f, d[TRAITS].to_numpy())
        k = np.minimum(ch.sum(1), 2)
        obs_k += np.bincount(k, minlength=3)
        obs_tr += ch.sum(0)
        for s in range(n_sims):
            cs = changed(f, simulate(f, len(d), rng))
            sim_k[s] += np.bincount(np.minimum(cs.sum(1), 2), minlength=3)
            sim_tr[s] += cs.sum(0)
    return obs_k, obs_tr, sim_k, sim_tr


def indep_two_trait_expectation(n_sims=200, seed=2):
    """If nudges were independent per gene (the best rival), how many children would show
    nudges in 2+ traits? Uses the rival's own fitted genes."""
    df = pd.read_csv(HERE / "data" / "children.csv")
    rng = np.random.default_rng(seed)
    obs, sims = 0, np.zeros(n_sims)
    for lit, d in df.groupby("litter", sort=False):
        f = LitterFit(d, MODELS["INDEP"])
        f.fit()
        obs += int((changed(f, d[TRAITS].to_numpy()).sum(1) >= 2).sum())
        for s in range(n_sims):
            sims[s] += (changed(f, simulate(f, len(d), rng)).sum(1) >= 2).sum()
    return obs, sims


if __name__ == "__main__":
    lines = [f"Rival 'independent nudges' model uses p = {P_INDEP}", ""]
    jobs = [(g, s) for g in MODELS for s in (11, 12, 13)]
    with ProcessPoolExecutor() as ex:
        rec = list(ex.map(recovery_job, jobs))
    lines.append("1. MODEL RECOVERY (log-likelihood of each fitted model on fake data; higher = better)")
    for gen, seed, ll, cv, (h, tot) in rec:
        for lab, sc in (("fit", ll), ("held-out", cv)):
            win = max(sc, key=sc.get)
            lines.append(f"   data made by {gen:6s} seed {seed}, {lab:8s}: " + ", ".join(f"{k} {v}" for k, v in sc.items())
                         + f"  -> best: {win} {'OK' if win == gen else 'WRONG'}")
    h = sum(r[4][0] for r in rec if r[0] == "CLAIM")
    tot = sum(r[4][1] for r in rec if r[0] == "CLAIM")
    lines += ["", f"2. HIDDEN-GENE RECOVERY on fake CLAIM data: {h} of {tot} hidden Sweet/Size gene pairs exactly right", ""]

    obs_k, obs_tr, sim_k, sim_tr = ppc()
    lines.append("3. POSTERIOR-PREDICTIVE CHECK (real data vs 300 simulations of the fitted CLAIM model)")
    for lab, o, s in zip(["0 traits visibly changed", "1 trait visibly changed", "2+ traits visibly changed"], obs_k, sim_k.T):
        lines.append(f"   {lab:28s} real {int(o):4d}   simulated mean {s.mean():6.1f}, 95% range {np.percentile(s, 2.5):.0f}-{np.percentile(s, 97.5):.0f}")
    for t, o, s in zip(TRAITS, obs_tr, sim_tr.T):
        lines.append(f"   {t:8s} visibly changed     real {int(o):4d}   simulated mean {s.mean():6.1f}, 95% range {np.percentile(s, 2.5):.0f}-{np.percentile(s, 97.5):.0f}")
    obs2, sims2 = indep_two_trait_expectation()
    lines += ["", f"4. RIVAL CHECK: under independent nudges (p={P_INDEP}, its own fitted genes) children with 2+ visibly",
              f"   changed traits: real {obs2}, expected {sims2.mean():.1f} (95% range {np.percentile(sims2, 2.5):.0f}-{np.percentile(sims2, 97.5):.0f})"]
    txt = "\n".join(lines)
    (HERE / "results" / "sim_checks.txt").write_text(txt, encoding="utf-8")
    print(txt)
