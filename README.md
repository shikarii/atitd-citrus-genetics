# Citrus-tree genetics: the model in code

A reproducible test of the proposed inheritance model for ATITD citrus trees
(Indonesian hives). It uses all 692 logged children from 14 litters (both parents known for each).

## Files

| File | What it does |
|---|---|
| `data/children.csv` / `.parquet` | The raw data, one row per child: litter, both parents' 4 values, the child's 4 values. Nothing cleaned or dropped. |
| `extract.py` | Rebuilds `data/` from the `Data` tab of the breeding-log workbook `IndoHives 2026 Data.xlsx` (not included here; `data/children.csv` holds every logged child, so you don't need it). |
| `model.py` | The model: an exact probability for every logged child, given the parents' (partly hidden) genes. The hidden genes are fitted by maximum likelihood, separately for each litter and each model. |
| `compare.py` | Fits the claimed model and 31 rival models to the same data → `results/model_comparison.csv`, `results/fitted_genes_claim.csv`. About 20 min. |
| `sim_checks.py` | Ground truth: makes fake data from known models and checks that the method picks the right one; also posterior-predictive checks → `results/sim_checks.txt`. About 35 min. |
| `report.html` | The same results as one readable page (built by `build_report.py` from `report_template.html`). |
| `length_check.py` | Checks whether a rival Length rule wins only because it has more free values → `results/length_check.txt`. |

Run with Python 3.12, `pip install numpy pandas scipy openpyxl pyarrow`:
`python compare.py && python sim_checks.py 0.14 && python length_check.py`

## The claimed model

- Every tree has 8 genes, 2 per trait, integers 0–1000.
- Shown value: Color = average of its 2 genes (rounded half up), Sweet = lower gene,
  Size = higher gene, Length = gene 1.
- A child copies each gene from a random parent (8 coin flips, slot kept).
- Then exactly one of the 8 genes gets a nudge: a whole number from −150 to +150, all equally likely, clamped to 0–1000.

## Results

**Fit.** The claimed model explains all 692 children. The log-likelihood (higher is better) is −5462.5. Selected rivals:

| Model | Fit | vs claim |
|---|---|---|
| Claimed model | −5462.5 | 0 |
| Triangular nudge ±150 (more small nudges) | −5548.1 | −86 |
| Uniform ±160 / ±175 / ±200 | −5478 / −5497 / −5528 | −16 / −34 / −65 |
| Uniform ±140 / ±125 | −5816 / −6253 | −353 / −791 (15 / 30 children impossible) |
| Every gene nudged independently (best p = 0.14) | −5609.8 | −147 |
| Sweet shown as higher gene | −5531.5 | −69 |
| Sweet shown as average / as gene 1 | −6104 / −6392 | −642 / −929 |
| Size shown as average / as gene 1 | −6007 / −6431 | −544 / −969 |
| Color shown as lower / higher gene | −6272 / −6351 | −809 / −889 |
| One gene per trait (no hidden genes) | −10487 | −5024 (169 children impossible) |

The full table is in `results/model_comparison.csv`.

**Does the method find the truth?** We made fake datasets of the same 14 litters from 3 known
models (the claimed model, independent nudges, triangular nudges), 3 datasets each. Fitting all 3 models,
the true one had the best fit **9 times out of 9**. The gaps on fake data from the claimed model
(about −150 for independent nudges, about −65 for triangular) match the gaps on the real data.

**One nudge per child, not independent nudges.** If nudges were independent per gene (the best rival),
about 97 of the 692 children (95% range 78–115) would show nudges in two or more traits. The real data has 1.

**Posterior-predictive check** (real data vs 300 simulations of the fitted claimed model):

| | Real | Simulated (95% range) |
|---|---|---|
| Children with no visible change | 257 | 226–279 |
| Children with 1 trait changed | 435 | 413–466 |
| Children with 2+ traits changed | 0 | 0–0 |
| Color / Sweet / Size / Length changed | 170 / 92 / 90 / 83 | 143–192 / 76–111 / 75–112 / 67–102 |

**Pedigree consistency.** Each litter is fitted on its own. Start 2 (325/311/408/621) is a parent in
4 litters (1a, 1b, 1c, 7) and Start 1 in 3 (1a, 1b, 1c). The separate fits agree: Start 2 Sweet = 311
+ hidden 320 in 4 of 4, Start 2 Size = 408 + hidden 394 in 3 of 4 (1b: 408/408), Start 1 Size = 642 +
hidden 612 in 3 of 3, Start 1 hidden Sweet ≥ 720 in 3 of 3 (fits 720, 721, 766; only a lower bound is
identifiable).

## Caveats and things that went against the model

- **Held-out scoring prefers the rival.** With 2-fold held-out scoring (fit on half the children,
  score the other half), the independent-nudge model wins by 253. We checked this on fake data:
  held-out scoring also picks the independent-nudge model on data that was **made by the claimed model**
  (3 of 3). It even does so on data made by the triangular model (2 of 3). The reason: a strict model calls a
  held-out child impossible when it shows a hidden gene the other half never revealed (20 such children
  here). On this kind of data, held-out scoring is biased toward lenient models, so we judge by fit, plus the
  fake-data checks that confirm fit picks the truth. All models have the same number of fitted hidden genes.
- **Length.** "Length = gene 1" cannot be told apart from "Length = lower (or higher) gene" by fit alone.
  The rival gains 59 on real data, and 54–66 on fake data where gene 1 is the truth. So the gain is just the
  extra free values. Held-out scoring prefers gene 1 by 392. Only gene 1 is ever seen; the second Length
  gene is inferred from the nudge rate, not seen.
- **Hidden genes are often only bounded.** On fake data the fit recovers 68% of hidden Sweet/Size
  genes exactly. The rest are only known as "at least X" or "at most X".
- **Hive1b.** About 34% of its children are best explained as a full copy of a parent that then gets the
  usual single nudge (only 8 of 72 are exact copies). Copying explains it far better than no copying
  (log-likelihood +41). No other litter needs copying (1a and 1c: 0%). 1b is the only litter whose parents
  stood in different regions; why it copies is open.
- Color's split between its two genes is not identifiable, only their sum. So clamping at 0/1000 for
  Color is approximate.
- This is a fit to observed data. It does not prove this is the game's code. Other mechanisms that produce
  the same probabilities would fit equally well.
