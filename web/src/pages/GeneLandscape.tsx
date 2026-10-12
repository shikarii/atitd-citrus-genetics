import { useEffect, useState, useMemo } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { DataTable } from "../components/DataTable";
import { NoData } from "../components/NoData";
import { loadFittedGenes, type FittedGenes, TRAITS } from "../lib/data";
import { CHART_COLORS, SLATE } from "../lib/colors";
import type { ColumnDef } from "@tanstack/react-table";

interface GenePoint {
  litter: string;
  parent: string;
  trait: string;
  g1: number;
  g2: number;
  loglik: number;
}

export function GeneLandscape() {
  const [data, setData] = useState<FittedGenes[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFittedGenes()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const genePoints = useMemo(() => {
    const points: GenePoint[] = [];
    data.forEach((row) => {
      for (const parent of ["A", "B"]) {
        for (const trait of TRAITS) {
          const key = `${parent}_${trait}_genes`;
          const val = String(row[key] ?? "");
          const match = val.match(/(\d+)\s*[,/]\s*(\d+)/);
          if (match) {
            points.push({
              litter: row.litter,
              parent: `Parent ${parent}`,
              trait,
              g1: parseInt(match[1]!),
              g2: parseInt(match[2]!),
              loglik: row.loglik,
            });
          }
        }
      }
    });
    return points;
  }, [data]);

  const meanLL = data.length > 0
    ? data.reduce((s, d) => s + d.loglik, 0) / data.length
    : 0;
  const meanClone = data.length > 0
    ? data.reduce((s, d) => s + d.clone_share, 0) / data.length
    : 0;

  const tableColumns: ColumnDef<FittedGenes, unknown>[] = [
    { accessorKey: "litter", header: "Litter" },
    { accessorKey: "loglik", header: "Log-Lik", cell: (info) => (info.getValue() as number).toFixed(1) },
    { accessorKey: "clone_share", header: "Clone Share", cell: (info) => (info.getValue() as number).toFixed(3) },
    ...TRAITS.flatMap((t) => [
      { accessorKey: `A_${t}_genes`, header: `A ${t}` } as ColumnDef<FittedGenes, unknown>,
      { accessorKey: `B_${t}_genes`, header: `B ${t}` } as ColumnDef<FittedGenes, unknown>,
    ]),
  ];

  if (!loading && data.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Gene Landscape</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Gene Landscape</h1>
      <p className="text-sm text-slate-500 mb-6">
        MLE-fitted hidden gene pairs (g1, g2) for each parent and trait.
        Points along the diagonal indicate both genes have similar values.
      </p>

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          CLAIM assumes each parent carries two hidden gene values (g1, g2) per trait, and each child
          inherits one gene from each parent via a coin-flip mechanism. The MLE fitting procedure
          recovers these hidden gene values from observed offspring data. Visualizing the fitted genes
          serves as a sanity check: gene values should span the plausible range (0-1000), and litters
          with shared parents should recover consistent gene estimates. The clone share metric tracks
          what fraction of fitted gene combinations are degenerate (g1 = g2), which would indicate
          limited genetic diversity or fitting artifacts.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Litters Fitted" value={data.length || "..."} />
        <MetricCard label="Gene Points" value={genePoints.length || "..."} detail="2 parents x 4 traits x N litters" />
        <MetricCard label="Mean Log-Lik" value={meanLL.toFixed(1)} />
        <MetricCard label="Mean Clone Share" value={meanClone.toFixed(4)} />
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {TRAITS.map((trait, ti) => {
            const traitPoints = genePoints.filter((p) => p.trait === trait);
            const aPoints = traitPoints.filter((p) => p.parent === "Parent A");
            const bPoints = traitPoints.filter((p) => p.parent === "Parent B");

            return (
              <ChartCard
                key={trait}
                title={`Gene Pairs: ${trait.charAt(0).toUpperCase() + trait.slice(1)}`}
                subtitle="g1 vs g2 per parent. Points on the diagonal indicate homozygous-like genes."
                description="Each point represents one parent's fitted gene pair for this trait. The dashed diagonal line marks g1 = g2 (homozygous-like). Points far from the diagonal have heterozygous-like genes, producing more offspring diversity. The spatial distribution reveals whether the fitting procedure converges to physically sensible values across litters."
              >
                <PlotlyChart
                  data={[
                    {
                      x: aPoints.map((p) => p.g1),
                      y: aPoints.map((p) => p.g2),
                      text: aPoints.map((p) => p.litter),
                      mode: "text+markers" as const,
                      type: "scatter",
                      name: "Parent A",
                      textposition: "top right" as const,
                      textfont: { size: 9, color: SLATE[500] },
                      marker: {
                        size: 11,
                        color: CHART_COLORS[ti * 2],
                        line: { color: "white", width: 1.5 },
                        opacity: 0.85,
                      },
                      hovertemplate: "<b>%{text}</b><br>g1: %{x}<br>g2: %{y}<extra>Parent A</extra>",
                    },
                    {
                      x: bPoints.map((p) => p.g1),
                      y: bPoints.map((p) => p.g2),
                      text: bPoints.map((p) => p.litter),
                      mode: "text+markers" as const,
                      type: "scatter",
                      name: "Parent B",
                      textposition: "top right" as const,
                      textfont: { size: 9, color: SLATE[500] },
                      marker: {
                        size: 11,
                        color: CHART_COLORS[ti * 2 + 1],
                        symbol: "diamond",
                        line: { color: "white", width: 1.5 },
                        opacity: 0.85,
                      },
                      hovertemplate: "<b>%{text}</b><br>g1: %{x}<br>g2: %{y}<extra>Parent B</extra>",
                    },
                    {
                      x: [0, 1000],
                      y: [0, 1000],
                      mode: "lines" as const,
                      type: "scatter",
                      name: "g1 = g2",
                      line: { dash: "dash", color: SLATE[300], width: 1.5 },
                      showlegend: false,
                      hoverinfo: "skip" as const,
                    },
                  ]}
                  layout={{
                    height: 420,
                    xaxis: { title: { text: "Gene 1", standoff: 10 }, range: [0, 1000] },
                    yaxis: { title: { text: "Gene 2", standoff: 10 }, range: [0, 1000] },
                    legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
                  }}
                />
              </ChartCard>
            );
          })}
        </div>

        {genePoints.length > 0 && (
          <ChartCard
            title="3D Gene Landscape: All Traits"
            subtitle="Gene 1 vs Gene 2 vs per-litter log-likelihood across all traits and parents. Color encodes trait."
            description="This 3D view adds the per-litter log-likelihood as a z-axis, revealing whether certain gene configurations systematically produce better or worse model fits. Points clustered at high z-values across diverse g1/g2 positions indicate the model fits well regardless of the underlying genetics — a sign of robustness."
          >
            <PlotlyChart
              data={TRAITS.map((trait, ti) => {
                const pts = genePoints.filter((p) => p.trait === trait);
                return {
                  x: pts.map((p) => p.g1),
                  y: pts.map((p) => p.g2),
                  z: pts.map((p) => p.loglik),
                  text: pts.map((p) => `${p.litter} (${p.parent})`),
                  mode: "markers" as const,
                  type: "scatter3d" as const,
                  name: trait.charAt(0).toUpperCase() + trait.slice(1),
                  marker: {
                    size: 5,
                    color: CHART_COLORS[ti],
                    opacity: 0.8,
                    line: { color: "white", width: 0.5 },
                  },
                  hovertemplate: "<b>%{text}</b><br>g1: %{x}<br>g2: %{y}<br>LL: %{z:.1f}<extra>%{fullData.name}</extra>",
                };
              })}
              layout={{
                height: 600,
                scene: {
                  xaxis: { title: { text: "Gene 1" } },
                  yaxis: { title: { text: "Gene 2" } },
                  zaxis: { title: { text: "Log-Likelihood" } },
                  camera: { eye: { x: 1.5, y: 1.5, z: 0.8 } },
                },
                legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
              }}
            />
          </ChartCard>
        )}

        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Fitted Gene Values</h2>
          <DataTable
            data={data as unknown as Record<string, unknown>[]}
            columns={tableColumns as ColumnDef<Record<string, unknown>, unknown>[]}
            downloadFilename="fitted_genes.csv"
          />
        </div>
      </div>
    </div>
  );
}
