/** Split-complementary teal palette with cool-tinted greyscale. */

export const TEAL = {
  50: "#F0FDFA",
  100: "#CCFBF1",
  200: "#99F6E4",
  300: "#5EEAD4",
  400: "#2DD4BF",
  500: "#14B8A6",
  600: "#0D9488",
  700: "#0F766E",
  800: "#115E59",
  900: "#134E4A",
} as const;

export const SLATE = {
  50: "#F8FAFC",
  100: "#F1F5F9",
  200: "#E2E8F0",
  300: "#CBD5E1",
  400: "#94A3B8",
  500: "#64748B",
  700: "#334155",
  800: "#1E293B",
  900: "#0F172A",
} as const;

export const ACCENT = {
  coral: "#EF4444",
  amber: "#F59E0B",
  indigo: "#6366F1",
  emerald: "#10B981",
  violet: "#8B5CF6",
  pink: "#EC4899",
} as const;

/** Ordered chart color sequence for multi-series data. */
export const CHART_COLORS = [
  TEAL[600],
  ACCENT.indigo,
  ACCENT.amber,
  ACCENT.coral,
  ACCENT.violet,
  ACCENT.pink,
  TEAL[500],
  SLATE[500],
] as const;

import type { Layout as PlotlyLayout, Config } from "plotly.js-dist-min";

/** Academic-style Plotly layout defaults. */
export const PLOTLY_LAYOUT: Partial<PlotlyLayout> = {
  font: {
    family: "'Inter', 'Helvetica Neue', Arial, sans-serif",
    color: SLATE[700],
    size: 12,
  },
  paper_bgcolor: "white",
  plot_bgcolor: "white",
  margin: { l: 65, r: 30, t: 50, b: 60 },
  xaxis: {
    gridcolor: SLATE[200],
    zerolinecolor: SLATE[300],
    linecolor: SLATE[300],
    linewidth: 1,
    showline: true,
    ticks: "outside",
    tickcolor: SLATE[300],
    ticklen: 4,
    title: { font: { size: 13, color: SLATE[700] } },
    tickfont: { size: 11 },
  },
  yaxis: {
    gridcolor: SLATE[200],
    zerolinecolor: SLATE[300],
    linecolor: SLATE[300],
    linewidth: 1,
    showline: true,
    ticks: "outside",
    tickcolor: SLATE[300],
    ticklen: 4,
    title: { font: { size: 13, color: SLATE[700] } },
    tickfont: { size: 11 },
  },
  colorway: [...CHART_COLORS] as string[],
  legend: {
    font: { size: 11 },
    bgcolor: "rgba(255,255,255,0.9)",
    bordercolor: SLATE[200],
    borderwidth: 1,
  },
  title: {
    font: { size: 14, color: SLATE[800] },
    x: 0.02,
    xanchor: "left",
  },
  hoverlabel: {
    bgcolor: "white",
    bordercolor: SLATE[300],
    font: { size: 12, family: "'Inter', sans-serif", color: SLATE[800] },
  },
};

export const PLOTLY_CONFIG: Partial<Config> = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
  responsive: true,
  toImageButtonOptions: {
    format: "svg",
    filename: "citrus-genetics-chart",
    scale: 2,
  },
};
