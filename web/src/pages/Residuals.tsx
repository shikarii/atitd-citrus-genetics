import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { NoData } from "../components/NoData";
import {
  loadResiduals,
  loadSiblingCorrelations,
  type ResidualEntry,
  type SiblingCorrelation,
  TRAITS,
} from "../lib/data";
import { CHART_COLORS } from "../lib/colors";

export function Residuals() {
  const [residuals, setResiduals] = useState<ResidualEntry[]>([]);
  const [sibCorr, setSibCorr] = useState<SiblingCorrelation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      loadResiduals().then(setResiduals).catch(() => {}),
      loadSiblingCorrelations().then(setSibCorr).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const traitResiduals = TRAITS.map((t) => ({
    trait: t,
    values: residuals.map((r) => r[`${t}_residual` as keyof ResidualEntry] as number),
  }));

  const meanAbsResiduals = traitResiduals.map((tr) => {
    if (tr.values.length === 0) return 0;
    return tr.values.reduce((s, v) => s + Math.abs(v), 0) / tr.values.length;
  });

  const overallMeanAbs = meanAbsResiduals.length > 0
    ? meanAbsResiduals.reduce((a, b) => a + b, 0) / meanAbsResiduals.length
    : 0;

  const nSigCorr = sibCorr.filter((s) => s.p_value < 0.05).length;

  if (!loading && residuals.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">Residual Analysis</h1>
        <NoData />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Residual Analysis</h1>
      <p className="text-sm text-slate-500 mb-6">
        Residuals (observed - CLAIM predicted) per child per trait.
        Residuals near zero with no systematic pattern confirm model adequacy.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Observations" value={residuals.length || "..."} />
        <MetricCard label="Mean |Residual|" value={overallMeanAbs.toFixed(1)} />
        <MetricCard label="Sibling Correlations" value={sibCorr.length || "..."} />
        <MetricCard label="Significant (p<0.05)" value={nSigCorr} detail="Sibling correlations" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Residual Distributions by Trait"
          subtitle="Histograms should be centered near zero with symmetric tails"
        >
          <PlotlyChart
            data={traitResiduals.map((tr, i) => ({
              x: tr.values,
              type: "histogram" as const,
              name: tr.trait,
              opacity: 0.7,
              marker: { color: CHART_COLORS[i] },
              nbinsx: 30,
            }))}
            layout={{
              height: 400,
              barmode: "overlay",
              xaxis: { title: { text: "Residual (observed - predicted)" } },
              yaxis: { title: { text: "Count" } },
            }}
          />
        </ChartCard>

        <ChartCard
          title="Residuals by Trait (Box Plots)"
          subtitle="Box centered at zero indicates unbiased predictions"
        >
          <PlotlyChart
            data={traitResiduals.map((tr, i) => ({
              y: tr.values,
              type: "box" as const,
              name: tr.trait,
              marker: { color: CHART_COLORS[i] },
              boxpoints: "outliers" as const,
            }))}
            layout={{
              height: 400,
              yaxis: { title: { text: "Residual" } },
              shapes: [
                { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#334155" } },
              ],
            }}
          />
        </ChartCard>

        {sibCorr.length > 0 && (
          <ChartCard
            title="Sibling Correlations"
            subtitle="Pearson r between siblings' residuals within each litter; significant values suggest unmodeled structure"
          >
            <PlotlyChart
              data={TRAITS.map((trait, i) => {
                const entries = sibCorr.filter((s) => s.trait === trait);
                return {
                  x: entries.map((s) => s.litter),
                  y: entries.map((s) => s.pearson_r),
                  type: "bar" as const,
                  name: trait,
                  marker: { color: CHART_COLORS[i] },
                };
              })}
              layout={{
                height: 400,
                barmode: "group",
                xaxis: { title: { text: "Litter" }, tickangle: -45 },
                yaxis: { title: { text: "Pearson r" }, range: [-1, 1] },
                shapes: [
                  { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: "#334155" } },
                ],
              }}
            />
          </ChartCard>
        )}
      </div>
    </div>
  );
}
