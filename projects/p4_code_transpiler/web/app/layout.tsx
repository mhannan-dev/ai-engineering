import type { Metadata } from 'next';
import { SiteHeader } from '@/components/site-header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Py2Cpp Transpiler | Python to optimized C++',
  description:
    'LLM-assisted Python to C++ transpiler with a self-correcting compile loop and Python vs C++ benchmarks.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />

        <main className="flex-1">{children}</main>

        <footer className="mt-10 border-t border-white/10 bg-[#0a0d14]/60 py-6">
          <div className="container flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
            <p className="font-semibold text-slate-300">Py2Cpp Transpiler</p>
            <p>Transpile → Optimize → Self-correct → Compile → Benchmark</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
