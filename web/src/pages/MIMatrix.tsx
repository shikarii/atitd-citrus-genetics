import { useEffect, useState, useMemo } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { NoData } from "../components/NoData";
import { loadMIMatrix, type MIEntry, TRAITS } from "../lib/data";

const PARENT_VARS = TRAITS.flatMap((t) => [`A_${t}`, `B_${t}`]);

export function MIMatrix() {
  const [data, setData] = useState<MIEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMIMatrix()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const { heatmapZ, heatmapX, heatmapY, maxExcess, nHighZ } = useMemo(() => {
    if (data.length === 0) return { heatmapZ: [], heatmapX: [], heatmapY: [], maxExcess: 0, nHighZ: 0 };

    const childVars = [...TRAITS];
    const parentVars = PARENT_VARS;

    const matrix: number[][] = parentVars.map((pv) =>
      childVars.map((cv) => {
        const entry = data.find((e) => e.parent_var === pv && e.child_var === cv);
        return entry?.mi_excess ?? 0;
      }),
    );

    return {
      heatmapZ: matrix,
      heatmapX: childVars,
      heatmapY: parentVars,
      maxExcess: Math.max(...data.map((e) => e.mi_excess)),
      nHighZ: data.filter((e) => Math.abs(e.mi_excess_z) > 2).length,
    };
  }, [data]);

  const diagonalEntries = data.filter((e) => e.is_diagonal);
  const offDiagEntries = data.filter((e) => !e.is_diagonal);
  const meanDiagExcess = diagonalEntries.length > 0
    ? (diagonalEntries.reduce((s, e) => s + e.mi_excess, 0) / diagonalEntries.length)
    : 0;

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Mutual Information Matrix</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Mutual Information Matrix</h1>
      <p className="text-sm text-slate-500 mb-6">
        Excess mutual information between parent traits and child traits,
        compared to a shuffled baseline. High on-diagonal MI confirms
        parent-child trait linkage; high off-diagonal MI would suggest unexpected coupling.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Parent-Child Pairs" value={data.length || "..."} />
        <MetricCard label="Max MI Excess" value={maxExcess.toFixed(4)} />
        <MetricCard label="Mean Diagonal Excess" value={meanDiagExcess.toFixed(4)} />
        <MetricCard label="Off-Diag |z| > 2" value={nHighZ} detail="Potential cross-talk" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="MI Excess Heatmap (parent var x child trait)"
          subtitle="Diagonal entries should dominate if traits are inherited independently"
        >
          <PlotlyChart
            data={[
              {
                z: heatmapZ,
                x: heatmapX,
                y: heatmapY,
                type: "heatmap",
                colorscale: "YlOrRd",
                text: heatmapZ.map((row) => row.map((v) => v.toFixed(4))) as unknown as string[],
                texttemplate: "%{text}",
                hovertemplate: "Parent: %{y}<br>Child: %{x}<br>MI Excess: %{z:.4f}<extra></extra>",
              },
            ]}
            layout={{
              height: 450,
              xaxis: { title: { text: "Child Trait" } },
              yaxis: { title: { text: "Parent Variable" } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="MI Excess Z-Scores"
          subtitle="How many standard deviations above shuffled baseline"
        >
          <PlotlyChart
            data={[
              {
                x: diagonalEntries.map((e) => `${e.parent_var} -> ${e.child_var}`),
                y: diagonalEntries.map((e) => e.mi_excess_z),
                type: "bar",
                name: "Diagonal (expected)",
                marker: { color: "#0D9488" },
              },
              {
                x: offDiagEntries.map((e) => `${e.parent_var} -> ${e.child_var}`),
                y: offDiagEntries.map((e) => e.mi_excess_z),
                type: "bar",
                name: "Off-diagonal",
                marker: { color: "#94A3B8" },
              },
            ]}
            layout={{
              height: 400,
              xaxis: { title: { text: "Parent -> Child pair" }, tickangle: -45 },
              yaxis: { title: { text: "Z-score (excess MI)" } },
              barmode: "group",
              shapes: [
                { type: "line", y0: 2, y1: 2, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#EF4444" } },
                { type: "line", y0: -2, y1: -2, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#EF4444" } },
              ],
            }}
          />
        </ChartCard>
      </div>
    </div>
  );
}
