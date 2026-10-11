import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadRSweep, type RSweepEntry } from "../lib/data";
import { CHART_COLORS } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<RSweepEntry, unknown>[] = [
  { accessorKey: "R", header: "R" },
  { accessorKey: "fit_ll", header: "Fit LL", cell: (info) => (info.getValue() as number).toFixed(1) },
  { accessorKey: "cv_ll", header: "CV LL", cell: (info) => (info.getValue() as number).toFixed(1) },
  { accessorKey: "delta_fit", header: "Delta Fit", cell: (info) => (info.getValue() as number).toFixed(1) },
  { accessorKey: "delta_cv", header: "Delta CV", cell: (info) => (info.getValue() as number).toFixed(1) },
];

export function RSweep() {
  const [data, setData] = useState<RSweepEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRSweep()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="R Values Tested" value={data.length || "..."} />
        <MetricCard label="Best R (CV)" value={bestCV?.R ?? "..."} detail={`cv_ll = ${bestCV?.cv_ll?.toFixed(1) ?? "..."}`} />
        <MetricCard label="Best R (Fit)" value={bestFit?.R ?? "..."} detail={`fit_ll = ${bestFit?.fit_ll?.toFixed(1) ?? "..."}`} />
        <MetricCard label="CLAIM Default R" value="150" detail="8 offsets in [-R, +R]" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Log-Likelihood vs Nudge Range R"
          subtitle="Both fit (solid) and cross-validated (dashed) log-likelihood"
        >
          <PlotlyChart
            data={[
              {
                x: data.map((d) => d.R),
                y: data.map((d) => d.fit_ll),
                type: "scatter",
                mode: "lines+markers" as const,
                name: "Fit LL",
                marker: { color: CHART_COLORS[0], size: 6 },
                line: { color: CHART_COLORS[0] },
              },
              {
                x: data.map((d) => d.R),
                y: data.map((d) => d.cv_ll),
                type: "scatter",
                mode: "lines+markers" as const,
                name: "CV LL",
                marker: { color: CHART_COLORS[1], size: 6 },
                line: { color: CHART_COLORS[1], dash: "dash" },
              },
            ]}
            layout={{
              height: 450,
              xaxis: { title: { text: "R (mutation nudge range)" } },
              yaxis: { title: { text: "Log-Likelihood" } },
              shapes: [
                {
                  type: "line",
                  x0: 150, x1: 150, y0: 0, y1: 1,
                  yref: "paper",
                  line: { dash: "dot", color: "#94A3B8", width: 1 },
                },
              ],
              annotations: [
                {
                  x: 150, y: 1.05, yref: "paper",
                  text: "R=150 (CLAIM default)",
                  showarrow: false,
                  font: { size: 10, color: "#64748B" },
                },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">R Sweep Results</h2>
          <DataTable
            data={data as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename="r_sweep.csv"
          />
        </div>
      </div>
    </div>
  );
}
