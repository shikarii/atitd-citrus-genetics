interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
}

export function MetricCard({ label, value, detail }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wider text-slate-400 mb-1">
        {label}
      </div>
      <div className="text-2xl font-semibold text-slate-800">{value}</div>
      {detail && (
        <div className="text-xs text-slate-500 mt-1">{detail}</div>
      )}
    </div>
  );
}
