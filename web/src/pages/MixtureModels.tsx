import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadMixtureWeights, type MixtureWeight } from "../lib/data";

import type { ColumnDef } from "@tanstack/react-table";

const columns: ColumnDef<MixtureWeight, unknown>[] = [
  { accessorKey: "litter", header: "Litter" },
  { accessorKey: "n", header: "N" },
  { accessorKey: "pi_claim", header: "pi (CLAIM)", cell: (info) => (info.getValue() as number).toFixed(4) },
  { accessorKey: "pi_indep", header: "pi (INDEP)", cell: (info) => (info.getValue() as number).toFixed(4) },
  { accessorKey: "log_lik_claim_only", header: "LL CLAIM", cell: (info) => (info.getValue() as number).toFixed(1) },
  { accessorKey: "log_lik_mixture", header: "LL Mixture", cell: (info) => (info.getValue() as number).toFixed(1) },
  { accessorKey: "delta_ll", header: "Delta LL", cell: (info) => (info.getValue() as number).toFixed(2) },
];

export function MixtureModels() {
  const [data, setData] = useState<MixtureWeight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMixtureWeights()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Mean CLAIM Weight" value={meanPi.toFixed(4)} />
        <MetricCard label="Lowest pi" value={minPi.toFixed(4)} detail="Most anomalous litter" />
        <MetricCard label="Litters with pi < 0.7" value={nLow} />
        <MetricCard label="Total Litters" value={data.length || "..."} />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="CLAIM Mixture Weight per Litter"
          subtitle="Sorted by pi (lowest first); color encodes weight"
        >
          <PlotlyChart
            data={[
              {
                x: sorted.map((d) => d.litter),
                y: sorted.map((d) => d.pi_claim),
                type: "bar",
                marker: {
                  color: sorted.map((d) => d.pi_claim),
                  colorscale: "RdYlGn",
                  cmin: 0,
                  cmax: 1,
                },
                text: sorted.map((d) => d.pi_claim.toFixed(3)),
                textposition: "outside" as const,
              },
            ]}
            layout={{
              height: 450,
              xaxis: { title: { text: "Litter" } },
              yaxis: { title: { text: "pi (CLAIM weight)" }, range: [0, 1.05] },
              shapes: [
                { type: "line", y0: 0.9, y1: 0.9, x0: 0, x1: 1, xref: "paper", line: { dash: "dot", color: "#10B981", width: 1 } },
                { type: "line", y0: 0.7, y1: 0.7, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#F59E0B", width: 1 } },
              ],
            }}
          />
        </ChartCard>

        <ChartCard
          title="Mixture vs CLAIM-Only Log-Likelihood"
          subtitle="Positive delta means the mixture improves over CLAIM-only"
        >
          <PlotlyChart
            data={[
              {
                x: [...data].sort((a, b) => b.delta_ll - a.delta_ll).map((d) => d.litter),
                y: [...data].sort((a, b) => b.delta_ll - a.delta_ll).map((d) => d.delta_ll),
                type: "bar",
                marker: {
                  color: [...data].sort((a, b) => b.delta_ll - a.delta_ll).map((d) => d.delta_ll),
                  colorscale: "RdYlGn",
                },
              },
            ]}
            layout={{
              height: 400,
              xaxis: { title: { text: "Litter" } },
              yaxis: { title: { text: "Delta log-likelihood (mixture - CLAIM)" } },
              shapes: [
                { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { color: "#334155" } },
              ],
            }}
          />
        </ChartCard>

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Mixture Weight Details</h2>
          <DataTable
            data={sorted as unknown as Record<string, unknown>[]}
            columns={columns as ColumnDef<Record<string, unknown>, unknown>[]}
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
