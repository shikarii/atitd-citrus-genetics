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
    void loadRunMeta().then(setMeta).catch(() => undefined);
    void loadModelComparison().then(setModels).catch(() => undefined);
    void loadChildren().then((c) => { setNChildren(c.length); }).catch(() => undefined);
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const top5 = [...models].sort((a, b) => b.cv_ll - a.cv_ll).slice(0, 5);

  return (
    <div>
      <div className="bg-teal-50 dark:bg-neutral-800 -mx-3 sm:-mx-4 md:-mx-6 lg:-mx-8 -mt-3 sm:-mt-4 md:-mt-6 lg:-mt-8 px-3 sm:px-4 md:px-6 lg:px-8 py-8 sm:py-10 mb-8 border-b border-teal-100 dark:border-neutral-700">
        <h1 className="text-2xl sm:text-3xl font-bold text-teal-900 dark:text-neutral-100 mb-3">
          Reverse-Engineering Citrus Tree Breeding Mechanics in A Tale in the Desert
        </h1>
        <p className="text-base sm:text-lg text-slate-600 dark:text-neutral-400 max-w-3xl leading-relaxed mb-6">
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
            className="px-4 py-2.5 min-h-[44px] flex items-center bg-teal-600 dark:bg-neutral-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 dark:hover:bg-neutral-500 transition-colors"
          >
            Read Methodology
          </Link>
          <Link
            to="/results/models"
            className="px-4 py-2.5 min-h-[44px] flex items-center bg-white dark:bg-neutral-700 text-teal-700 dark:text-neutral-200 text-sm font-medium rounded-lg border border-teal-200 dark:border-neutral-600 hover:bg-teal-50 dark:hover:bg-neutral-600 transition-colors"
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
            detail={models.length > 0 ? `cv_ll = ${top5[0]?.cv_ll.toFixed(1)}` : "Loading..."}
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
        <div className="prose-research text-slate-700 dark:text-neutral-300 max-w-3xl space-y-4">
          <p>
            We present a maximum-likelihood framework for reverse-engineering the hidden genetics
            governing citrus tree breeding in <em>A Tale in the Desert</em> (ATITD). Each parent
            carries eight hidden gene values (two per trait: color, sweetness, size, length),
            inherited via a coin-flip mechanism with a uniform mutation drawn from one of eight
            possible offsets. By fitting {interps.models ? String(interps.models.stats.n_models) : "30"} competing
            models — varying gene count, inheritance rules, mutation distributions, and trait-coupling
            assumptions — with leave-one-litter-out cross-validation, we identify the best-performing
            inheritance model from {nChildren || "692"} observed offspring
            across {meta?.n_litters ?? 14} independent litters.
          </p>
          <p>
            Seven complementary analyses (anomaly detection, residual diagnostics, mutual information,
            KS/AD goodness-of-fit tests, mixture decomposition, parameter sensitivity sweeps, and
            profile likelihoods) stress-test the winning model for self-consistency and systematic
            failures.
          </p>

          {Object.keys(interps).length > 0 && (
            <p>
              {interps.models && (
                <>
                  Among the {interps.models.stats.n_models} models evaluated,{" "}
                  <strong>{String(interps.models.stats.best_model)}</strong> achieves the highest
                  cross-validated log-likelihood (cv_ll&nbsp;=&nbsp;{String(interps.models.stats.best_cv_ll)}),
                  with {String(interps.models.stats.models_with_impossible)} models
                  ruled out entirely for assigning zero probability to observed offspring.{" "}
                </>
              )}
              {interps.anomalies && (interps.anomalies.stats.n_outliers_2std as number) === 0 && (
                <>
                  No children among the {String(interps.anomalies.stats.n_children)} analyzed
                  were flagged as anomalous under the winning model.{" "}
                </>
              )}
              {interps.mixture && (interps.mixture.stats.n_indep_heavy as number) === 0 && (
                <>
                  Mixture decomposition confirms the model is self-sufficient across
                  all {String(interps.mixture.stats.n_litters)} litters (mean
                  CLAIM weight pi&nbsp;=&nbsp;{String(interps.mixture.stats.mean_pi_claim)}).{" "}
                </>
              )}
              {interps.residuals && (
                <>
                  Only {String(interps.residuals.stats.n_sig_sibling_corr)} of 56 sibling
                  correlation tests reach significance (mean |r|&nbsp;=&nbsp;{String(interps.residuals.stats.mean_abs_sibling_r)}),
                  consistent with independent per-child inheritance.{" "}
                </>
              )}
              {interps.distribution_tests && (interps.distribution_tests.stats.n_ks_sig_fdr as number) > 0 && (
                <>
                  {String(interps.distribution_tests.stats.n_ks_sig_fdr)} of{" "}
                  {String(interps.distribution_tests.stats.n_pairs)} litter-trait distribution tests
                  show significant discrepancies after FDR correction ({String(interps.distribution_tests.stats.pct_sig)}%),
                  concentrated in specific traits.{" "}
                </>
              )}
              {interps.r_sweep && (
                <>
                  The mutation range parameter R&nbsp;=&nbsp;{String(interps.r_sweep.stats.best_R)} is
                  well-identified, with {String(interps.r_sweep.stats.total_cv_range)} log-likelihood
                  units of discriminating power across the sweep.
                </>
              )}
            </p>
          )}
        </div>
      </section>

      {interps.anomalies && interps.mixture && interps.residuals && (
        <section className="mb-8">
          <div className="p-5 bg-teal-50 dark:bg-neutral-800 border border-teal-200 dark:border-neutral-700 rounded-lg max-w-3xl">
            <h2 className="text-lg font-semibold text-teal-900 dark:text-neutral-100 mb-2">Verdict</h2>
            <p className="text-slate-700 dark:text-neutral-300 leading-relaxed">
              {(interps.anomalies.stats.n_outliers_2std as number) === 0 &&
              (interps.mixture.stats.n_indep_heavy as number) === 0 &&
              (interps.residuals.stats.n_sig_sibling_corr as number) <= 3
                ? "The data strongly support a coin-flip + uniform-mutation inheritance mechanism. The best model explains all observed offspring without anomalies, requires no secondary process, and produces independent sibling trait values — exactly as predicted. The remaining distributional mismatches are concentrated in specific traits and do not undermine the overall model."
                : "The coin-flip + uniform-mutation inheritance mechanism explains the majority of observed data, though some aspects warrant further investigation. See the individual analysis pages for detailed diagnostics."}
            </p>
          </div>
        </section>
      )}

    </div>
  );
}
