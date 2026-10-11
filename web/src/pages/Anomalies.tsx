import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { loadAnomalyScores, type AnomalyScore, TRAITS } from "../lib/data";
import { CHART_COLORS } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<AnomalyScore, unknown>[] = [
  { accessorKey: "rank", header: "Rank" },
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "child_num", header: "Child #" },
  {
    accessorKey: "log_lik",
    header: "Log-Likelihood",
    cell: (info) => (info.getValue() as number).toFixed(3),
  },
  ...TRAITS.map(
    (t) =>
      ({
        accessorKey: t,
        header: t,
        cell: (info) => info.getValue() as number,
      }) as ColumnDef<AnomalyScore, unknown>,
  ),
];

export function Anomalies() {
  const [data, setData] = useState<AnomalyScore[]>([]);

  useEffect(() => {
    loadAnomalyScores().then(setData).catch(() => {});
  }, []);

  const sorted = [...data].sort((a, b) => a.log_lik - b.log_lik);
  const worst10 = sorted.slice(0, 10);
  const nBelowMinus5 = data.filter((d) => d.log_lik < -5).length;
  const meanLL = data.length > 0
    ? (data.reduce((s, d) => s + d.log_lik, 0) / data.length)
    : 0;

  const litters = [...new Set(data.map((d) => d.litter))].sort();

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Per-Child Anomaly Scores</h1>
      <p className="text-sm text-slate-500 mb-6">
        Each child's log-likelihood under the CLAIM model with MLE-fitted genes.
        Lower values indicate children that are harder for the model to explain.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Children" value={data.length || "..."} />
        <MetricCard label="Mean Log-Lik" value={meanLL.toFixed(2)} />
        <MetricCard label="Worst Log-Lik" value={sorted[0]?.log_lik?.toFixed(2) ?? "..."} detail={sorted[0] ? `${sorted[0].litter} #${sorted[0].child_num}` : ""} />
        <MetricCard label="Children with LL < -5" value={nBelowMinus5} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Log-Likelihood Distribution by Litter"
          subtitle="Box plots showing per-child log-likelihood spread"
        >
          <PlotlyChart
            data={litters.map((litter, i) => ({
              y: data.filter((d) => d.litter === litter).map((d) => d.log_lik),
              type: "box" as const,
              name: litter,
              boxpoints: "outliers" as const,
              marker: { color: CHART_COLORS[i % CHART_COLORS.length] },
            }))}
            layout={{
              height: 450,
              yaxis: { title: { text: "Log-Likelihood" } },
              showlegend: false,
            }}
          />
        </ChartCard>

        <ChartCard
          title="Ranked Anomaly Scores (All Children)"
          subtitle="Children sorted by log-likelihood; hover for details"
        >
          <PlotlyChart
            data={[
              {
                x: sorted.map((_, i) => i + 1),
                y: sorted.map((d) => d.log_lik),
                text: sorted.map((d) => `${d.litter} #${d.child_num}`),
                mode: "markers" as const,
                type: "scatter",
                marker: {
                  size: 4,
                  color: sorted.map((d) => (d.log_lik < -5 ? "#EF4444" : "#0D9488")),
                },
                hovertemplate: "%{text}<br>LL: %{y:.3f}<extra></extra>",
              },
            ]}
            layout={{
              height: 400,
              xaxis: { title: { text: "Rank" } },
              yaxis: { title: { text: "Log-Likelihood" } },
              shapes: [
                { type: "line", y0: -5, y1: -5, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#EF4444", width: 1 } },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Top 10 Most Anomalous Children</h2>
          <DataTable
            data={worst10 as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename="anomaly_scores.csv"
          />
        </div>
      </div>
    </div>
  );
}
