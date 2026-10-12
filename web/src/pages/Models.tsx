import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadModelComparison, loadInterpretations, type ModelComparison, type Interpretations } from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { TEAL, ACCENT, SLATE } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<ModelComparison>[] = [
  { accessorKey: "model", header: "Model" },
  {
    accessorKey: "fit_ll",
    header: "Fit LL",
    cell: (info) => info.getValue<number>().toFixed(1),
  },
  {
    accessorKey: "cv_ll",
    header: "CV LL",
    cell: (info) => info.getValue<number>().toFixed(1),
  },
  { accessorKey: "children_impossible", header: "Impossible Children" },
];

export function Models() {
  const [data, setData] = useState<ModelComparison[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModelComparison()
      .then(setData)
      .catch(() => undefined)
      .finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const sorted = [...data].sort((a, b) => b.cv_ll - a.cv_ll);
  const best = sorted[0];
  const second = sorted[1];
  const gap = best && second ? (best.cv_ll - second.cv_ll).toFixed(1) : "...";
  const nImpossible = data.filter((m) => m.children_impossible > 0).length;

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">30-Model Comparison</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">30-Model Comparison</h1>
      <p className="text-sm text-slate-500 mb-6">
        Leave-one-litter-out cross-validated log-likelihood across 30 inheritance models
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          The central question of this study is: <em>which inheritance model best explains observed citrus offspring?</em>{" "}
          We evaluate 30 competing models that differ in gene count, inheritance rules, mutation distributions,
          and trait-coupling assumptions. Each model is scored using leave-one-litter-out cross-validation (LOLOCV),
          where all 13 litters are used for fitting and the held-out litter is used for evaluation. This prevents
          overfitting and ensures the winning model generalizes to unseen breeding experiments. A higher CV log-likelihood
          indicates the model assigns higher probability to offspring it has never seen during training.
        </p>
      </div>

      <FindingsSummary interpretation={interps.models} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Models Tested" value={data.length || "..."} />
        <MetricCard label="Best Model" value={best?.model ?? "..."} detail={`cv_ll = ${best?.cv_ll.toFixed(1) ?? "..."}`} />
        <MetricCard label="CV LL Gap (1st - 2nd)" value={gap} detail="Log-likelihood units" />
        <MetricCard label="Models with Impossible Children" value={nImpossible} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Cross-Validated Log-Likelihood Leaderboard"
          subtitle="Models sorted by CV LL; higher is better. Red bars indicate models with impossible children."
          description="Each bar represents one model's total cross-validated log-likelihood across all held-out litters. Models are ranked left-to-right from best to worst. A model that assigns zero probability to any observed child (impossible children) is highlighted in red — these models are fundamentally incompatible with the data regardless of their aggregate score."
        >
          <PlotlyChart
            data={[
              {
                x: sorted.map((m) => m.model),
                y: sorted.map((m) => m.cv_ll),
                type: "bar",
                marker: {
                  color: sorted.map((m) =>
                    m.children_impossible > 0 ? ACCENT.coral : TEAL[600],
                  ),
                  line: { color: "rgba(0,0,0,0.08)", width: 0.5 },
                },
                text: sorted.map((m) => m.cv_ll.toFixed(0)),
                textposition: "outside" as const,
                textfont: { size: 10, color: SLATE[500] },
                hovertemplate: "<b>%{x}</b><br>CV LL: %{y:.1f}<br>Rank: %{pointNumber}<extra></extra>",
              },
            ]}
            layout={{
              height: 520,
              xaxis: {
                title: { text: "Model Specification", standoff: 20 },
                tickangle: -45,
                tickfont: { size: 10 },
              },
              yaxis: {
                title: { text: "Cross-Validated Log-Likelihood", standoff: 10 },
              },
              bargap: 0.25,
            }}
          />
        </ChartCard>

        <ChartCard
          title="In-Sample Fit vs Cross-Validation Performance"
          subtitle="Dashed line: y = x. Points below the line overfit to training data."
          description="This scatter plot tests for overfitting. The x-axis is how well each model fits its training data; the y-axis is how well it predicts held-out data. Models near the dashed y=x line generalize well. Models far below the line have high in-sample fit but poor generalization — a hallmark of overfitting due to excessive free parameters. The best model should be both high on the y-axis and close to the diagonal."
        >
          <PlotlyChart
            data={[
              {
                x: data.map((m) => m.fit_ll),
                y: data.map((m) => m.cv_ll),
                text: data.map((m) => m.model),
                mode: "markers" as const,
                type: "scatter",
                marker: {
                  size: 10,
                  color: data.map((m) =>
                    m.children_impossible > 0 ? ACCENT.coral : TEAL[600],
                  ),
                  line: { color: "white", width: 1.5 },
                  opacity: 0.85,
                },
                hovertemplate: "<b>%{text}</b><br>Fit LL: %{x:.1f}<br>CV LL: %{y:.1f}<extra></extra>",
              },
              // y=x reference line
              {
                x: [Math.min(...data.map((m) => m.fit_ll)) - 200, Math.max(...data.map((m) => m.fit_ll)) + 200],
                y: [Math.min(...data.map((m) => m.fit_ll)) - 200, Math.max(...data.map((m) => m.fit_ll)) + 200],
                mode: "lines" as const,
                type: "scatter",
                line: { color: SLATE[300], dash: "dash", width: 1 },
                showlegend: false,
                hoverinfo: "skip" as const,
              },
            ]}
            layout={{
              height: 520,
              xaxis: { title: { text: "In-Sample Log-Likelihood (fit_ll)", standoff: 10 } },
              yaxis: { title: { text: "Cross-Validated Log-Likelihood (cv_ll)", standoff: 10 } },
              annotations: data.length > 0 ? sorted.slice(0, 5).map((m) => ({
                x: m.fit_ll,
                y: m.cv_ll,
                text: m.model,
                showarrow: true,
                arrowhead: 0,
                arrowcolor: SLATE[400],
                ax: 30,
                ay: -20,
                font: { size: 10, color: SLATE[700] },
                bgcolor: "rgba(255,255,255,0.85)",
                borderpad: 2,
              })) : [],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Full Model Comparison Table</h2>
          <DataTable
            data={sorted}
            columns={columns as ColumnDef<Record<string, unknown>>[]}
            downloadFilename="model_comparison.csv"
          />
        </div>
      </div>
    </div>
  );
}
