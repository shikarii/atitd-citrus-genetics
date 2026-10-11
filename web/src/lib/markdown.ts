/** Markdown rendering pipeline: marked + KaTeX + Prism + Mermaid + DOMPurify. */

import { marked } from "marked";
import DOMPurify from "dompurify";
import katex from "katex";
import Prism from "prismjs";

interface MathPlaceholder {
  type: "display" | "inline";
  math: string;
}

export interface RenderOptions {
  sanitize?: boolean;
}

export interface PostProcessOptions {
  mermaid?: boolean;
}

const SANITIZE_TAGS = [
  "svg", "path", "line", "circle", "rect", "polygon", "polyline", "ellipse",
  "g", "defs", "marker", "text", "tspan", "foreignObject", "use", "clipPath",
  "linearGradient", "radialGradient", "stop", "style", "title", "desc",
  "annotation", "math", "semantics", "mrow", "mi", "mn", "mo", "msup",
  "msub", "mfrac", "mover", "munder",
];

const SANITIZE_ATTRS = [
  "viewBox", "xmlns", "d", "fill", "stroke", "stroke-width", "stroke-dasharray",
  "stroke-linecap", "stroke-linejoin", "transform", "x", "y", "x1", "y1",
  "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "points",
  "marker-end", "marker-start", "font-size", "font-family", "text-anchor",
  "dominant-baseline", "opacity", "id", "style", "class",
];

const PLACEHOLDER_RE = /MATHPLACEHOLDER(\d+)END/;

function extractMathPlaceholders(md: string): {
  processed: string;
  placeholders: MathPlaceholder[];
} {
  const placeholders: MathPlaceholder[] = [];
  let processed = md;

  // Display math: $$...$$
  processed = processed.replace(
    /\$\$((?:(?!\$\$)[\s\S])*?)\$\$/g,
    (_match: string, math: string): string => {
      const idx = placeholders.length;
      placeholders.push({ type: "display", math: math.trim() });
      return `MATHPLACEHOLDER${String(idx)}END`;
    },
  );

  // Inline math: $...$
  processed = processed.replace(
    /\$([^\n$]+?)\$/g,
    (_match: string, math: string): string => {
      const idx = placeholders.length;
      placeholders.push({ type: "inline", math: math.trim() });
      return `MATHPLACEHOLDER${String(idx)}END`;
    },
  );

  return { processed, placeholders };
}

function addHtmlEnhancements(html: string): string {
  return html.replace(
    /<pre><code class="language-(\w+)">([\s\S]*?)<\/code><\/pre>/g,
    (_m: string, lang: string, code: string): string =>
      `<div class="code-wrapper"><span class="code-lang">${lang}</span><pre><code class="language-${lang}">${code}</code></pre></div>`,
  );
}

export function renderMarkdown(
  md: string,
  opts: RenderOptions = {},
): {
  html: string;
  placeholders: MathPlaceholder[];
} {
  marked.setOptions({ breaks: false, gfm: true });

  const { processed, placeholders } = extractMathPlaceholders(md);
  let html = marked.parse(processed) as string;
  html = addHtmlEnhancements(html);

  if (opts.sanitize === true) {
    html = DOMPurify.sanitize(html, {
      ADD_TAGS: SANITIZE_TAGS,
      ADD_ATTR: SANITIZE_ATTRS,
      ALLOW_DATA_ATTR: true,
    });
  }

  return { html, placeholders };
}

function renderMathSpan(ph: MathPlaceholder): HTMLElement {
  const span = document.createElement(ph.type === "display" ? "div" : "span");
  try {
    katex.render(ph.math, span, {
      displayMode: ph.type === "display",
      throwOnError: false,
      trust: false,
    });
  } catch {
    span.textContent = ph.type === "display" ? `$$${ph.math}$$` : `$${ph.math}$`;
    span.style.color = "#e07070";
  }
  return span;
}

function restoreMath(container: HTMLElement, placeholders: MathPlaceholder[]): void {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  const replacements: Text[] = [];
  let node = walker.nextNode() as Text | null;
  while (node) {
    if (node.data.includes("MATHPLACEHOLDER")) {
      replacements.push(node);
    }
    node = walker.nextNode() as Text | null;
  }

  replacements.forEach((textNode) => {
    const parts = textNode.data.split(/(MATHPLACEHOLDER\d+END)/);
    if (parts.length < 2) return;
    const frag = document.createDocumentFragment();
    parts.forEach((part) => {
      const m = PLACEHOLDER_RE.exec(part);
      if (m) {
        const ph = placeholders[Number(m[1])];
        if (!ph) {
          frag.appendChild(document.createTextNode(part));
          return;
        }
        frag.appendChild(renderMathSpan(ph));
      } else {
        frag.appendChild(document.createTextNode(part));
      }
    });
    textNode.parentNode?.replaceChild(frag, textNode);
  });
}

function highlightCode(container: HTMLElement): void {
  Prism.highlightAllUnder(container);
}

let mermaidCounter = 0;

async function renderMermaidBlocks(container: HTMLElement): Promise<void> {
  const blocks = container.querySelectorAll<HTMLElement>("code.language-mermaid");
  if (blocks.length === 0) return;

  const mermaid = (await import("mermaid")).default;
  mermaid.initialize({
    startOnLoad: false,
    theme: "base",
    themeVariables: {
      primaryColor: "#CCFBF1",
      primaryTextColor: "#134E4A",
      primaryBorderColor: "#0D9488",
      lineColor: "#94A3B8",
      secondaryColor: "#F1F5F9",
      tertiaryColor: "#F0FDFA",
      fontFamily: "Inter, system-ui, sans-serif",
      fontSize: "14px",
    },
  });

  for (const codeEl of blocks) {
    const source = codeEl.textContent;
    if (!source) continue;
    const pre = codeEl.closest("pre");
    const wrapper = pre?.closest(".code-wrapper") ?? pre;
    if (!wrapper) continue;

    const id = `mermaid-${++mermaidCounter}`;
    try {
      const { svg } = await mermaid.render(id, source);
      const div = document.createElement("div");
      div.className = "mermaid-container";
      div.innerHTML = svg;
      wrapper.parentNode?.replaceChild(div, wrapper);
    } catch {
      // Gracefully degrade to code block on error
    }
  }
}

export async function postProcessDom(
  container: HTMLElement,
  placeholders: MathPlaceholder[],
  opts: PostProcessOptions = {},
): Promise<void> {
  restoreMath(container, placeholders);
  highlightCode(container);
  if (opts.mermaid !== false) {
    await renderMermaidBlocks(container);
  }
}
