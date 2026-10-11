import { useEffect, useRef } from "react";
import { renderMarkdown, postProcessDom } from "../lib/markdown";

interface MarkdownViewerProps {
  markdown: string;
  sanitize?: boolean;
  onRendered?: (el: HTMLElement) => void;
}

export function MarkdownViewer({ markdown, sanitize, onRendered }: MarkdownViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const { html, placeholders } = renderMarkdown(markdown, {
      sanitize: sanitize === true,
    });
    el.innerHTML = html;
    postProcessDom(el, placeholders);
    onRendered?.(el);
  }, [markdown, sanitize, onRendered]);

  return <div ref={containerRef} className="prose-research text-slate-700 leading-relaxed" />;
}
