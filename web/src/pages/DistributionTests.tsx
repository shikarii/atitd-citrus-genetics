import { useEffect, useState, useMemo } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { loadDistributionTests, type DistributionTest, TRAITS, LITTERS } from "../lib/data";
import { CHART_COLORS } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<DistributionTest, unknown>[] = [
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "trait", header: "Trait" },
  { accessorKey: "n_observed", header: "N" },
  { accessorKey: "ks_stat", header: "KS Stat", cell: (info) => (info.getValue() as number).toFixed(4) },
  { accessorKey: "ks_pvalue", header: "KS p-value", cell: (info) => (info.getValue() as number).toFixed(4) },
  { accessorKey: "ks_pvalue_fdr", header: "FDR p-value", cell: (info) => (info.getValue() as number).toFixed(4) },
  { accessorKey: "ks_sig_fdr", header: "FDR Sig?", cell: (info) => (info.getValue() as boolean) ? "Yes" : "No" },
  { accessorKey: "ad_stat", header: "AD Stat", cell: (info) => (info.getValue() as number).toFixed(3) },
  { accessorKey: "ad_sig_5pct", header: "AD Sig?", cell: (info) => (info.getValue() as boolean) ? "Yes" : "No" },
];

export function DistributionTests() {
  const [data, setData] = useState<DistributionTest[]>([]);

  useEffect(() => {
    loadDistributionTests().then(setData).catch(() => {});
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
        return entry?.ks_stat?.toFixed(3) ?? "";
      }),
    );
    return { heatmapZ: z, heatmapText: text };
  }, [data]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Distribution Goodness-of-Fit Tests</h1>
      <p className="text-sm text-slate-500 mb-6">
        Two-sample KS and Anderson-Darling tests comparing observed child trait distributions
        against CLAIM-simulated distributions. Benjamini-Hochberg FDR correction applied.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total Tests" value={data.length || "..."} detail="14 litters x 4 traits" />
        <MetricCard label="KS Sig (raw p<0.05)" value={nSigRaw} />
        <MetricCard label="KS Sig (BH-FDR)" value={nSigFDR} />
        <MetricCard label="AD Sig (5%)" value={nADSig} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="KS Statistic Heatmap (litter x trait)"
          subtitle="Higher KS statistic = larger distributional discrepancy"
        >
          <PlotlyChart
            data={[
              {
                z: heatmapZ,
                x: [...TRAITS],
                y: [...LITTERS],
                type: "heatmap",
                colorscale: "YlOrRd",
                text: heatmapText as unknown as string[],
                texttemplate: "%{text}",
                hovertemplate: "Litter: %{y}<br>Trait: %{x}<br>KS Stat: %{z:.4f}<extra></extra>",
              },
            ]}
            layout={{
              height: 500,
              xaxis: { title: { text: "Trait" } },
              yaxis: { title: { text: "Litter" } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="Volcano Plot: KS Statistic vs Significance"
          subtitle="-log10(p) on y-axis; points above dashed line are significant"
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
                  size: 10,
                  color: CHART_COLORS[i],
                  symbol: entries.map((d) => (d.ks_sig_fdr ? "diamond" : "circle")),
                },
                hovertemplate: "%{text}<br>KS: %{x:.4f}<br>-log10(p): %{y:.2f}<extra></extra>",
              };
            })}
            layout={{
              height: 450,
              xaxis: { title: { text: "KS Statistic" } },
              yaxis: { title: { text: "-log10(KS p-value)" } },
              shapes: [
                {
                  type: "line", y0: -Math.log10(0.05), y1: -Math.log10(0.05),
                  x0: 0, x1: 1, xref: "paper",
                  line: { dash: "dash", color: "#EF4444", width: 1 },
                },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">All Test Results</h2>
          <DataTable
            data={data as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename="distribution_tests.csv"
          />
        </div>
      </div>
    </div>
  );
}
