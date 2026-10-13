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
  `flex items-center px-3 py-2.5 min-h-[44px] text-sm rounded-md transition-colors ${
    isActive
      ? "bg-teal-100 text-teal-800 font-medium dark:bg-neutral-700 dark:text-neutral-100"
      : "text-slate-600 hover:bg-slate-100 hover:text-slate-800 dark:text-neutral-400 dark:hover:bg-neutral-700 dark:hover:text-neutral-200"
  }`;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-60 border-r border-slate-200
          dark:border-neutral-700 bg-white dark:bg-neutral-800
          overflow-y-auto transition-transform duration-200 ease-in-out
          lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 lg:shrink-0
          ${open ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="px-4 py-5 border-b border-slate-200 dark:border-neutral-700 flex items-center justify-between">
          <div>
            <NavLink
              to="/"
              onClick={onClose}
              className="text-teal-800 dark:text-neutral-100 font-semibold text-base leading-tight block"
            >
              ATITD Citrus Genetics
            </NavLink>
            <span className="text-xs text-slate-400 dark:text-neutral-500 mt-1 block">
              Research Dashboard
            </span>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-2.5 rounded-md text-slate-400 hover:text-slate-600 dark:text-neutral-500 dark:hover:text-neutral-300"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={linkClass}
                    end={item.to === "/"}
                    onClick={onClose}
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
