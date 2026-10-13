import type { ReactNode } from "react";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  description?: string;
  children: ReactNode;
}

export function ChartCard({ title, subtitle, description, children }: ChartCardProps) {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border border-slate-200 dark:border-neutral-700 shadow-sm overflow-hidden">
      <div className="px-3 pt-3 pb-1.5 sm:px-5 sm:pt-4 sm:pb-2">
        <h3 className="text-base font-semibold text-slate-800 dark:text-neutral-100">{title}</h3>
        {subtitle && (
          <p className="text-sm text-slate-500 dark:text-neutral-400 mt-0.5">{subtitle}</p>
        )}
        {description && (
          <p className="text-sm text-slate-600 dark:text-neutral-400 mt-2 leading-relaxed">{description}</p>
        )}
      </div>
      <div className="px-1 pb-2 sm:px-2 sm:pb-3">{children}</div>
    </div>
  );
}
