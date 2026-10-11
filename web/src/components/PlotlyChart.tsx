import Plot from "react-plotly.js";
import type { Data, Layout as PlotlyLayout, Config } from "plotly.js";
import { PLOTLY_LAYOUT, PLOTLY_CONFIG } from "../lib/colors";

interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<PlotlyLayout>;
  config?: Partial<Config>;
  className?: string;
}

export function PlotlyChart({ data, layout = {}, config = {}, className }: PlotlyChartProps) {
  const mergedLayout: Partial<PlotlyLayout> = {
    ...PLOTLY_LAYOUT,
    ...layout,
    margin: { ...PLOTLY_LAYOUT.margin, ...(layout.margin ?? {}) },
  };

  const mergedConfig: Partial<Config> = {
    ...PLOTLY_CONFIG,
    ...config,
  };

  return (
    <div className={className}>
      <Plot
        data={data}
        layout={mergedLayout}
        config={mergedConfig}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
