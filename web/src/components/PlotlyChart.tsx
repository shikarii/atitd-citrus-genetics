import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import type { Data, Layout as PlotlyLayout, Config } from "plotly.js-dist-min";
import { PLOTLY_LAYOUT, PLOTLY_CONFIG } from "../lib/colors";

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- plotly.js-dist-min v4 types diverge from @types/react-plotly.js
const Plot = createPlotlyComponent(Plotly as any);

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
        data={data as any}
        layout={mergedLayout as any}
        config={mergedConfig as any}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
