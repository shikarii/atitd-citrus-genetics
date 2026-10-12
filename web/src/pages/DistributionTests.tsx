import { useEffect, useState, useMemo } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadDistributionTests, loadInterpretations, type DistributionTest, type Interpretations, TRAITS, LITTERS } from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { CHART_COLORS, TEAL, SLATE, ACCENT } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<DistributionTest>[] = [
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "trait", header: "Trait" },
  { accessorKey: "n_observed", header: "N" },
  { accessorKey: "ks_stat", header: "KS Stat", cell: (info) => info.getValue<number>().toFixed(4) },
  { accessorKey: "ks_pvalue", header: "KS p-value", cell: (info) => info.getValue<number>().toFixed(4) },
  { accessorKey: "ks_pvalue_fdr", header: "FDR p-value", cell: (info) => info.getValue<number>().toFixed(4) },
  { accessorKey: "ks_sig_fdr", header: "FDR Sig?", cell: (info) => info.getValue<boolean>() ? "Yes" : "No" },
  { accessorKey: "ad_stat", header: "AD Stat", cell: (info) => { const v = info.getValue<number | null>(); return v !== null ? v.toFixed(3) : "N/A"; } },
  { accessorKey: "ad_sig_5pct", header: "AD Sig?", cell: (info) => { const v = info.getValue<boolean | null>(); return v !== null ? (v ? "Yes" : "No") : "N/A"; } },
];

export function DistributionTests() {
  const [data, setData] = useState<DistributionTest[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDistributionTests()
      .then(setData)
      .catch(() => undefined)
      .finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const nSigFDR = data.filter((d) => d.ks_sig_fdr).length;
  const nSigRaw = data.filter((d) => d.ks_pvalue < 0.05).length;
  const nADSig = data.filter((d) => d.ad_sig_5pct).length;

  const { heatmapZ, heatmapText } = useMemo(() => {
    if (data.length === 0) return { heatmapZ: [], heatmapText: [] };

    const z = LITTERS.map((litter) =>
      TRAITS.map((trait) => {
        const entry = data.find((d) => d.litter === litter && d.trait === trait);
        return entry?.ks_stat ?? 0;
      }),
    );
    const text = LITTERS.map((litter) =>
      TRAITS.map((trait) => {
        const entry = data.find((d) => d.litter === litter && d.trait === trait);
        return entry?.ks_stat.toFixed(3) ?? "";
      }),
    );
    return { heatmapZ: z, heatmapText: text };
  }, [data]);

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Distribution Goodness-of-Fit Tests</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Distribution Goodness-of-Fit Tests</h1>
      <p className="text-sm text-slate-500 mb-6">
        Two-sample KS and Anderson-Darling tests comparing observed child trait distributions
        against CLAIM-simulated distributions. Benjamini-Hochberg FDR correction applied.
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          Cross-validated log-likelihood tells us which model is <em>best</em>, but not whether it is <em>good enough</em>.
          Distribution tests formally compare the shape of observed trait values against what CLAIM
          predicts via simulation. For each of the 56 litter-trait combinations, we simulate 500 children
          from the fitted model and run two-sample Kolmogorov-Smirnov (KS) and Anderson-Darling (AD) tests.
          A significant result means the model's predicted distribution detectably differs from the observed
          one. Benjamini-Hochberg FDR correction controls the false discovery rate across all 56 tests.
        </p>
      </div>

      <FindingsSummary interpretation={interps.distribution_tests} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Tests" value={data.length || "..."} detail="14 litters x 4 traits" />
        <MetricCard label="KS Sig (raw p<0.05)" value={nSigRaw} />
        <MetricCard label="KS Sig (BH-FDR)" value={nSigFDR} />
        <MetricCard label="AD Sig (5%)" value={nADSig} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="KS Statistic Heatmap"
          subtitle="Litter (rows) vs trait (columns). Higher KS statistic indicates larger distributional discrepancy between observed and simulated."
          description="Each cell shows the KS test statistic for one litter-trait pair. The KS statistic measures the maximum vertical distance between the observed and simulated cumulative distribution functions — larger values mean the distributions differ more. Cool colors (green/teal) indicate good agreement; warm colors (amber/red) flag potential misfit. Systematic patterns across a row (litter) or column (trait) would suggest litter-specific or trait-specific model failures."
        >
          <PlotlyChart
            data={[
              {
                z: heatmapZ,
                x: [...TRAITS],
                y: [...LITTERS],
                type: "heatmap",
                colorscale: [
                  [0, "#F0FDFA"],
                  [0.2, TEAL[200]],
                  [0.4, ACCENT.amber],
                  [0.7, "#F97316"],
                  [1, ACCENT.coral],
                ],
                text: heatmapText as unknown as string[],
                texttemplate: "%{text}",
                textfont: { size: 11, color: SLATE[700] },
                hovertemplate: "<b>%{y}</b> / <b>%{x}</b><br>KS Statistic: %{z:.4f}<extra></extra>",
                colorbar: {
                  title: { text: "KS Statistic", side: "right" },
                  tickfont: { size: 10 },
                  len: 0.9,
                },
              },
            ]}
            layout={{
              height: 520,
              xaxis: { title: { text: "Trait", standoff: 15 }, tickfont: { size: 12 } },
              yaxis: { title: { text: "Litter", standoff: 15 }, tickfont: { size: 11 } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="Volcano Plot: KS Statistic vs Significance"
          subtitle="Each point is one litter-trait test. Diamonds indicate FDR-significant. Dashed line at p = 0.05."
          description="Volcano plots combine effect size (x-axis: KS statistic) with statistical significance (y-axis: -log10 p-value). Points above the dashed line are nominally significant at p < 0.05. Diamond markers indicate tests that remain significant after Benjamini-Hochberg FDR correction across all 56 tests. Points in the upper-right corner represent the most concerning misfits — both large and statistically significant."
        >
          <PlotlyChart
            data={TRAITS.map((trait, i) => {
              const entries = data.filter((d) => d.trait === trait);
              return {
                x: entries.map((d) => d.ks_stat),
                y: entries.map((d) => -Math.log10(Math.max(d.ks_pvalue, 1e-10))),
                text: entries.map((d) => `${d.litter} / ${d.trait}`),
                mode: "markers" as const,
                type: "scatter" as const,
                name: trait,
                marker: {
                  size: 11,
                  color: CHART_COLORS[i],
                  symbol: entries.map((d) => (d.ks_sig_fdr ? "diamond" : "circle")),
                  line: { color: "white", width: 1.5 },
                  opacity: 0.85,
                },
                hovertemplate: "<b>%{text}</b><br>KS: %{x:.4f}<br>-log\u2081\u2080(p): %{y:.2f}<extra></extra>",
              };
            })}
            layout={{
              height: 480,
              xaxis: { title: { text: "KS Statistic", standoff: 10 } },
              yaxis: { title: { text: "-log\u2081\u2080(KS p-value)", standoff: 10 } },
              shapes: [
                {
                  type: "line", y0: -Math.log10(0.05), y1: -Math.log10(0.05),
                  x0: 0, x1: 1, xref: "paper",
                  line: { dash: "dash", color: ACCENT.coral, width: 1.5 },
                },
              ],
              annotations: [
                {
                  x: 1, y: -Math.log10(0.05), xref: "paper",
                  text: "p = 0.05", showarrow: false,
                  font: { size: 10, color: ACCENT.coral },
                  yshift: 12, xanchor: "right",
                },
              ],
              legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">All Test Results</h2>
          <DataTable
            data={data as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>>[]}
            downloadFilename="distribution_tests.csv"
          />
        </div>
      </div>
    </div>
  );
}
