import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import {
  loadRunMeta,
  loadModelComparison,
  loadChildren,
  type RunMeta,
  type ModelComparison,
  type Child,
  TRAITS,
} from "../lib/data";
import { CHART_COLORS, TEAL, SLATE } from "../lib/colors";

function pearsonR(xs: number[], ys: number[]): number {
  const n = xs.length;
  if (n < 2) return 0;
  const mx = xs.reduce((a, b) => a + b, 0) / n;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0, dx2 = 0, dy2 = 0;
  for (let i = 0; i < n; i++) {
    const dx = xs[i]! - mx, dy = ys[i]! - my;
    num += dx * dy;
    dx2 += dx * dx;
    dy2 += dy * dy;
  }
  const denom = Math.sqrt(dx2 * dy2);
  return denom === 0 ? 0 : num / denom;
}

export function Landing() {
  const [meta, setMeta] = useState<RunMeta | null>(null);
  const [models, setModels] = useState<ModelComparison[]>([]);
  const [children, setChildren] = useState<Child[]>([]);

  useEffect(() => {
    loadRunMeta().then(setMeta).catch(() => {});
    loadModelComparison().then(setModels).catch(() => {});
    loadChildren().then(setChildren).catch(() => {});
  }, []);

  const nChildren = children.length;

  const top5 = [...models].sort((a, b) => b.cv_ll - a.cv_ll).slice(0, 5);

  return (
    <div>
      <div className="bg-teal-50 -mx-6 lg:-mx-8 -mt-6 lg:-mt-8 px-6 lg:px-8 py-10 mb-8 border-b border-teal-100">
        <h1 className="text-3xl font-bold text-teal-900 mb-3">
          Reverse-Engineering Citrus Tree Breeding Mechanics in A Tale in the Desert
        </h1>
        <p className="text-lg text-slate-600 max-w-3xl leading-relaxed mb-6">
          A systematic statistical investigation of citrus tree genetics in ATITD,
          using maximum likelihood estimation across 30 competing inheritance models
          to identify the true breeding mechanic from 692 observed offspring across 14 litters.
        </p>
        <div className="flex gap-3">
          <Link
            to="/methods"
            className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-colors"
          >
            Read Methodology
          </Link>
          <Link
            to="/results/models"
            className="px-4 py-2 bg-white text-teal-700 text-sm font-medium rounded-lg border border-teal-200 hover:bg-teal-50 transition-colors"
          >
            View Results
          </Link>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-800 mb-4">Key Findings</h2>
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
        <h2 className="text-xl font-semibold text-slate-800 mb-2">Abstract</h2>
        <div className="prose-research text-slate-700 max-w-3xl">
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

      {top5.length > 0 && (
        <section className="mb-8">
          <ChartCard
            title="Top 5 Models by Cross-Validated Log-Likelihood"
            subtitle="Leave-one-litter-out CV; higher is better"
          >
            <PlotlyChart
              data={[
                {
                  x: top5.map((m) => m.model),
                  y: top5.map((m) => m.cv_ll),
                  type: "bar",
                  marker: {
                    color: top5.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
                    line: { color: "rgba(0,0,0,0.1)", width: 0.5 },
                  },
                  text: top5.map((m) => m.cv_ll.toFixed(1)),
                  textposition: "outside" as const,
                  textfont: { size: 11, color: SLATE[500] },
                  hovertemplate: "<b>%{x}</b><br>CV LL: %{y:.1f}<extra></extra>",
                },
              ]}
              layout={{
                height: 380,
                xaxis: {
                  title: { text: "Model Specification", standoff: 15 },
                  tickangle: -25,
                },
                yaxis: {
                  title: { text: "Cross-Validated Log-Likelihood", standoff: 10 },
                },
                bargap: 0.3,
              }}
            />
          </ChartCard>
        </section>
      )}

      {children.length > 0 && (
        <section className="mb-8">
          <ChartCard
            title="Trait Correlation Matrix"
            subtitle="Pearson correlation between child trait values across all 692 offspring. Low correlations confirm trait independence."
          >
            <PlotlyChart
              data={(() => {
                const labels = TRAITS.map((t) => t.charAt(0).toUpperCase() + t.slice(1));
                const z = TRAITS.map((t1) => {
                  const v1 = children.map((c) => c[t1 as keyof Child] as number);
                  return TRAITS.map((t2) => {
                    const v2 = children.map((c) => c[t2 as keyof Child] as number);
                    return parseFloat(pearsonR(v1, v2).toFixed(3));
                  });
                });
                return [{
                  z,
                  x: labels,
                  y: labels,
                  type: "heatmap",
                  colorscale: [
                    [0, TEAL[100]],
                    [0.5, "white"],
                    [1, TEAL[700]],
                  ],
                  zmin: -1,
                  zmax: 1,
                  text: z.map((row) => row.map((v) => v.toFixed(3))) as unknown as string[],
                  texttemplate: "%{text}",
                  textfont: { size: 13, color: SLATE[800] },
                  hovertemplate: "<b>%{y}</b> vs <b>%{x}</b><br>r = %{z:.3f}<extra></extra>",
                  colorbar: {
                    title: { text: "Pearson r", side: "right" },
                    tickfont: { size: 10 },
                  },
                }];
              })()}
              layout={{
                height: 400,
                xaxis: { tickfont: { size: 13 } },
                yaxis: { tickfont: { size: 13 }, autorange: "reversed" },
              }}
            />
          </ChartCard>
        </section>
      )}
    </div>
  );
}
