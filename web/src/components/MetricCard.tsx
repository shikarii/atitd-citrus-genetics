interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
}

export function MetricCard({ label, value, detail }: MetricCardProps) {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border border-slate-200 dark:border-neutral-700 p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wider text-slate-400 dark:text-neutral-500 mb-1">
        {label}
      </div>
      <div className="text-2xl font-semibold text-slate-800 dark:text-neutral-100">{value}</div>
      {detail && (
        <div className="text-xs text-slate-500 dark:text-neutral-400 mt-1">{detail}</div>
      )}
    </div>
  );
}
