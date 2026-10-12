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
              className="p-1.5 rounded-md text-slate-500 dark:text-neutral-400 hover:bg-slate-100 dark:hover:bg-neutral-700 hover:text-slate-700 dark:hover:text-neutral-200 transition-colors"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              )}
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
