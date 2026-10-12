import type { AnalysisInterpretation } from "../lib/data";

interface FindingsSummaryProps {
  interpretation: AnalysisInterpretation | undefined;
}

export function FindingsSummary({ interpretation }: FindingsSummaryProps) {
  if (!interpretation) return null;

  return (
    <div className="bg-teal-50 dark:bg-neutral-800 border border-teal-100 dark:border-neutral-700 rounded-lg px-5 py-4 mb-6">
      <h3 className="text-sm font-semibold text-teal-800 dark:text-neutral-200 uppercase tracking-wide mb-2">
        Data Summary
      </h3>
      <ul className="space-y-1.5">
        {interpretation.findings.map((f, i) => (
          <li key={i} className="text-sm text-slate-700 dark:text-neutral-300 leading-relaxed">
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
