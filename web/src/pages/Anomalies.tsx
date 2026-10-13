import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadAnomalyScores, loadInterpretations, type AnomalyScore, type Interpretations, TRAITS } from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { CHART_COLORS, TEAL, ACCENT } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";
import { useResponsiveChartHeight } from "../lib/responsive";

const columns: ColumnDef<AnomalyScore>[] = [
  { accessorKey: "rank", header: "Rank" },
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "child_num", header: "Child #" },
  {
    accessorKey: "log_lik",
    header: "Log-Likelihood",
    cell: (info) => info.getValue<number>().toFixed(3),
  },
  ...TRAITS.map(
    (t): ColumnDef<AnomalyScore> =>
      ({
        accessorKey: t,
        header: t,
        cell: (info) => info.getValue<number>(),
      }),
  ),
];

export function Anomalies() {
  const [data, setData] = useState<AnomalyScore[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);
  const h480 = useResponsiveChartHeight(480);
  const h420 = useResponsiveChartHeight(420);

  useEffect(() => {
    loadAnomalyScores()
      .then(setData)
      .catch(() => undefined)
      .finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const sorted = [...data].sort((a, b) => a.log_lik - b.log_lik);
  const worst10 = sorted.slice(0, 10);
  const nBelowMinus5 = data.filter((d) => d.log_lik < -5).length;
  const meanLL = data.length > 0
    ? (data.reduce((s, d) => s + d.log_lik, 0) / data.length)
    : 0;

  const litters = [...new Set(data.map((d) => d.litter))].sort();

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Per-Child Anomaly Scores</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Per-Child Anomaly Scores</h1>
      <p className="text-sm text-slate-500 mb-6">
        Each child's log-likelihood under the CLAIM model with MLE-fitted genes.
        Lower values indicate children that are harder for the model to explain.
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          Even a correct model will assign low probability to some children by chance — but a
          pattern of extreme outliers would suggest systematic model failure or data errors.
          We compute each child's individual log-likelihood under CLAIM with MLE-fitted parent genes.
          Children with very low scores (LL &lt; -5) are flagged as anomalous. If these concentrate
          in specific litters or show trait-specific patterns, it may indicate an unmodeled game mechanic
          or data entry error rather than random variation.
        </p>
      </div>

      <FindingsSummary interpretation={interps.anomalies} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Children" value={data.length || "..."} />
        <MetricCard label="Mean Log-Lik" value={meanLL.toFixed(2)} />
        <MetricCard label="Worst Log-Lik" value={sorted[0]?.log_lik.toFixed(2) ?? "..."} detail={sorted[0] ? `${sorted[0].litter} #${sorted[0].child_num}` : ""} />
        <MetricCard label="Children with LL < -5" value={nBelowMinus5} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Log-Likelihood Distribution by Litter"
          subtitle="Box plots showing per-child log-likelihood spread across litters"
          description="Each box summarizes the distribution of per-child log-likelihoods within a single litter. Litters with consistently high medians are well-explained by CLAIM. Litters with low medians or many outliers may contain children that violate model assumptions — for example, offspring from a different breeding mechanic or with recording errors."
        >
          <PlotlyChart
            data={litters.map((litter, i) => ({
              y: data.filter((d) => d.litter === litter).map((d) => d.log_lik),
              type: "box" as const,
              name: litter,
              boxpoints: "outliers" as const,
              marker: {
                color: CHART_COLORS[i % CHART_COLORS.length],
                outliercolor: ACCENT.coral,
              },
              line: { width: 1.5 },
              hovertemplate: "<b>%{x}</b><br>LL: %{y:.3f}<extra></extra>",
            }))}
            layout={{
              height: h480,
              yaxis: { title: { text: "Log-Likelihood", standoff: 10 } },
              xaxis: { tickangle: -30, tickfont: { size: 10 } },
              showlegend: false,
            }}
          />
        </ChartCard>

        <ChartCard
          title="Ranked Anomaly Scores"
          subtitle="All children sorted by log-likelihood. Red markers indicate LL < -5 (anomalous)."
          description="All 692 children are plotted from most anomalous (left) to best-explained (right). The dashed threshold at LL = -5 separates children that fall within expected model variation from those the model struggles to explain. A smooth, gradual curve with few red points indicates the model handles the vast majority of offspring well."
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
                  size: 5,
                  color: sorted.map((d) => (d.log_lik < -5 ? ACCENT.coral : TEAL[600])),
                  line: { color: "white", width: 0.5 },
                  opacity: 0.85,
                },
                hovertemplate: "<b>%{text}</b><br>Rank: %{x}<br>LL: %{y:.3f}<extra></extra>",
              },
            ]}
            layout={{
              height: h420,
              xaxis: { title: { text: "Rank (worst to best)", standoff: 10 } },
              yaxis: { title: { text: "Log-Likelihood", standoff: 10 } },
              shapes: [
                { type: "line", y0: -5, y1: -5, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: ACCENT.coral, width: 1.5 } },
              ],
              annotations: [
                {
                  x: 1, y: -5, xref: "paper", text: "LL = -5 threshold",
                  showarrow: false, font: { size: 10, color: ACCENT.coral },
                  yshift: -12, xanchor: "right",
                },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Top 10 Most Anomalous Children</h2>
          <DataTable
            data={worst10 as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>>[]}
            downloadFilename="anomaly_scores.csv"
          />
        </div>
      </div>
    </div>
  );
}
