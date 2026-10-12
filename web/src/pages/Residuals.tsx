import { useEffect, useState } from "react";
import { MetricCard } from "../components/MetricCard";
import { ChartCard } from "../components/ChartCard";
import { PlotlyChart } from "../components/PlotlyChart";
import { NoData } from "../components/NoData";
import {
  loadResiduals,
  loadSiblingCorrelations,
  loadInterpretations,
  type ResidualEntry,
  type SiblingCorrelation,
  type Interpretations,
  TRAITS,
} from "../lib/data";
import { FindingsSummary } from "../components/FindingsSummary";
import { CHART_COLORS, SLATE, ACCENT } from "../lib/colors";

export function Residuals() {
  const [residuals, setResiduals] = useState<ResidualEntry[]>([]);
  const [sibCorr, setSibCorr] = useState<SiblingCorrelation[]>([]);
  const [interps, setInterps] = useState<Interpretations>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([
      loadResiduals().then(setResiduals).catch(() => undefined),
      loadSiblingCorrelations().then(setSibCorr).catch(() => undefined),
    ]).finally(() => { setLoading(false); });
    void loadInterpretations().then(setInterps).catch(() => undefined);
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

      <div className="prose-research text-slate-700 max-w-3xl mb-8 text-sm leading-relaxed space-y-2">
        <p>
          Residual analysis tests whether CLAIM's predictions are systematically biased. For each child and
          trait, we compute the difference between the observed trait value and the model's expected value
          given the MLE-fitted parent genes. If the model is correct, residuals should be centered at zero,
          symmetrically distributed, and uncorrelated between siblings within the same litter. Systematic
          patterns — such as residuals consistently positive for one trait, or correlated between siblings —
          would indicate missing structure that CLAIM fails to capture.
        </p>
      </div>

      <FindingsSummary interpretation={interps.residuals} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Observations" value={residuals.length || "..."} />
        <MetricCard label="Mean |Residual|" value={overallMeanAbs.toFixed(1)} />
        <MetricCard label="Sibling Correlations" value={sibCorr.length || "..."} />
        <MetricCard label="Significant (p<0.05)" value={nSigCorr} detail="Sibling correlations" />
      </div>

      <div className="space-y-6">
        <ChartCard
          title="Residual Distributions by Trait"
          subtitle="Overlaid histograms centered near zero with symmetric tails indicate unbiased predictions"
          description="Each histogram shows the distribution of residuals for one trait across all 692 children. A well-calibrated model produces histograms centered at zero with roughly symmetric tails. Skewness or heavy tails would indicate the model systematically over- or under-predicts certain trait values."
        >
          <PlotlyChart
            data={traitResiduals.map((tr, i) => ({
              x: tr.values,
              type: "histogram" as const,
              name: tr.trait,
              opacity: 0.65,
              marker: {
                color: CHART_COLORS[i],
                line: { color: "rgba(0,0,0,0.08)", width: 0.5 },
              },
              nbinsx: 30,
              hovertemplate: "<b>%{fullData.name}</b><br>Residual: %{x}<br>Count: %{y}<extra></extra>",
            }))}
            layout={{
              height: 420,
              barmode: "overlay",
              xaxis: { title: { text: "Residual (Observed - Predicted)", standoff: 10 } },
              yaxis: { title: { text: "Count", standoff: 10 } },
              legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
              shapes: [
                { type: "line", x0: 0, x1: 0, y0: 0, y1: 1, yref: "paper", line: { dash: "dash", color: SLATE[700], width: 1.5 } },
              ],
              annotations: [
                { x: 0, y: 1.02, yref: "paper", text: "Zero", showarrow: false, font: { size: 10, color: SLATE[500] } },
              ],
            }}
          />
        </ChartCard>

        <ChartCard
          title="Residual Box Plots by Trait"
          subtitle="Median centered at zero indicates unbiased predictions. Outliers shown individually."
          description="Box plots provide a compact summary of each trait's residual distribution: median, interquartile range, and outliers. The median line should sit on zero (no bias). The box width reflects prediction uncertainty — wider boxes mean more variable predictions. Individual outlier points identify children with unusually large residuals."
        >
          <PlotlyChart
            data={traitResiduals.map((tr, i) => ({
              y: tr.values,
              type: "box" as const,
              name: tr.trait,
              marker: { color: CHART_COLORS[i], outliercolor: ACCENT.coral },
              line: { width: 1.5 },
              boxpoints: "outliers" as const,
              hovertemplate: "<b>%{x}</b><br>Residual: %{y:.1f}<extra></extra>",
            }))}
            layout={{
              height: 420,
              yaxis: { title: { text: "Residual", standoff: 10 } },
              shapes: [
                { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { dash: "dash", color: SLATE[700], width: 1.5 } },
              ],
            }}
          />
        </ChartCard>

        {sibCorr.length > 0 && (
          <ChartCard
            title="Sibling Residual Correlations"
            subtitle="Pearson r between siblings' residuals per litter. Significant correlations (p < 0.05) suggest unmodeled structure."
            description="If CLAIM is correct, siblings' residuals should be independent — knowing one sibling's residual should not predict another's. A significant positive correlation would suggest shared environmental effects or gene interactions that CLAIM does not model. Each bar shows the Pearson correlation coefficient between sibling residuals within one litter for one trait."
          >
            <PlotlyChart
              data={TRAITS.map((trait, i) => {
                const entries = sibCorr.filter((s) => s.trait === trait);
                return {
                  x: entries.map((s) => s.litter),
                  y: entries.map((s) => s.pearson_r),
                  type: "bar" as const,
                  name: trait,
                  marker: {
                    color: CHART_COLORS[i],
                    line: { color: "rgba(0,0,0,0.08)", width: 0.5 },
                  },
                  hovertemplate: "<b>%{x}</b><br>Pearson r = %{y:.3f}<extra>%{fullData.name}</extra>",
                };
              })}
              layout={{
                height: 420,
                barmode: "group",
                bargap: 0.2,
                xaxis: { title: { text: "Litter", standoff: 15 }, tickangle: -35, tickfont: { size: 10 } },
                yaxis: { title: { text: "Pearson r", standoff: 10 }, range: [-1, 1] },
                shapes: [
                  { type: "line", y0: 0, y1: 0, x0: 0, x1: 1, xref: "paper", line: { color: SLATE[700], width: 1 } },
                ],
                legend: { x: 0.01, y: 0.99, xanchor: "left", yanchor: "top" },
              }}
            />
          </ChartCard>
        )}
      </div>
    </div>
  );
}
