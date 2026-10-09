# Research Methodology: ATITD Citrus Genetics

A critical examination of how we investigate citrus tree breeding mechanics in
A Tale in the Desert (ATITD). This document separates confirmed facts from
speculation, audits the assumptions baked into our current analysis, and
proposes alternative research methods for exploring a black-box system without
getting locked into any single theory.

---

## 1. Source and Ground Truth

### 1.1 The Wiki Source

The community's understanding of citrus genetics comes from the
[Indonesian Beehives guide on the ATITD Tale 11 wiki](https://atitd.wiki/tale11/Guides/Indonesian_Beehives#Estimated_Ideal_Values).
This is a player-compiled guide, not official documentation. The game
developers have never published source code or mechanics specifications.

### 1.2 Confirmed: Species Expression Is Nearest-Neighbor in 4D Trait Space

The only non-speculative knowledge is the species expression table. Every
citrus tree has four observable traits: Color, Sweet, Size, and Length, each
an integer from 0 to 1000. These four values define a point in a
4-dimensional trait space. The species a tree expresses is determined by
which known species centroid its trait point is closest to.

This is empirically confirmed by many players across hundreds of trees. The
centroids (based on ~1,300 recorded Indonesian Hives):

| Species | Color | Sweet | Size | Length |
|---|---|---|---|---|
| Amanatsu | 540 | 230 | 560 | 550 |
| Buddha's Hand | 170 | 390 | 830 | 730 |
| Calamondin | 450 | 620 | 860 | 100 |
| Citron | 570 | 770 | 280 | 260 |
| Coralfruit | 570 | 800 | 550 | 60 |
| Corian | 330 | 380 | 440 | 190 |
| Etrog | 550 | 660 | 610 | 380 |
| Grapefruit | 620 | 680 | 290 | 70 |
| Iyokan | 660 | 260 | 570 | 200 |
| Kabosu | 350 | 410 | 670 | 570 |
| Kinnow | 740 | 770 | 630 | 560 |
| Kumquat | 630 | 350 | 640 | 550 |
| Lemon | 670 | 210 | 760 | 920 |
| Lenat | 800 | 230 | 150 | 970 |
| Lime | 490 | 290 | 840 | 940 |
| Mandarin | 530 | 650 | 720 | 630 |
| Orange | 360 | 670 | 850 | 650 |
| Oroblanco | 220 | 810 | 560 | 550 |
| Pummelo | 760 | 660 | 390 | 540 |
| Rangpur | 840 | 500 | 710 | 100 |
| Shangjuan | 410 | 570 | 420 | 560 |
| Sudachi | 290 | 200 | 830 | 600 |
| Summerbell | 750 | 710 | 400 | 930 |
| Tangelo | 750 | 670 | 920 | 820 |
| Tangerine | 220 | 610 | 950 | 230 |
| Yuzu | 370 | 370 | 460 | 840 |

These centroids are averages of observed trees. The actual species boundaries
are Voronoi cells around these points in 4D space -- a tree becomes whatever
species it is closest to. The distance metric (Euclidean, Manhattan, or other)
and exact boundary positions have not been independently verified, but the
centroids themselves are well-established from large sample sizes.

**What this means**: species identity is a deterministic function of the four
observable trait values. The breeding problem reduces to: how do you move a
tree's trait point to a desired region of 4D space?

### 1.3 The Speculative Theory

Everything below is reverse-engineered from observed breeding outcomes. None
of it has been confirmed by the game developers or source code inspection.

| Claim | Summary | Confidence |
|---|---|---|
| C1 | Each tree has 8 hidden gene values (2 per trait), integers 0-1000 | Medium -- 1-gene model is catastrophically bad, but 3+ genes untested |
| C2 | Color = mean(g1, g2) with round-half-up | High -- alternatives score 600-900 worse |
| C3 | Sweet = min(g1, g2) | High -- mean and g1 alternatives score 640-930 worse |
| C4 | Size = max(g1, g2) | High -- alternatives score 540-970 worse |
| C5 | Length = g1 only (g2 unobservable) | Medium -- min/max alternatives gain 59, within noise |
| C6 | Inheritance: fair coin flip per gene slot, slot-preserving | Medium -- untested alternatives exist |
| C7 | Exactly 1 of 8 genes nudged per child | High -- only 1 of 692 children shows 2+ trait changes (expected 97 under independent nudges) |
| C8 | Nudge: uniform distribution on integers -150 to +150 | Medium -- triangular is 86 worse, but Gaussian/Laplacian untested |
| C9 | Nudge clamped to [0, 1000] | Low -- wrapping and reflecting untested |
| C10 | Cloning: some children are exact copies of one parent | Medium -- strong evidence in Hive1b only (34% clone share, +41 log-likelihood vs no clone) |

### 1.4 Provenance Chain

```
Game source code  (unknown, unobservable)
       |
       v
Player observations  (breeding logs, manual recording)
       |
       v
Wiki documentation  (community synthesis, Tale 11 era)
       |
       v
Our formalized model  (precise mathematical encoding)
```

Each link introduces potential errors. Player observations may have recording
mistakes or missing children. The wiki synthesizes across players who may have
had different game versions or misunderstood edge cases. Our formalization
makes choices (integer gene space, specific floor value, specific convergence
criterion) that could introduce artifacts.

---

## 2. Current Exploration Approach

This section summarizes what the project does today. For full technical
specification, see `systems_engineering.md` Section 4.

### 2.1 Data

The dataset is 692 children from 14 litters in `data/children.csv`. Each
record has: the litter name, child ID, parent A's 4 observable traits,
parent B's 4 observable traits, and the child's 4 observable traits. No
hidden gene values are observed.

Notable structure:
- Litters range from 20 to 72 children
- Hive1a, Hive1b, Hive1c share the same parent pair
- Hive7 shares one parent with the Hive1 group
- The dataset is SHA-256 fingerprinted for provenance tracking

### 2.2 The CLAIM Model

The community theory is encoded as a Python dict in `core/constants.py`:

```python
CLAIM = {
    "rules": ("mean", "min", "max", "g1"),  # display rules per trait
    "mut": "one8",      # exactly 1 of 8 genes nudged
    "p": None,          # not used for one8
    "shape": "uniform", # nudge distribution shape
    "R": 150,           # nudge range: -150 to +150
    "rround": "halfup", # rounding mode for mean display rule
    "clone": True,      # allow clone component
}
```

The fitting engine (`core/model.py:LitterFit`) takes a model spec and a
litter of children, then finds the hidden gene values that maximize the
floored log-score via coordinate ascent. The clone fraction is fitted per
litter via 121-point grid search over c in {0.0, 0.005, ..., 0.600}.

### 2.3 The 30-Model Comparison

The project tests CLAIM against 29 rivals in `pipelines/compare.py`. The
rivals vary one axis at a time from the CLAIM spec:

| Axis | Variants | Count |
|---|---|---|
| Nudge range | R in {100, 125, 140, 160, 175, 200} | 6 |
| Nudge shape | Triangular, R in {150, 200, 250} | 3 |
| Nudge mechanism | Independent, p in {0.08, 0.11, 0.14, 0.17, 0.20} | 5 |
| Gene count | 1 gene per trait (no hidden genes) | 1 |
| Display rules | Each trait tested with each alternative rule | 12 |
| Rounding | Color rounds down instead of half-up | 1 |
| Cloning | No clone component | 1 |
| **Total** | CLAIM + 29 rivals | **30** |

### 2.4 Fitting Method

For each model and each litter independently:

1. Initialize hidden gene values from parent observables
2. Coordinate ascent: scan gene pairs for each trait, optimizing one trait at
   a time while holding others fixed
3. Scan order: joint (both parents), then parent A alone, then parent B alone
4. Clone fraction: grid search over 121 values of c
5. Convergence: stop when per-round log-likelihood improvement < 1e-6 or
   after 8 rounds
6. Floored scoring: any child with raw probability < 1e-15 is scored at 1e-15
   (not a proper likelihood -- a heuristic floor)

### 2.5 Validation Layers

| Layer | What it tests | Result |
|---|---|---|
| Model recovery | Generate fake data from known model, verify correct model wins | 9/9 correct |
| Gene recovery | Fit to synthetic CLAIM data, check hidden genes recovered | 68% exact match |
| PPC | Simulate from fitted model, compare 7 summary statistics | All within 95% range |
| Multi-trait changes | Count children with 2+ trait changes | 1 real vs 97 expected under INDEP |
| Optimizer validation | Exhaustive search on V=3 and V=11 gene spaces | Matches coordinate ascent |
| Pedigree consistency | Shared parents fitted independently agree on hidden genes | Consistent across litters |

### 2.6 Current Results

CLAIM ranks #1 on in-sample fit log-likelihood at -5462.5. See `README.md`
for the full results table.

Key caveats (documented in `README.md`):
- Held-out cross-validation prefers the independent-nudge rival by 253
  log-likelihood units. This bias is confirmed on synthetic data: cv_ll picks
  INDEP even on CLAIM-generated data (3/3).
- Length display rule (g1 vs min/max) cannot be distinguished by fit alone.
- Hidden genes are often only bounded, not exactly identified.
- Hive1b shows a 34% clone component; no other litter does.

---

## 3. Assumption Audit

An adversarial examination of what assumptions are baked into the current
approach and how each could be wrong.

### 3.1 Structural Assumptions (About the Game)

**A1: Exactly 2 genes per trait.** The 1-gene model is catastrophic
(fit_ll = -10487, 169 impossible children), providing strong evidence for
*at least* 2 genes. But 3 genes per trait has never been tested. A 3-gene
model would have a different inheritance structure (3 coin flips per trait)
and different display rules (median? weighted average?). The terrible
performance of 1-gene is evidence against 1 gene, not proof of exactly 2.

**A2: Integer gene values in [0, 1000].** The model assumes discrete integer
genes. If the game uses floating-point values internally, our discrete
probability calculations are approximations. The range could be [0, 999] or
[0, 10000] with the display value being a rescaling. The integer assumption
is load-bearing: it makes exact probability calculation tractable. Changing it
to continuous values would require a fundamentally different likelihood
framework (probability densities instead of discrete probabilities).

**A3: Slot-preserving inheritance.** The model assumes child gene slot 1
always comes from a parent's gene slot 1. If inheritance allows slot swapping
(child slot 1 can come from parent's slot 2), the identifiability structure
changes. For min/max display rules, swapping g1 and g2 can produce
observationally different offspring distributions (because nudging g1 vs g2
has different effects on the displayed value). For the mean rule, slot
swapping is observationally equivalent (mean is symmetric). This is partially
testable but has not been tested.

**A4: Fair 50/50 coin flip per gene.** Could be biased (e.g. 60/40 toward
one parent). Could be correlated across genes (all 8 from the same parent
sometimes). Could depend on proximity, tree age, or species. The current
framework does not test biased-coin models: a biased coin would degrade
CLAIM's fit, but since we never fit a biased-coin variant we would not know
if it fits better.

**A5: Exactly one mutation per child.** The one-of-8 model assumes exactly
one gene is nudged. The INDEP model allows 0 or multiple. The multi-trait
change count (1 child with 2+ changes vs 97 expected under INDEP) strongly
supports at most one visible mutation. But what about a model where 90% of
children get 1 mutation and 10% get 0? Or where 95% get 1 and 5% get 2? The
current framework tests "exactly 1" vs "independently with probability p"
but not the space in between.

**A6: Uniform nudge distribution.** Tested against triangular (86 worse) but
not against Gaussian, Laplacian, beta, or empirical distributions. The shape
distinction is subtle: with R=150, a uniform nudge has standard deviation 87;
a triangular has SD 61. Different shapes mainly affect the tails. With only
692 children and most nudges invisible (hidden gene changes that do not
affect the display value), the data may not have enough power to distinguish
shapes.

**A7: Display rules tested one at a time.** The 30-model manifest varies one
trait's display rule per rival. No model tests combinations of non-standard
rules (e.g. what if both Sweet and Size use mean?). If two display rules are
wrong, no single-swap rival will score well, and the error will be invisible.
There are 4^4 - 1 = 255 non-CLAIM display rule combinations; only 12 are
tested.

**A8: Clamping at 0 and 1000.** After mutation, genes exceeding [0, 1000] are
clamped. Alternatives: wrapping (1050 becomes 50) or reflecting (1050 becomes
950). This matters only for genes near the boundaries. With R=150, a gene at
value 900 has a 15% chance of hitting the upper boundary. Wrapping vs clamping
would produce different offspring distributions for extreme-valued parents.
Not tested.

**A9: Parent assignment in data is correct.** The project takes the recorded
parent A and parent B at face value. If the game's parent-selection mechanism
differs from what was recorded (wrong parent identified, a third tree
interfering, coordinate edge cases with the +/-19 range), the model would
be fitting noise as signal. Parent assignment errors would most likely
manifest as "impossible" children -- and the CLAIM model has 0 impossible
children, which is reassuring.

**A10: Children are independent given parents.** Each child is modeled as an
independent draw given the parents' hidden genes. If the game uses a shared
random state (e.g. a sequential PRNG where the first child's mutation affects
the second child's seed), the independence assumption is wrong. This could be
tested by looking for serial correlations between siblings' trait values
within a litter.

### 3.2 Methodological Assumptions (About Our Testing)

**M1: Maximum likelihood is the right criterion.** MLE selects the model that
assigns highest probability to observed data *at the best-fit hidden genes*.
This conflates model adequacy with parameter estimation quality. A model with
more flexible hidden-gene structure gets penalized less by poor estimation.
The cv_ll vs fit_ll discrepancy (INDEP wins cv_ll, CLAIM wins fit_ll) is a
direct manifestation of this problem.

**M2: The floor hides information.** Children scored at the 1e-15 floor are
the strongest evidence against a model. Under the uniform +/-140 model, 15
children are impossible; under +/-125, 30 are impossible. But the floor
compresses their signal to a fixed -34.5 per child penalty regardless of
*how* impossible they are. A contamination model (e.g. "with probability
epsilon, the child is drawn uniformly") would handle this more informatively.

**M3: Per-litter independence in fitting.** Hidden genes are fitted
independently per litter. When litters share parents (Hive1a/1b/1c and
Hive7), the independent fits do not enforce consistency. The README notes
that fits *do* agree across litters (pedigree consistency check), but this
is observed post-hoc, not enforced during fitting. Joint fitting across
litters with shared parents would be more principled and could improve
gene recovery.

**M4: The rival set is not exhaustive.** All 30 models assume 2 genes per
trait, the same general inheritance mechanism, and the same display-rule
format. The rivals vary parameters within the CLAIM framework. No rival
tests a fundamentally different architecture (e.g. 3 genes, continuous
latent variables, trait-trait coupling, environmental factors). The
comparison answers "which CLAIM variant fits best?" not "is CLAIM the right
kind of model?"

**M5: Cross-validation is biased.** Documented in `README.md`: held-out
scoring picks INDEP even on CLAIM-generated synthetic data (3/3 seeds). The
mechanism is understood (strict models call held-out children impossible when
hidden-gene estimation fails on the training fold), but it means cv_ll
cannot serve as the primary model selection criterion for this problem.

**M6: Optimizer quality may be model-dependent.** Coordinate ascent may find
better optima for some models than others, giving those models an unfair
advantage. The optimizer validation (exhaustive on V=3 and V=11, multi-start
escalation) partially addresses this but only covers a few models.

**M7: Sample size limitations.** With 692 children across 14 litters, many
model distinctions are near the noise floor. The fit_ll gap between CLAIM
and uniform +/-160 is only 16 log-likelihood units. On synthetic data, gaps
of similar magnitude arise between the true model and its closest rival,
suggesting the data is near the discrimination limit for closely-related
specifications.

### 3.3 The Streetlight Problem

The current approach is excellent at answering: "which of these 30 similar
models best explains the data?" It cannot answer: "does any model in this
family explain the data well?"

The PPC is the only check that partially addresses this. It compares 7
summary statistics (children with 0/1/2+ trait changes, per-trait change
counts) between real data and simulated data from the fitted model. All real
counts fall within simulated 95% ranges. But 7 coarse statistics are a weak
test. A model could match these 7 statistics while being wrong in ways the
statistics do not capture.

We are searching for our keys under the streetlight. The 30-model comparison
tells us where on this street the keys are most likely. It does not tell us
whether the keys are on this street at all.

---

## 4. Alternative Research Methods

Each method below includes: what question it answers, how to apply it to the
ATITD data specifically, what it would reveal that current methods cannot,
and an implementation sketch.

### 4.1 Model-Free Information Theory

**Question**: How much information do parent traits carry about child traits,
without assuming any model?

**Method**: Compute mutual information I(parent_trait; child_trait) for all
32 parent-child trait pairs (4 parent A traits x 4 child traits + 4 parent
B traits x 4 child traits). Use a non-parametric estimator (k-nearest-
neighbor, e.g. the Kraskov-Stoegbauer-Grassberger estimator via
`sklearn.feature_selection.mutual_info_regression`).

**Expected result under CLAIM**: The MI matrix should be approximately
block-diagonal. Each child trait depends on the corresponding parent traits
from both parents (I(A_color; child_color) > 0, I(B_color; child_color) > 0)
but not on non-corresponding traits (I(A_color; child_sweet) ~ 0). Also,
parent A and B should contribute symmetrically (the 50/50 coin implies
I(A_trait; child_trait) ~ I(B_trait; child_trait)).

**What violations would mean**:
- Significant off-diagonal MI: traits are coupled in ways the model misses.
  Could indicate shared genes across traits, environmental effects, or a
  different inheritance mechanism.
- Asymmetric parent contributions: the coin flip is not 50/50, or parent
  selection depends on proximity/species.
- Near-zero MI for a supposedly informative pair: the assumed display rule
  for that trait may be wrong, obscuring the parent-child relationship.

**Implementation sketch**:

```python
# Pseudocode -- not production code
from sklearn.feature_selection import mutual_info_regression
import numpy as np

parent_cols = ["A_color", "A_sweet", "A_size", "A_length",
               "B_color", "B_sweet", "B_size", "B_length"]
child_cols = ["color", "sweet", "size", "length"]

mi_matrix = np.zeros((8, 4))
for i, pcol in enumerate(parent_cols):
    for j, ccol in enumerate(child_cols):
        mi_matrix[i, j] = mutual_info_regression(
            df[[pcol]].values, df[ccol].values, n_neighbors=5
        )[0]

# Bootstrap 1000 resamples for confidence intervals
# Display as 8x4 heatmap
```

**Cost**: Minutes on existing data. No new code infrastructure needed.

### 4.2 Non-Parametric Distribution Tests

**Question**: Does the distribution of child trait values match model
predictions, beyond the 7 PPC summary statistics?

**Method**: For each litter and trait, compute the fitted model's predicted
distribution over child trait values (already available via `trait_rows` in
`model.py`) and compare against the empirical distribution using
distribution-free tests.

**Specific tests**:
- Kolmogorov-Smirnov: sensitive to overall distributional shape
- Anderson-Darling: more sensitive to tail behavior
- Chi-squared goodness-of-fit: binned comparison, interpretable

Apply Benjamini-Hochberg FDR correction across 56 tests (14 litters x 4
traits).

**Extension -- joint distribution tests**: Compare the joint distribution of
(child_color, child_sweet) pairs using multivariate two-sample tests (energy
distance or maximum mean discrepancy). The current PPC checks marginals only.
Joint departures would indicate trait-trait coupling that the model misses.

**What this reveals**: Whether the fitted model is adequate
*distributionally*, not just on 7 summary statistics. Specific litter/trait
combinations that depart from predictions are targets for deeper
investigation.

**Cost**: Hours. Requires generating the predicted distribution from fitted
genes (straightforward extension of existing code).

### 4.3 Causal Discovery

**Question**: What is the dependency structure between parent and child
traits, without assuming CLAIM's causal graph?

**Method**: Apply constraint-based causal discovery (PC algorithm) or
score-based structure learning (GES with BIC scoring) to learn a causal DAG
from the observational data. Treat each parent's 4 traits and each child's
4 traits as 12 observed variables.

**Expected result under CLAIM**: The learned graph should show edges from
A_color -> child_color, B_color -> child_color (and similarly for other
traits), with no cross-trait edges.

**Caveats**: With 692 observations and 12 variables, statistical power is
limited. Conditional independence tests may fail to detect weak edges or
falsely remove real ones. Report power analysis alongside results.

**What unexpected edges would mean**: If the PC algorithm finds
A_color -> child_sweet (parent A's color influences child's sweetness), this
suggests either trait coupling, shared hidden genes, or a display rule error.

**Implementation**: Use `causal-learn` or `pgmpy` Python libraries.

**Cost**: Hours to days. Requires a new dependency but the analysis itself
is straightforward.

### 4.4 Bayesian Model Comparison

**Question**: How probable are different models given the data, accounting
for parameter uncertainty?

**Method**: Instead of point-estimate MLE, compute marginal likelihoods
(Bayesian evidence) for each model. This naturally penalizes model complexity
(Occam's razor) without needing cross-validation.

**Why this matters**: The cv_ll failure (INDEP wins on CLAIM-generated data)
shows that cross-validation is unreliable for this problem. Bayesian model
comparison provides an alternative that properly accounts for the hidden-gene
parameter space: models with more effective free parameters are automatically
penalized by the prior volume.

**Application**: For each model and litter, integrate the likelihood over all
possible hidden gene values with a uniform prior on [0, 1000] per gene.

Approaches by tractability:
1. **Laplace approximation**: Approximate the integral as a Gaussian around
   the MLE. Cheap but may be inaccurate for multi-modal likelihoods.
2. **Nested sampling** (e.g. `dynesty`, `ultranest`): Reliable marginal
   likelihood estimation. More expensive but handles multi-modality.
3. **Bridge sampling**: Efficient for comparing pairs of models.

**What this reveals**:
- Whether CLAIM's superiority survives proper Bayesian penalization
- Posterior distributions of hidden gene values (width = identifiability)
- Which hidden genes are well-determined vs poorly determined

**Cost**: Days to weeks for full nested sampling across 30 models x 14
litters. Laplace approximation: hours.

### 4.5 Active Experiment Design

**Question**: If you could breed more trees in-game, which crosses would be
most informative for distinguishing between models?

**Method**: Compute the expected information gain (KL divergence between
model predictions) for hypothetical new crosses. The cross where competing
models disagree most is the most informative experiment.

**High-value experiments**:

1. **Single-trait-extreme cross**: Choose parents that differ in exactly one
   trait (e.g. parent A has Color=200, parent B has Color=800, but identical
   Sweet/Size/Length). Under one-of-8 mutation, 7/8 children show no change
   in the matching traits. Under INDEP, all four traits have independent
   noise. Counting multi-trait changes on a controlled cross directly tests
   the mutation mechanism.

2. **Self-cross (identical parents)**: If both parents have the same
   observable traits, every child should look identical to the parents except
   for the one mutation. This isolates the nudge distribution shape and range
   from the inheritance mechanism. Histogram the single-trait deviations to
   empirically observe the nudge kernel.

3. **Boundary-value cross**: Choose parents with genes near 0 or 1000 (e.g.
   Sweet=5 implies both genes <= 5 under the min rule). Children from these
   parents probe the clamping vs wrapping vs reflecting behavior at the
   boundaries.

4. **High-N litter**: A single cross with 200+ children (achievable by
   repeated planting in-game) gives much stronger statistical power for all
   distribution tests. The current largest litter is 72 children.

5. **Controlled parent assignment**: Plant exactly 2 trees within the +/-19
   range of a new tree. This eliminates ambiguity about which trees are the
   parents. Record coordinates precisely.

**Cost**: Requires in-game time. Most experiments need 1-3 hours of planting
and recording. The payoff is new data that no amount of re-analysis of the
existing 692 children can provide.

### 4.6 Sensitivity Analysis

**Question**: Which model parameters matter most, and which are
observationally irrelevant?

**Method**: Systematically vary each parameter and measure the effect on
log-likelihood. Identify "stiff" directions (parameter changes that rapidly
degrade the fit) and "sloppy" directions (parameter changes the data cannot
detect).

**Specific analyses**:

1. **Fine nudge-range sweep**: Plot fit_ll as a function of R from 50 to 300
   in steps of 5. The current data tests R in {100, 125, 140, 150, 160, 175,
   200}. A finer grid reveals whether there is a sharp peak at R=150 or a
   broad plateau.

2. **Profile likelihoods for hidden genes**: For each litter, fix all genes
   except one and sweep that gene over [0, 1000]. Plot the profile
   likelihood. This visualizes which genes are well-identified (sharp peak)
   vs poorly identified (flat profile, only bounded). The README notes 68%
   exact recovery; the profiles would show *why* the other 32% are only
   bounded.

3. **Clone fraction profile**: For litters other than Hive1b, plot fit_ll as
   a function of clone fraction c. If the curve is flat, cloning is
   undetectable in that litter. If it peaks at c > 0, there may be a weak
   clone signal below the detection threshold.

4. **Sloppy parameter identification**: Use the Fisher information matrix
   (Hessian of log-likelihood at the MLE) to identify parameter combinations
   the data constrains vs combinations it does not. This is the formal
   version of asking "what can the data actually tell us?"

**Cost**: Hours. All analyses use existing fitting code with parameter
sweeps.

### 4.7 Anomaly and Outlier Analysis

**Question**: Are there specific children that all models struggle to
explain?

**Method**: For each of the 692 children, compute its per-child
log-likelihood under every model at its fitted genes. Rank children by their
worst-case (or average) score across all 30 models.

**What anomalous children mean**: A child that all models score poorly is the
most informative data point in the dataset. It either reveals a mechanic
outside the entire model family, or it is a data error (wrong parent
recorded, transcription mistake).

**Follow-up for each anomaly**:
- Which trait(s) are anomalous?
- What parent gene values would make the child probable?
- Is the child consistent with a different parent pair (parent
  misattribution)?
- Is it consistent with zero mutations (clone) or two mutations?
- Is it consistent with a larger nudge range than R=150?

**Concrete deliverable**: A ranked table of the 20 most anomalous children
with per-model log-likelihoods, the specific trait(s) causing the low score,
and proposed explanations.

**Cost**: Minutes. All per-child scores are already computed during fitting;
this is just a disaggregation and ranking step.

### 4.8 Model-Free Pattern Detection

**Question**: Are there patterns in the raw data that no model predicts?

**Analyses**:

1. **Child-parent residuals**: Compute delta_trait = child_trait -
   nearest_parent_trait for all 4 traits and all 692 children. "Nearest
   parent" means whichever parent's value is closer to the child's. Under
   CLAIM, the residual distribution should reflect the nudge kernel convolved
   with the hidden-gene uncertainty. Plot histograms and look for unexpected
   structure: bimodality, asymmetry, heavy tails, or discrete peaks.

2. **Sibling correlations**: Within each litter, compute pairwise
   correlations between siblings' trait values. Under CLAIM, siblings are
   independent given parents (no shared latent state beyond the parents'
   genes). Non-zero sibling correlation after conditioning on parents would
   indicate shared environmental effects or a non-independent random state.

3. **Trait change co-occurrence**: For each child, determine which traits
   changed visibly (child != both parents). Under one-of-8 mutation, at most
   one trait should change per child. The existing count (1 child with 2+
   changes) already supports this, but the *joint distribution* of which
   trait changed contains more information. Is the nudge equally likely to
   affect each trait? (Under one-of-8, probability proportional to 2/8 = 0.25
   per trait, since 2 of 8 genes belong to each trait.)

4. **Dimensionality reduction**: Project the 4D child trait vector into 2D
   via PCA or UMAP. Color by litter. Look for clusters or manifold structure
   that the model does not predict. Under CLAIM, children should scatter
   around their parents' display values with noise determined by the nudge
   kernel and hidden genes.

**Cost**: Hours. Standard statistical analyses on existing data.

### 4.9 Mixture Models

**Question**: What if the true mechanics are a mixture of different
processes?

**Method**: Fit a mixture model where each child is drawn from one of K
component models with learned mixture weights. Use the EM algorithm:

1. E-step: compute posterior probability that each child belongs to each
   component, given current parameters
2. M-step: refit each component's hidden genes using weighted children
3. Iterate until convergence

**Application**: Start with K=2 -- a CLAIM component and an INDEP component
with a learned mixture weight w. If w converges to ~100% CLAIM, the data
does not support a mixture. If it converges to 80% CLAIM / 20% INDEP, this
suggests heterogeneous mechanics.

**Per-litter mixtures**: The clone fraction in Hive1b (34% clones) already
demonstrates litter-level heterogeneity. A per-litter mixture model could
reveal whether different litters follow different mechanics or whether the
clone mechanism is the only source of heterogeneity.

**What this reveals**:
- Whether the data is homogeneous or contains subpopulations with different
  rules
- Per-child posterior assignments (which component each child most likely
  belongs to) -- these can be inspected for patterns

**Cost**: Days. Requires implementing the EM wrapper around the existing
fitting code.

### 4.10 Known Unknowns Framework

A structured inventory of what we know, what we know we do not know, and
strategies for discovering things we do not know we do not know.

**Known knowns** (high confidence, strong evidence):
- Species expression is nearest-neighbor in 4D trait space (confirmed)
- Display rules for Color, Sweet, Size are mean/min/max (600+ LL gap
  vs alternatives)
- One mutation per child, not independent per-gene (1 vs 97 multi-trait
  changes)
- At least 2 genes per trait (1-gene model is catastrophic)
- Nudge range is approximately 150 (+/-10 changes the fit by <20)

**Known unknowns** (identified gaps, testable):
- Exact nudge distribution shape (uniform vs triangular are close)
- Length display rule (g1 vs min/max indistinguishable by fit)
- Exact clone mechanism (only observable in Hive1b)
- Second gene value for many traits (bounded but not identified)
- Parent selection when multiple candidates exist within +/-19 range
- Whether mechanics vary between tales/patches

**Unknown unknowns** (what each method could discover):

| Method | Type of unknown-unknown it could detect |
|---|---|
| MI matrix (4.1) | Unexpected trait coupling, parent asymmetry |
| Distribution tests (4.2) | Systematic distributional departures |
| Causal discovery (4.3) | Unexpected causal structure |
| Bayesian comparison (4.4) | Proper complexity-penalized ranking |
| Active experiments (4.5) | Any mechanic distinguishable by new data |
| Sensitivity analysis (4.6) | Unidentifiable parameters, sloppy directions |
| Anomaly analysis (4.7) | Individual exceptions to all models |
| Sibling correlation (4.8) | Non-independence of children |
| Mixture models (4.9) | Heterogeneous mechanics across subpopulations |

---

## 5. Research Roadmap

Prioritized by effort vs expected information gain.

### Tier 1: Low Effort, High Value (hours, existing data)

Run these first. They require no new dependencies, no in-game work, and
produce results in minutes to hours.

1. **Mutual information matrix** (Section 4.1) -- verify the trait
   independence assumption. If off-diagonal entries are significant,
   everything downstream changes.
2. **Anomaly ranking** (Section 4.7) -- identify the 20 most informative
   children in the dataset. Manual inspection may immediately reveal
   recording errors or unexpected mechanics.
3. **Child-parent residual histograms** (Section 4.8) -- look for unexpected
   distributional shape in the raw data, independent of any model.
4. **Fine nudge-range sweep** (Section 4.6) -- plot fit_ll vs R from 50 to
   300 at high resolution to see whether R=150 is a sharp peak or part of a
   plateau.

### Tier 2: Moderate Effort, High Value (days, new code)

Run these after Tier 1 confirms (or does not) the basic structure.

5. **Formal distribution tests** (Section 4.2) -- KS/AD tests per
   litter/trait with FDR correction. Identifies specific departures.
6. **Profile likelihoods** (Section 4.6) -- visualize hidden-gene
   identifiability per litter. Reveals which fitted genes are trustworthy.
7. **2-component mixture model** (Section 4.9) -- test whether the data
   is mechanistically homogeneous.
8. **Multi-axis rival models** (Section 3.1 A7) -- test display rule
   combinations, not just single swaps.

### Tier 3: High Effort, Potentially Transformative (weeks)

These require significant development but could change the research
direction.

9. **Bayesian marginal likelihoods** (Section 4.4) -- proper model
   comparison with parameter uncertainty, resolving the cv_ll vs fit_ll
   tension.
10. **Causal structure learning** (Section 4.3) -- model-free dependency
    structure.
11. **Active experiment design** (Section 4.5) -- compute which in-game
    crosses would be most informative.

### Tier 4: In-Game Work

These require playing the game and collecting new data.

12. Execute the designed experiments from Tier 3 item 11.
13. Collect data from controlled crosses: identical parents (clone
    isolation), boundary-value parents (clamping test), high-N litters
    (statistical power).

---

## 6. Epistemological Notes

### 6.1 The Black-Box Problem

ATITD's game code is a deterministic algorithm. We observe only inputs
(parents) and outputs (children). We cannot inspect the code, set
breakpoints, or run controlled experiments in a test environment. This is
closer to studying a natural phenomenon than reverse-engineering software.

The key difference from natural science: physical phenomena follow
discoverable laws, but game code could be arbitrary. The game could use a
hash function, a lookup table, or contain bugs. The only constraint is that
the code produces the children we observe.

### 6.2 Model Comparison vs Model Discovery

The current approach excels at model comparison: given a finite candidate
set, which fits best? What it cannot do is model discovery: finding a model
that was not in the candidate set.

The alternative methods in Section 4 are designed to support model discovery
by providing model-free signals (MI matrix, distribution tests, anomaly
analysis) that could suggest entirely new hypotheses. The goal is to avoid
the failure mode of spending all effort refining a model that is wrong in a
way the refinement process cannot detect.

### 6.3 When to Stop

Proposed convergence criteria for the research program:

1. All Tier 1 analyses show no anomalies (or all anomalies are explained)
2. Bayesian model comparison confirms CLAIM with Bayes factor > 100 over all
   rivals
3. Designed in-game experiments confirm key predictions (nudge distribution,
   clone mechanism, boundary behavior)

Until all three conditions are met, the appropriate conclusion is: "The CLAIM
model is the best candidate tested, but not confirmed."
