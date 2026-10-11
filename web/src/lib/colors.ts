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

import type { Layout as PlotlyLayout, Config } from "plotly.js";

/** Plotly layout defaults for consistent styling. */
export const PLOTLY_LAYOUT: Partial<PlotlyLayout> = {
  font: { family: "Inter, system-ui, sans-serif", color: SLATE[700] },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  margin: { l: 60, r: 20, t: 40, b: 50 },
  xaxis: { gridcolor: SLATE[200], zerolinecolor: SLATE[300] },
  yaxis: { gridcolor: SLATE[200], zerolinecolor: SLATE[300] },
  colorway: [...CHART_COLORS] as string[],
};

export const PLOTLY_CONFIG: Partial<Config> = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d"],
  responsive: true,
};
