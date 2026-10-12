interface NoDataProps {
  title?: string;
  message?: string;
}

export function NoData({
  title = "Data Not Available",
  message = "This analysis has not been generated yet. Run the analysis pipeline to populate this view.",
}: NoDataProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-neutral-800 flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-slate-400 dark:text-neutral-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-slate-700 dark:text-neutral-300 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 dark:text-neutral-400 text-center max-w-md">{message}</p>
    </div>
  );
}
