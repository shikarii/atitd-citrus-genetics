import { useCallback, useEffect, useState } from "react";
import { MarkdownViewer } from "../components/MarkdownViewer";
import { TableOfContents } from "../components/TableOfContents";
import { loadMethodology } from "../lib/data";

export function Methods() {
  const [md, setMd] = useState<string | null>(null);
  const [contentEl, setContentEl] = useState<HTMLElement | null>(null);

  useEffect(() => {
    loadMethodology().then(setMd).catch(() => setMd("*Failed to load methodology document.*"));
  }, []);

  const handleRendered = useCallback((el: HTMLElement) => {
    setContentEl(el);
  }, []);

  if (md === null) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading methodology...</div>
      </div>
    );
  }

  return (
    <div className="flex gap-8">
      <article className="flex-1 min-w-0">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">Methodology</h1>
        <p className="text-sm text-slate-500 mb-6">
          Full research methodology with mathematical formulations
        </p>
        <MarkdownViewer markdown={md} sanitize onRendered={handleRendered} />
      </article>
      <aside className="hidden xl:block w-56 shrink-0">
        <div className="sticky top-20">
          <TableOfContents contentEl={contentEl} />
        </div>
      </aside>
    </div>
  );
}
