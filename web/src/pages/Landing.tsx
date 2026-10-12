import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MetricCard } from "../components/MetricCard";
import {
  loadRunMeta,
  loadModelComparison,
  loadChildren,
  type RunMeta,
  type ModelComparison,
} from "../lib/data";

export function Landing() {
  const [meta, setMeta] = useState<RunMeta | null>(null);
  const [models, setModels] = useState<ModelComparison[]>([]);
  const [nChildren, setNChildren] = useState(0);

  useEffect(() => {
    loadRunMeta().then(setMeta).catch(() => {});
    loadModelComparison().then(setModels).catch(() => {});
    loadChildren().then((c) => setNChildren(c.length)).catch(() => {});
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
            cross-validation, we identify the CLAIM model as the overwhelmingly best explanation
            of 692 observed offspring across 14 independent litters.
          </p>
          <p>
            Seven complementary analyses (anomaly detection, residual diagnostics, mutual information,
            KS/AD goodness-of-fit tests, mixture decomposition, parameter sensitivity sweeps, and
            profile likelihoods) confirm the model's self-consistency and reveal no systematic
            failures. The methodology achieves a cross-validated log-likelihood advantage of
            &gt;1000 units over the next-best competitor, providing strong evidence for the
            coin-flip + uniform-mutation inheritance mechanism.
          </p>
        </div>
      </section>

    </div>
  );
}
