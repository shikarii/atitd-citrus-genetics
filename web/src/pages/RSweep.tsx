import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadRSweep, loadInterpretations, type RSweepEntry, type Interpretations } from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { CHART_COLORS, SLATE } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<RSweepEntry>[] = [
  { accessorKey: "R", header: "R" },
  { accessorKey: "fit_ll", header: "Fit LL", cell: (info) => info.getValue<number>().toFixed(1) },
  { accessorKey: "cv_ll", header: "CV LL", cell: (info) => info.getValue<number>().toFixed(1) },
  { accessorKey: "delta_fit", header: "Delta Fit", cell: (info) => info.getValue<number>().toFixed(1) },
  { accessorKey: "delta_cv", header: "Delta CV", cell: (info) => info.getValue<number>().toFixed(1) },
];

export function RSweep() {
  const [data, setData] = useState<RSweepEntry[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRSweep()
      .then(setData)
      .catch(() => undefined)
      .finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const bestCV = data.length > 0 ? data.reduce((a, b) => (b.cv_ll > a.cv_ll ? b : a)) : null;
  const bestFit = data.length > 0 ? data.reduce((a, b) => (b.fit_ll > a.fit_ll ? b : a)) : null;

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Parameter Sensitivity: R Sweep</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Parameter Sensitivity: R Sweep</h1>
      <p className="text-sm text-slate-500 mb-6">
        Sweeping the mutation nudge range R from 50 to 300, measuring fit and
        cross-validated log-likelihood. The true R is the value maximizing CV LL.
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          CLAIM assumes each child's trait inherits a parent gene plus a uniform mutation drawn
          from one of 8 offsets in [-R, +R]. The default R = 150 was determined by prior analysis,
          but how sensitive are our results to this choice? We sweep R across a range of values and
          re-fit the entire model at each point. If the cross-validated log-likelihood curve has a
          sharp peak at R = 150, it confirms both the parameter value and the model's sensitivity.
          A flat curve would mean R is poorly constrained by the data.
        </p>
      </div>

      <FindingsSummary interpretation={interps.r_sweep} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="R Values Tested" value={data.length || "..."} />
        <MetricCard label="Best R (CV)" value={bestCV?.R ?? "..."} detail={`cv_ll = ${bestCV?.cv_ll.toFixed(1) ?? "..."}`} />
        <MetricCard label="Best R (Fit)" value={bestFit?.R ?? "..."} detail={`fit_ll = ${bestFit?.fit_ll.toFixed(1) ?? "..."}`} />
        <MetricCard label="CLAIM Default R" value="150" detail="8 offsets in [-R, +R]" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Log-Likelihood vs Nudge Range R"
          subtitle="In-sample fit (solid) and leave-one-litter-out cross-validated (dashed) log-likelihood across R values"
          description="The solid line shows how well the model fits training data at each R value — this always improves with more flexible R. The dashed line shows cross-validated performance, which penalizes overfitting. The peak of the dashed curve identifies the true optimal R. A vertical dotted line marks R = 150, the CLAIM default. The gap between the two curves at large R reveals overfitting."
        >
          <PlotlyChart
            data={[
              {
                x: data.map((d) => d.R),
                y: data.map((d) => d.fit_ll),
                type: "scatter",
                mode: "lines+markers" as const,
                name: "In-Sample Fit LL",
                marker: { color: CHART_COLORS[0], size: 7, line: { color: "white", width: 1 } },
                line: { color: CHART_COLORS[0], width: 2 },
                hovertemplate: "<b>R = %{x}</b><br>Fit LL: %{y:.1f}<extra></extra>",
              },
              {
                x: data.map((d) => d.R),
                y: data.map((d) => d.cv_ll),
                type: "scatter",
                mode: "lines+markers" as const,
                name: "Cross-Validated LL",
                marker: { color: CHART_COLORS[1], size: 7, symbol: "diamond", line: { color: "white", width: 1 } },
                line: { color: CHART_COLORS[1], dash: "dash", width: 2 },
                hovertemplate: "<b>R = %{x}</b><br>CV LL: %{y:.1f}<extra></extra>",
              },
            ]}
            layout={{
              height: 480,
              xaxis: { title: { text: "R (Mutation Nudge Range)", standoff: 10 }, dtick: 25 },
              yaxis: { title: { text: "Log-Likelihood", standoff: 10 } },
              shapes: [
                {
                  type: "line",
                  x0: 150, x1: 150, y0: 0, y1: 1,
                  yref: "paper",
                  line: { dash: "dot", color: SLATE[400], width: 1.5 },
                },
              ],
              annotations: [
                {
                  x: 150, y: 1.05, yref: "paper",
                  text: "R = 150 (CLAIM default)",
                  showarrow: false,
                  font: { size: 10, color: SLATE[500] },
                },
              ],
              legend: { x: 0.01, y: 0.01, xanchor: "left", yanchor: "bottom" },
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">R Sweep Results</h2>
          <DataTable
            data={data as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>>[]}
            downloadFilename="r_sweep.csv"
          />
        </div>
      </div>
    </div>
  );
}
