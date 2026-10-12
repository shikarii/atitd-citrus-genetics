import { useEffect, useState, useMemo } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { NoData } from "../components/NoData";
import { loadMIMatrix, type MIEntry, TRAITS } from "../lib/data";
import { TEAL, SLATE, ACCENT } from "../lib/colors";

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

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          If CLAIM is correct, each child trait (e.g., sweetness) should depend primarily on the
          corresponding parent genes and be statistically independent of unrelated parent traits (e.g., color genes).
          Mutual information (MI) quantifies the statistical dependence between two variables without assuming
          linearity. We compute MI excess — the observed MI minus the mean MI under random shuffling — to
          control for finite-sample noise. High diagonal entries confirm that parent genes do predict
          child traits. High off-diagonal entries would reveal unexpected cross-trait coupling that
          CLAIM does not model, pointing to a missing mechanism.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Parent-Child Pairs" value={data.length || "..."} />
        <MetricCard label="Max MI Excess" value={maxExcess.toFixed(4)} />
        <MetricCard label="Mean Diagonal Excess" value={meanDiagExcess.toFixed(4)} />
        <MetricCard label="Off-Diag |z| > 2" value={nHighZ} detail="Potential cross-talk" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="MI Excess Heatmap"
          subtitle="Parent variable (rows) vs child trait (columns). Diagonal entries should dominate if traits are inherited independently."
          description="Each cell shows how much more mutual information exists between a parent variable and child trait than expected by chance. Strong diagonal entries (e.g., A_color to color) confirm that parents' genes predict the corresponding child trait. Weak off-diagonal entries confirm that traits are inherited independently — color genes do not influence sweetness, for example."
        >
          <PlotlyChart
            data={[
              {
                z: heatmapZ,
                x: heatmapX,
                y: heatmapY,
                type: "heatmap",
                colorscale: [
                  [0, "#F0FDFA"],
                  [0.25, TEAL[200]],
                  [0.5, TEAL[400]],
                  [0.75, TEAL[600]],
                  [1, TEAL[900]],
                ],
                text: heatmapZ.map((row) => row.map((v) => v.toFixed(4))) as unknown as string[],
                texttemplate: "%{text}",
                textfont: { size: 11, color: SLATE[700] },
                hovertemplate: "<b>%{y}</b> → <b>%{x}</b><br>MI Excess: %{z:.4f}<extra></extra>",
                colorbar: {
                  title: { text: "MI Excess", side: "right" },
                  tickfont: { size: 10 },
                  len: 0.9,
                },
              },
            ]}
            layout={{
              height: 480,
              xaxis: { title: { text: "Child Trait", standoff: 15 }, tickfont: { size: 12 } },
              yaxis: { title: { text: "Parent Variable", standoff: 15 }, tickfont: { size: 11 } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="MI Excess Z-Scores"
          subtitle="Standard deviations above shuffled baseline. Dashed lines at z = +/- 2 (95% threshold)."
          description="Z-scores normalize MI excess by the standard deviation of the shuffled distribution, making it easy to identify statistically significant dependencies. Diagonal entries (teal) with z > 2 confirm real parent-child linkage. Off-diagonal entries (gray) with z > 2 would flag unexpected cross-trait coupling. Most off-diagonal bars should fall well within the dashed thresholds."
        >
          <PlotlyChart
            data={[
              {
                x: diagonalEntries.map((e) => `${e.parent_var} → ${e.child_var}`),
                y: diagonalEntries.map((e) => e.mi_excess_z),
                type: "bar",
                name: "Diagonal (expected)",
                marker: {
                  color: TEAL[600],
                  line: { color: TEAL[700], width: 0.5 },
                },
                hovertemplate: "<b>%{x}</b><br>z = %{y:.2f}<extra>Diagonal</extra>",
              },
              {
                x: offDiagEntries.map((e) => `${e.parent_var} → ${e.child_var}`),
                y: offDiagEntries.map((e) => e.mi_excess_z),
                type: "bar",
                name: "Off-diagonal",
                marker: {
                  color: SLATE[400],
                  line: { color: SLATE[500], width: 0.5 },
                },
                hovertemplate: "<b>%{x}</b><br>z = %{y:.2f}<extra>Off-diagonal</extra>",
              },
            ]}
            layout={{
              height: 420,
              xaxis: {
                title: { text: "Parent → Child Pair", standoff: 20 },
                tickangle: -45,
                tickfont: { size: 9 },
              },
              yaxis: { title: { text: "Z-Score (Excess MI)", standoff: 10 } },
              barmode: "group",
              bargap: 0.2,
              shapes: [
                { type: "line", y0: 2, y1: 2, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: ACCENT.coral, width: 1.5 } },
                { type: "line", y0: -2, y1: -2, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: ACCENT.coral, width: 1.5 } },
              ],
              annotations: [
                { x: 1, y: 2, xref: "paper", text: "z = 2", showarrow: false, font: { size: 10, color: ACCENT.coral }, yshift: 10 },
                { x: 1, y: -2, xref: "paper", text: "z = -2", showarrow: false, font: { size: 10, color: ACCENT.coral }, yshift: -10 },
              ],
              legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
            }}
          />
        </ChartCard>
      </div>
    </div>
  );
}
