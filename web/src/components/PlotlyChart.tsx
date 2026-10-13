import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import type { Data, Layout as PlotlyLayout, Config } from "plotly.js-dist-min";
import { PLOTLY_LAYOUT, PLOTLY_CONFIG, PLOTLY_LAYOUT_DARK } from "../lib/colors";
import { useTheme } from "../lib/theme";
import { useResponsivePlotlyOverrides, useIsMobile } from "../lib/responsive";

const Plot = createPlotlyComponent(Plotly);

interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<PlotlyLayout>;
  config?: Partial<Config>;
  className?: string;
}

export function PlotlyChart({ data, layout = {}, config = {}, className }: PlotlyChartProps) {
  const { theme } = useTheme();
  const base = theme === "dark" ? PLOTLY_LAYOUT_DARK : PLOTLY_LAYOUT;
  const mobileOverrides = useResponsivePlotlyOverrides();
  const isMobile = useIsMobile();

  const mergedLayout: Partial<PlotlyLayout> = {
    ...base,
    ...(mobileOverrides as Partial<PlotlyLayout>),
    ...layout,
    margin: {
      ...base.margin,
      ...((mobileOverrides as Partial<PlotlyLayout>).margin ?? {}),
      ...(layout.margin ?? {}),
    },
  };

  const mergedConfig: Partial<Config> = {
    ...PLOTLY_CONFIG,
    ...config,
    displayModeBar: isMobile ? "hover" : (config.displayModeBar ?? PLOTLY_CONFIG.displayModeBar),
  };

  return (
    <div className={className}>
      <Plot
        data={data as unknown as Plotly.Data[]}
        layout={mergedLayout as unknown as Plotly.Layout}
        config={mergedConfig as unknown as Plotly.Config}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
