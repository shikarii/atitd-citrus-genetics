import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadModelComparison, type ModelComparison } from "../lib/data";
import { CHART_COLORS } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<ModelComparison, unknown>[] = [
  { accessorKey: "model", header: "Model" },
  {
    accessorKey: "fit_ll",
    header: "Fit LL",
    cell: (info) => (info.getValue() as number).toFixed(1),
  },
  {
    accessorKey: "cv_ll",
    header: "CV LL",
    cell: (info) => (info.getValue() as number).toFixed(1),
  },
  { accessorKey: "children_impossible", header: "Impossible Children" },
];

export function Models() {
  const [data, setData] = useState<ModelComparison[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModelComparison()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Models Tested" value={data.length || "..."} />
        <MetricCard label="Best Model" value={best?.model ?? "..."} detail={`cv_ll = ${best?.cv_ll?.toFixed(1) ?? "..."}`} />
        <MetricCard label="CV LL Gap (1st - 2nd)" value={gap} detail="Log-likelihood units" />
        <MetricCard label="Models with Impossible Children" value={nImpossible} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Cross-Validated Log-Likelihood Leaderboard"
          subtitle="Models sorted by CV LL; higher is better"
        >
          <PlotlyChart
            data={[
              {
                x: sorted.map((m) => m.model),
                y: sorted.map((m) => m.cv_ll),
                type: "bar",
                marker: {
                  color: sorted.map((m) =>
                    m.children_impossible > 0 ? "#EF4444" : CHART_COLORS[0],
                  ),
                },
                text: sorted.map((m) => m.cv_ll.toFixed(0)),
                textposition: "outside" as const,
              },
            ]}
            layout={{
              height: 500,
              xaxis: { title: { text: "Model" }, tickangle: -45 },
              yaxis: { title: { text: "CV Log-Likelihood" } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="Fit vs Cross-Validated Log-Likelihood"
          subtitle="Points above the diagonal indicate overfitting"
        >
          <PlotlyChart
            data={[
              {
                x: data.map((m) => m.fit_ll),
                y: data.map((m) => m.cv_ll),
                text: data.map((m) => m.model),
                mode: "text+markers" as const,
                type: "scatter",
                textposition: "top right" as const,
                textfont: { size: 9 },
                marker: {
                  size: 10,
                  color: data.map((m) =>
                    m.children_impossible > 0 ? "#EF4444" : CHART_COLORS[0],
                  ),
                },
              },
            ]}
            layout={{
              height: 500,
              xaxis: { title: { text: "Fit Log-Likelihood (full data)" } },
              yaxis: { title: { text: "CV Log-Likelihood (leave-one-out)" } },
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">All Models</h2>
          <DataTable
            data={sorted as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename="model_comparison.csv"
          />
        </div>
      </div>
    </div>
  );
}
