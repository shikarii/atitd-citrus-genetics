import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { useTheme } from "../lib/theme";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { theme, toggle } = useTheme();

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-neutral-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-12 border-b border-slate-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 flex items-center justify-between px-6 shrink-0">
          <span className="text-sm text-slate-500 dark:text-neutral-400">
            Reverse-Engineering Citrus Breeding Mechanics
          </span>
          <div className="flex items-center gap-4">
            <button
              onClick={toggle}
              className="text-sm text-slate-500 dark:text-neutral-400 hover:text-slate-700 dark:hover:text-neutral-200 transition-colors"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <a
              href="https://github.com/shikarii/atitd-citrus-genetics"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-500 dark:text-neutral-400 hover:text-teal-600 dark:hover:text-neutral-200 transition-colors"
            >
              GitHub
            </a>
          </div>
        </header>
        <main className="flex-1 p-6 lg:p-8 max-w-[1200px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
