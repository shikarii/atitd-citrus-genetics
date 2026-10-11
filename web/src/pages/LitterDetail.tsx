import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import {
  loadChildren,
  loadFittedGenes,
  loadResiduals,
  loadAnomalyScores,
  type Child,
  type FittedGenes,
  type ResidualEntry,
  type AnomalyScore,
  TRAITS,
  LITTERS,
} from "../lib/data";
import { CHART_COLORS, SLATE, ACCENT } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

const childColumns: ColumnDef<Child, unknown>[] = [
  { accessorKey: "child", header: "Child #" },
  ...TRAITS.map(
    (t) =>
      ({
        accessorKey: t,
        header: t,
        cell: (info) => info.getValue() as number,
      }) as ColumnDef<Child, unknown>,
  ),
  ...TRAITS.map(
    (t) =>
      ({
        accessorKey: `A_${t}`,
        header: `A_${t}`,
        cell: (info) => info.getValue() as number,
      }) as ColumnDef<Child, unknown>,
  ),
  ...TRAITS.map(
    (t) =>
      ({
        accessorKey: `B_${t}`,
        header: `B_${t}`,
        cell: (info) => info.getValue() as number,
      }) as ColumnDef<Child, unknown>,
  ),
];

export function LitterDetail() {
  const { name } = useParams<{ name: string }>();
  const [children, setChildren] = useState<Child[]>([]);
  const [genes, setGenes] = useState<FittedGenes[]>([]);
  const [residuals, setResiduals] = useState<ResidualEntry[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      loadChildren().then(setChildren).catch(() => {}),
      loadFittedGenes().then(setGenes).catch(() => {}),
      loadResiduals().then(setResiduals).catch(() => {}),
      loadAnomalyScores().then(setAnomalies).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const litterChildren = children.filter((c) => c.litter === name);
  const litterGenes = genes.find((g) => g.litter === name);
  const litterResiduals = residuals.filter((r) => r.litter === name);
  const litterAnomalies = anomalies.filter((a) => a.litter === name);

  if (!name) {
    return <div className="text-slate-500">No litter selected.</div>;
  }

  if (!loading && children.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">{name}</h1>
        <NoData />
      </div>
    );
  }

  const firstChild = litterChildren[0];
  const parentA = firstChild
    ? Object.fromEntries(TRAITS.map((t) => [t, firstChild[`A_${t}` as keyof Child] as number]))
    : {};
  const parentB = firstChild
    ? Object.fromEntries(TRAITS.map((t) => [t, firstChild[`B_${t}` as keyof Child] as number]))
    : {};

  const worstChild = [...litterAnomalies].sort((a, b) => a.log_lik - b.log_lik)[0];

  return (
    <div>
      <div className="flex items-center gap-3 mb-1">
        <h1 className="text-2xl font-bold text-slate-800">{name}</h1>
        <span className="text-sm text-slate-400">Litter Deep Dive</span>
      </div>

      <div className="flex gap-2 mb-6 text-sm">
        {LITTERS.map((l) => (
          <Link
            key={l}
            to={`/litter/${l}`}
            className={`px-2 py-1 rounded text-xs ${
              l === name
                ? "bg-teal-100 text-teal-800 font-medium"
                : "text-slate-500 hover:bg-slate-100"
            }`}
          >
            {l}
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Children" value={litterChildren.length || "..."} />
        <MetricCard
          label="Log-Likelihood"
          value={litterGenes?.loglik?.toFixed(1) ?? "..."}
          detail="CLAIM MLE fit"
        />
        <MetricCard
          label="Clone Share"
          value={litterGenes?.clone_share?.toFixed(4) ?? "..."}
        />
        {worstChild && (
          <MetricCard
            label="Worst Child LL"
            value={worstChild.log_lik.toFixed(2)}
            detail={`Child #${worstChild.child_num}`}
          />
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Parent A Traits</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {TRAITS.map((t) => (
              <div key={t} className="flex justify-between">
                <span className="text-slate-500">{t}:</span>
                <span className="font-medium">{parentA[t] ?? "?"}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Parent B Traits</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {TRAITS.map((t) => (
              <div key={t} className="flex justify-between">
                <span className="text-slate-500">{t}:</span>
                <span className="font-medium">{parentB[t] ?? "?"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {litterGenes && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-2">CLAIM MLE Fitted Hidden Genes</h3>
          <div className="grid grid-cols-4 gap-4 text-sm">
            {TRAITS.map((t) => (
              <div key={t}>
                <div className="text-slate-400 text-xs uppercase mb-1">{t}</div>
                <div>A: {String(litterGenes[`A_${t}_genes`] ?? "?")}</div>
                <div>B: {String(litterGenes[`B_${t}_genes`] ?? "?")}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-6">
        <ChartCard
          title="Child Trait Distributions"
          subtitle="Box plots with individual points. Blue dashed line = Parent A trait value, red dashed = Parent B."
        >
          <PlotlyChart
            data={TRAITS.map((trait, i) => ({
              y: litterChildren.map((c) => c[trait as keyof Child] as number),
              type: "box" as const,
              name: trait,
              boxpoints: "all" as const,
              jitter: 0.3,
              pointpos: -1.8,
              marker: {
                color: CHART_COLORS[i],
                size: 5,
                line: { color: "white", width: 0.5 },
              },
              line: { width: 1.5 },
              hovertemplate: "<b>%{x}</b><br>Value: %{y}<extra></extra>",
            }))}
            layout={{
              height: 450,
              yaxis: { title: { text: "Trait Value (0-1000)", standoff: 10 } },
              shapes: TRAITS.flatMap((trait, i) => [
                {
                  type: "line" as const,
                  x0: i - 0.4, x1: i + 0.4,
                  y0: parentA[trait] ?? 0, y1: parentA[trait] ?? 0,
                  line: { color: ACCENT.indigo, dash: "dash" as const, width: 2 },
                },
                {
                  type: "line" as const,
                  x0: i - 0.4, x1: i + 0.4,
                  y0: parentB[trait] ?? 0, y1: parentB[trait] ?? 0,
                  line: { color: ACCENT.coral, dash: "dash" as const, width: 2 },
                },
              ]),
              annotations: [
                { x: 0, y: 1.08, yref: "paper", xref: "paper", text: "--- Parent A  --- Parent B", showarrow: false, font: { size: 10, color: SLATE[500] } },
              ],
            }}
          />
        </ChartCard>

        {litterResiduals.length > 0 && (
          <ChartCard
            title="Per-Child Residuals"
            subtitle="Observed minus CLAIM predicted per trait. Zero line indicates perfect prediction."
          >
            <PlotlyChart
              data={TRAITS.map((trait, i) => ({
                x: litterResiduals.map((r) => r.child_num),
                y: litterResiduals.map(
                  (r) => r[`${trait}_residual` as keyof ResidualEntry] as number,
                ),
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: trait,
                marker: { size: 7, color: CHART_COLORS[i], line: { color: "white", width: 1 } },
                line: { color: CHART_COLORS[i], width: 1.5 },
                hovertemplate: "<b>Child #%{x}</b><br>Residual: %{y:.1f}<extra>%{fullData.name}</extra>",
              }))}
              layout={{
                height: 420,
                xaxis: { title: { text: "Child #", standoff: 10 }, dtick: 1 },
                yaxis: { title: { text: "Residual", standoff: 10 } },
                shapes: [
                  {
                    type: "line", y0: 0, y1: 0, x0: 0, x1: 1,
                    xref: "paper", line: { dash: "dash", color: SLATE[700], width: 1.5 },
                  },
                ],
                legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
              }}
            />
          </ChartCard>
        )}

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Children Data</h2>
          <DataTable
            data={litterChildren as unknown as Record<string, unknown>[]}
            columns={childColumns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename={`${name}_children.csv`}
          />
        </div>
      </div>
    </div>
  );
}
