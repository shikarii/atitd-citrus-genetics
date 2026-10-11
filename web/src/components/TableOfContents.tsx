import { useEffect, useRef, useState } from "react";

interface TOCItem {
  id: string;
  text: string;
  level: string;
}

interface TableOfContentsProps {
  contentEl: HTMLElement | null;
}

export function TableOfContents({ contentEl }: TableOfContentsProps) {
  const [items, setItems] = useState<TOCItem[]>([]);
  const [activeId, setActiveId] = useState("");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    if (!contentEl) return;

    const headings = contentEl.querySelectorAll<HTMLElement>("h1, h2, h3");
    const tocItems: TOCItem[] = [];
    headings.forEach((h, i) => {
      if (!h.id) {
        h.id = `h-${String(i)}-${(h.textContent ?? "")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "")}`;
      }
      tocItems.push({
        id: h.id,
        text: h.textContent ?? "",
        level: h.tagName.toLowerCase(),
      });
    });
    setItems(tocItems);

    observerRef.current?.disconnect();
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: "-10% 0px -80% 0px" },
    );
    observerRef.current = observer;
    headings.forEach((h) => observer.observe(h));

    return () => observer.disconnect();
  }, [contentEl]);

  if (items.length === 0) return null;

  return (
    <nav className="space-y-0.5">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-3">
        On this page
      </h4>
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => {
            document.getElementById(item.id)?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }}
          className={`block w-full text-left text-sm py-1 border-l-2 transition-colors ${
            activeId === item.id
              ? "border-teal-500 text-teal-700 font-medium"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
          style={{
            paddingLeft: item.level === "h1" ? 12 : item.level === "h2" ? 20 : 32,
          }}
        >
          {item.text}
        </button>
      ))}
    </nav>
  );
}
