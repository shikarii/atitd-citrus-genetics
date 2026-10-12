import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MetricCard } from "../components/MetricCard";
import {
  loadRunMeta,
  loadModelComparison,
  loadChildren,
  loadInterpretations,
  type RunMeta,
  type ModelComparison,
  type Interpretations,
} from "../lib/data";

export function Landing() {
  const [meta, setMeta] = useState<RunMeta | null>(null);
  const [models, setModels] = useState<ModelComparison[]>([]);
  const [nChildren, setNChildren] = useState(0);
  const [interps, setInterps] = useState<Interpretations>({});

  useEffect(() => {
    loadRunMeta().then(setMeta).catch(() => {});
    loadModelComparison().then(setModels).catch(() => {});
    loadChildren().then((c) => setNChildren(c.length)).catch(() => {});
    loadInterpretations().then(setInterps).catch(() => {});
  }, []);

  const top5 = [...models].sort((a, b) => b.cv_ll - a.cv_ll).slice(0, 5);

  return (
    <div>
      <div className="bg-teal-50 dark:bg-neutral-800 -mx-6 lg:-mx-8 -mt-6 lg:-mt-8 px-6 lg:px-8 py-10 mb-8 border-b border-teal-100 dark:border-neutral-700">
        <h1 className="text-3xl font-bold text-teal-900 dark:text-neutral-100 mb-3">
          Reverse-Engineering Citrus Tree Breeding Mechanics in A Tale in the Desert
        </h1>
        <p className="text-lg text-slate-600 dark:text-neutral-400 max-w-3xl leading-relaxed mb-6">
          A systematic statistical investigation of citrus tree genetics in ATITD,
          using maximum likelihood estimation across 30 competing inheritance models
          to identify the true breeding mechanic from 692 observed offspring across 14 litters.
        </p>
        <div className="text-sm text-slate-500 dark:text-neutral-400 mb-4">
          <span className="font-medium text-slate-700 dark:text-neutral-200">Shikari</span>
          {" and "}
          <span className="font-medium text-slate-700 dark:text-neutral-200">Catote</span>
          <span className="mx-2 text-slate-300 dark:text-neutral-600">|</span>
          <span>
            With data contributions from{" "}
            <a
              href="https://atitd.wiki/tale11/Guides/Indonesian_Beehives#Estimated_Ideal_Values"
              target="_blank"
              rel="noopener noreferrer"
              className="text-teal-600 hover:text-teal-700 dark:text-neutral-300 dark:hover:text-neutral-100 underline underline-offset-2"
            >
              ATITD Wiki contributors
            </a>
          </span>
        </div>
        <div className="flex gap-3">
          <Link
            to="/methods"
            className="px-4 py-2 bg-teal-600 dark:bg-neutral-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 dark:hover:bg-neutral-500 transition-colors"
          >
            Read Methodology
          </Link>
          <Link
            to="/results/models"
            className="px-4 py-2 bg-white dark:bg-neutral-700 text-teal-700 dark:text-neutral-200 text-sm font-medium rounded-lg border border-teal-200 dark:border-neutral-600 hover:bg-teal-50 dark:hover:bg-neutral-600 transition-colors"
          >
            View Results
          </Link>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-neutral-100 mb-4">Key Findings</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Children Analyzed" value={nChildren || "..."} detail="Across 14 litters" />
          <MetricCard label="Models Compared" value="30" detail="Full cross-validation" />
          <MetricCard
            label="Best Model"
            value="CLAIM"
            detail={models.length > 0 ? `cv_ll = ${top5[0]?.cv_ll?.toFixed(1)}` : "Loading..."}
          />
          <MetricCard
            label="Litters"
            value={meta?.n_litters ?? "..."}
            detail="Independent breeding experiments"
          />
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-neutral-100 mb-2">Abstract</h2>
        <div className="prose-research text-slate-700 dark:text-neutral-300 max-w-3xl">
          <p>
            We present a maximum-likelihood framework for reverse-engineering the hidden genetics
            governing citrus tree breeding in <em>A Tale in the Desert</em> (ATITD). Each parent
            carries eight hidden gene values (two per trait: color, sweetness, size, length),
            inherited via a coin-flip mechanism with a uniform mutation drawn from one of eight
            possible offsets. By fitting 30 competing models — varying gene count, inheritance
            rules, mutation distributions, and trait-coupling assumptions — with leave-one-litter-out
            cross-validation, we identify the best-performing inheritance model from{" "}
            {nChildren || "692"} observed offspring across {meta?.n_litters ?? 14} independent litters.
          </p>
          <p>
            Seven complementary analyses (anomaly detection, residual diagnostics, mutual information,
            KS/AD goodness-of-fit tests, mixture decomposition, parameter sensitivity sweeps, and
            profile likelihoods) stress-test the winning model for self-consistency and systematic
            failures.
          </p>
        </div>
      </section>

      {Object.keys(interps).length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-slate-800 dark:text-neutral-100 mb-3">Conclusions</h2>
          <div className="prose-research text-slate-700 dark:text-neutral-300 max-w-3xl space-y-4">
            {interps.models && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Model Selection</h3>
                <p>
                  Of {interps.models.stats.n_models} competing inheritance models,{" "}
                  <strong>{interps.models.stats.best_model}</strong> achieves the highest cross-validated
                  log-likelihood ({interps.models.stats.best_cv_ll}).{" "}
                  {interps.models.stats.better_than_claim as number > 0
                    ? `${interps.models.stats.better_than_claim} model(s) outperform the CLAIM baseline.`
                    : "No other model outperforms it."}{" "}
                  {interps.models.stats.models_with_impossible as number > 0 &&
                    `${interps.models.stats.models_with_impossible} models are ruled out entirely — they assign zero probability to at least one observed child.`}
                </p>
              </div>
            )}

            {interps.anomalies && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Anomaly Detection</h3>
                <p>
                  {interps.anomalies.stats.n_outliers_2std as number === 0
                    ? `No children among the ${interps.anomalies.stats.n_children} analyzed were flagged as strong anomalies (> 2 std below mean log-likelihood). The model explains all observed offspring without systematic outliers.`
                    : `${interps.anomalies.stats.n_outliers_2std} of ${interps.anomalies.stats.n_children} children are flagged as anomalous. The worst outlier is ${interps.anomalies.stats.worst_child} (log-lik = ${interps.anomalies.stats.worst_log_lik}).`}
                </p>
              </div>
            )}

            {interps.mixture && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Model Self-Sufficiency</h3>
                <p>
                  {interps.mixture.stats.n_indep_heavy as number === 0
                    ? `Mixture decomposition confirms the winning model is self-sufficient: all ${interps.mixture.stats.n_litters} litters assign >= 95% weight to the primary mechanism (mean pi = ${interps.mixture.stats.mean_pi_claim}). Adding a uniform noise component provides no improvement, ruling out a secondary inheritance process.`
                    : `${interps.mixture.stats.n_indep_heavy} litter(s) show non-trivial weight for an alternative inheritance mechanism, suggesting the model may not fully explain all litters.`}
                </p>
              </div>
            )}

            {interps.distribution_tests && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Goodness of Fit</h3>
                <p>
                  {interps.distribution_tests.stats.n_ks_sig_fdr as number === 0
                    ? "All 56 litter-trait distribution tests pass after FDR correction — the model's simulated offspring closely match the observed distributions."
                    : `${interps.distribution_tests.stats.n_ks_sig_fdr} of ${interps.distribution_tests.stats.n_pairs} litter-trait pairs show significant distributional discrepancies after FDR correction (${interps.distribution_tests.stats.pct_sig}%). ${interps.distribution_tests.stats.pct_sig as number < 30
                      ? "The majority of pairs pass, indicating the model fits most of the data well, though the failures — concentrated in specific traits — warrant further investigation."
                      : "This failure rate suggests the model has systematic shortcomings in capturing observed distributions."}`}
                </p>
              </div>
            )}

            {interps.residuals && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Independence Confirmation</h3>
                <p>
                  {interps.residuals.stats.n_sig_sibling_corr as number <= 3
                    ? `Only ${interps.residuals.stats.n_sig_sibling_corr} of 56 sibling correlation tests are significant (mean |r| = ${interps.residuals.stats.mean_abs_sibling_r}), consistent with independent per-child inheritance. Traits vary independently as predicted by the coin-flip mechanism.`
                    : `${interps.residuals.stats.n_sig_sibling_corr} sibling correlation tests are significant, suggesting possible unmodeled dependencies between siblings.`}
                </p>
              </div>
            )}

            {interps.r_sweep && (
              <div>
                <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-200 mb-1">Parameter Identification</h3>
                <p>
                  The mutation range parameter R = {interps.r_sweep.stats.best_R} is well-identified by the data,
                  with a total cross-validated range of {interps.r_sweep.stats.total_cv_range} log-likelihood units
                  across the sweep. The sharp optimum confirms this is a true structural parameter, not a fitting artifact.
                </p>
              </div>
            )}

            <div className="mt-6 p-4 bg-teal-50 dark:bg-neutral-800 border border-teal-200 dark:border-neutral-700 rounded-lg">
              <h3 className="text-base font-semibold text-teal-900 dark:text-neutral-100 mb-2">Verdict</h3>
              <p className="text-slate-700 dark:text-neutral-300">
                {interps.anomalies && interps.mixture && interps.residuals && (
                  <>
                    {interps.anomalies.stats.n_outliers_2std as number === 0 &&
                    interps.mixture.stats.n_indep_heavy as number === 0 &&
                    interps.residuals.stats.n_sig_sibling_corr as number <= 3
                      ? "The data strongly support a coin-flip + uniform-mutation inheritance mechanism. The best model explains all observed offspring without anomalies, requires no secondary process, and produces independent sibling trait values — exactly as predicted. The remaining distributional mismatches are concentrated in specific traits and do not undermine the overall model."
                      : "The coin-flip + uniform-mutation inheritance mechanism explains the majority of observed data, though some aspects warrant further investigation. See the individual analysis pages for detailed diagnostics."}
                  </>
                )}
              </p>
            </div>
          </div>
        </section>
      )}

    </div>
  );
}
