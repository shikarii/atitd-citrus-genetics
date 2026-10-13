import { useState, useEffect } from "react";

type ChartSize = "sm" | "md" | "lg";

const BP_SM = 640;
const BP_MD = 768;

function getSize(): ChartSize {
  if (typeof window === "undefined") return "lg";
  if (window.innerWidth < BP_SM) return "sm";
  if (window.innerWidth < BP_MD) return "md";
  return "lg";
}

/**
 * Returns a viewport-aware chart height.
 * Mobile (< 640px): 65% of desktop. Tablet (640-767px): 85%. Desktop: full.
 */
export function useResponsiveChartHeight(
  desktopHeight: number,
  opts?: { mobileRatio?: number; tabletRatio?: number },
): number {
  const mobileRatio = opts?.mobileRatio ?? 0.65;
  const tabletRatio = opts?.tabletRatio ?? 0.85;
  const [size, setSize] = useState<ChartSize>(getSize);

  useEffect(() => {
    const handler = () => { setSize(getSize()); };
    window.addEventListener("resize", handler);
    return () => { window.removeEventListener("resize", handler); };
  }, []);

  if (size === "sm") return Math.round(desktopHeight * mobileRatio);
  if (size === "md") return Math.round(desktopHeight * tabletRatio);
  return desktopHeight;
}

/**
 * Returns Plotly layout overrides for mobile: smaller fonts, tighter margins,
 * rotated x-axis labels. Returns empty object on desktop.
 */
export function useResponsivePlotlyOverrides(): Record<string, unknown> {
  const mobile = useIsMobile();
  if (!mobile) return {};
  return {
    font: { size: 10 },
    margin: { l: 45, r: 15, t: 35, b: 50 },
    xaxis: { tickfont: { size: 9 }, tickangle: -45 },
    yaxis: { tickfont: { size: 9 } },
    legend: { font: { size: 9 } },
  };
}

/** Returns true when viewport width is below the given breakpoint. */
export function useIsMobile(breakpoint: number = BP_SM): boolean {
  const [mobile, setMobile] = useState(
    () => typeof window !== "undefined" && window.innerWidth < breakpoint,
  );

  useEffect(() => {
    const handler = () => { setMobile(window.innerWidth < breakpoint); };
    window.addEventListener("resize", handler);
    return () => { window.removeEventListener("resize", handler); };
  }, [breakpoint]);

  return mobile;
}
