import { NavLink } from "react-router-dom";
import { LITTERS } from "../lib/data";

interface NavItem {
  to: string;
  label: string;
}

const SECTIONS: { heading: string; items: NavItem[] }[] = [
  {
    heading: "",
    items: [
      { to: "/", label: "Abstract" },
      { to: "/methods", label: "Methodology" },
      { to: "/weaknesses", label: "Known Weaknesses" },
    ],
  },
  {
    heading: "Results",
    items: [
      { to: "/results/models", label: "Model Comparison" },
      { to: "/results/mi-matrix", label: "Mutual Information" },
      { to: "/results/anomalies", label: "Anomaly Scores" },
      { to: "/results/residuals", label: "Residual Analysis" },
      { to: "/results/r-sweep", label: "Parameter Sweep" },
      { to: "/results/distribution", label: "Distribution Tests" },
      { to: "/results/mixture", label: "Mixture Models" },
      { to: "/results/genes", label: "Gene Landscape" },
    ],
  },
  {
    heading: "Litters",
    items: LITTERS.map((name) => ({
      to: `/litter/${name}`,
      label: name,
    })),
  },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `block px-3 py-1.5 text-sm rounded-md transition-colors ${
    isActive
      ? "bg-teal-100 text-teal-800 font-medium dark:bg-neutral-700 dark:text-neutral-100"
      : "text-slate-600 hover:bg-slate-100 hover:text-slate-800 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
  }`;

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-slate-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 overflow-y-auto h-screen sticky top-0">
      <div className="px-4 py-5 border-b border-slate-200 dark:border-neutral-700">
        <NavLink to="/" className="text-teal-800 dark:text-neutral-100 font-semibold text-base leading-tight block">
          ATITD Citrus Genetics
        </NavLink>
        <span className="text-xs text-slate-400 dark:text-neutral-500 mt-1 block">Research Dashboard</span>
      </div>

      <nav className="p-3 space-y-4">
        {SECTIONS.map((section, si) => (
          <div key={si}>
            {section.heading && (
              <h3 className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-neutral-500">
                {section.heading}
              </h3>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink key={item.to} to={item.to} className={linkClass} end={item.to === "/"}>
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
