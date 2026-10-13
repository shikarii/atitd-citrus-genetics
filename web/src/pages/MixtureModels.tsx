import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadMixtureWeights, loadInterpretations, type MixtureWeight, type Interpretations } from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { TEAL, SLATE, ACCENT } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";
import { useResponsiveChartHeight } from "../lib/responsive";

const columns: ColumnDef<MixtureWeight>[] = [
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "n", header: "N" },
  { accessorKey: "pi_claim", header: "pi (CLAIM)", cell: (info) => info.getValue<number>().toFixed(4) },
  { accessorKey: "pi_indep", header: "pi (INDEP)", cell: (info) => info.getValue<number>().toFixed(4) },
  { accessorKey: "log_lik_claim_only", header: "LL CLAIM", cell: (info) => info.getValue<number>().toFixed(1) },
  { accessorKey: "log_lik_mixture", header: "LL Mixture", cell: (info) => info.getValue<number>().toFixed(1) },
  { accessorKey: "delta_ll", header: "Delta LL", cell: (info) => info.getValue<number>().toFixed(2) },
];

export function MixtureModels() {
  const [data, setData] = useState<MixtureWeight[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);
  const h480 = useResponsiveChartHeight(480);
  const h420 = useResponsiveChartHeight(420);

  useEffect(() => {
    loadMixtureWeights()
      .then(setData)
      .catch(() => undefined)
      .finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
  }, []);

  const meanPi = data.length > 0
    ? data.reduce((s, d) => s + d.pi_claim, 0) / data.length
    : 0;
  const minPi = data.length > 0 ? Math.min(...data.map((d) => d.pi_claim)) : 0;
  const nLow = data.filter((d) => d.pi_claim < 0.7).length;
  const sorted = [...data].sort((a, b) => a.pi_claim - b.pi_claim);

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">CLAIM + INDEP Mixture Models</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">CLAIM + INDEP Mixture Models</h1>
      <p className="text-sm text-slate-500 mb-6">
        For each litter, a mixture model is fit: pi x CLAIM + (1-pi) x INDEP.
        pi near 1 means CLAIM explains nearly all children; pi near 0 means mostly unexplained.
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          Mixture decomposition tests whether CLAIM is self-sufficient or whether some children
          are better explained by a non-informative alternative. For each litter, we fit a two-component
          mixture: pi x CLAIM + (1-pi) x INDEP, where INDEP is a uniform (independence) model that
          treats all trait values as equally likely. If CLAIM is the true generating mechanism, the
          optimal mixing weight pi should be near 1.0, meaning no children benefit from the INDEP
          escape component. Low pi values identify litters where a substantial fraction of offspring
          deviate from CLAIM's predictions.
        </p>
      </div>

      <FindingsSummary interpretation={interps.mixture} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Mean CLAIM Weight" value={meanPi.toFixed(4)} />
        <MetricCard label="Lowest pi" value={minPi.toFixed(4)} detail="Most anomalous litter" />
        <MetricCard label="Litters with pi < 0.7" value={nLow} />
        <MetricCard label="Total Litters" value={data.length || "..."} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="CLAIM Mixture Weight per Litter"
          subtitle="Sorted by pi (lowest first). Green line: pi = 0.9 (strong fit). Amber line: pi = 0.7 (warning threshold)."
          description="Each bar shows the optimal CLAIM weight (pi) for one litter. Teal bars above the green line (pi > 0.9) indicate litters where CLAIM explains virtually all offspring. Amber bars between 0.7 and 0.9 warrant investigation. Red bars below 0.7 indicate litters where 30%+ of children are better modeled as random noise, suggesting possible data issues or unmodeled mechanics for those specific crosses."
        >
          <PlotlyChart
            data={[
              {
                x: sorted.map((d) => d.litter),
                y: sorted.map((d) => d.pi_claim),
                type: "bar",
                marker: {
                  color: sorted.map((d) =>
                    d.pi_claim >= 0.9 ? TEAL[600] : d.pi_claim >= 0.7 ? ACCENT.amber : ACCENT.coral,
                  ),
                  line: { color: "rgba(0,0,0,0.08)", width: 0.5 },
                },
                text: sorted.map((d) => d.pi_claim.toFixed(3)),
                textposition: "outside" as const,
                textfont: { size: 10, color: SLATE[500] },
                hovertemplate: "<b>%{x}</b><br>pi(CLAIM) = %{y:.4f}<extra></extra>",
              },
            ]}
            layout={{
              height: h480,
              xaxis: { title: { text: "Litter", standoff: 10 } },
              yaxis: { title: { text: "\u03C0 (CLAIM Weight)", standoff: 10 }, range: [0, 1.08] },
              shapes: [
                { type: "line", y0: 0.9, y1: 0.9, x0: 0, x1: 1, xref: "paper", line: { dash: "dot", color: ACCENT.emerald, width: 1.5 } },
                { type: "line", y0: 0.7, y1: 0.7, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: ACCENT.amber, width: 1.5 } },
              ],
              annotations: [
                { x: 1, y: 0.9, xref: "paper", text: "\u03C0 = 0.9", showarrow: false, font: { size: 10, color: ACCENT.emerald }, yshift: 10, xanchor: "right" },
                { x: 1, y: 0.7, xref: "paper", text: "\u03C0 = 0.7", showarrow: false, font: { size: 10, color: ACCENT.amber }, yshift: -10, xanchor: "right" },
              ],
            }}
          />
        </ChartCard>

        <ChartCard
          title="Mixture Log-Likelihood Improvement"
          subtitle="Delta LL = mixture LL - CLAIM-only LL. Positive values indicate improvement from adding INDEP component."
          description="This chart shows how much the mixture model improves over pure CLAIM for each litter. Small delta-LL values (near zero, teal) mean CLAIM alone is sufficient — adding the INDEP component does not help. Larger values (amber/red) indicate the mixture provides a meaningfully better fit, meaning some children in that litter are poorly explained by CLAIM alone."
        >
          <PlotlyChart
            data={(() => {
              const deltaSorted = [...data].sort((a, b) => b.delta_ll - a.delta_ll);
              return [{
                x: deltaSorted.map((d) => d.litter),
                y: deltaSorted.map((d) => d.delta_ll),
                type: "bar",
                marker: {
                  color: deltaSorted.map((d) =>
                    d.delta_ll > 1 ? ACCENT.coral : d.delta_ll > 0.1 ? ACCENT.amber : TEAL[600],
                  ),
                  line: { color: "rgba(0,0,0,0.08)", width: 0.5 },
                },
                text: deltaSorted.map((d) => d.delta_ll.toFixed(2)),
                textposition: "outside" as const,
                textfont: { size: 10, color: SLATE[500] },
                hovertemplate: "<b>%{x}</b><br>\u0394LL = %{y:.2f}<extra></extra>",
              }];
            })()}
            layout={{
              height: h420,
              xaxis: { title: { text: "Litter", standoff: 10 } },
              yaxis: { title: { text: "\u0394 Log-Likelihood (Mixture - CLAIM)", standoff: 10 } },
              shapes: [
                { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { color: SLATE[700], width: 1 } },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Mixture Weight Details</h2>
          <DataTable
            data={sorted as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>>[]}
            downloadFilename="mixture_weights.csv"
          />
        </div>
      </div>

      <div className="mt-8 bg-slate-50 rounded-lg p-5 border border-slate-200">
        <h3 className="font-semibold text-slate-800 mb-2">Interpretation</h3>
        <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
          <li><strong>pi near 1.0:</strong> CLAIM explains nearly all children. The mixture offers no benefit.</li>
          <li><strong>pi near 0.7:</strong> ~30% of children are better explained by INDEP (uniform noise).</li>
          <li><strong>High delta_ll:</strong> The mixture fit is meaningfully better than CLAIM alone.</li>
          <li>If most litters have pi &gt; 0.9, CLAIM is highly self-consistent across litters.</li>
        </ul>
      </div>
    </div>
  );
}
