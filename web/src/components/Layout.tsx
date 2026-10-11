import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-12 border-b border-slate-200 bg-white flex items-center justify-between px-6 shrink-0">
          <span className="text-sm text-slate-500">
            Reverse-Engineering Citrus Breeding Mechanics
          </span>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/shikarii/atitd-citrus-genetics"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-500 hover:text-teal-600 transition-colors"
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
