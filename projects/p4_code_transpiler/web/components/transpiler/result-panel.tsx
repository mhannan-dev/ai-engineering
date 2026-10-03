'use client';

import { useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Copy,
  Download,
  FileCode2,
  Loader2,
  RefreshCcw,
  Terminal,
  Timer,
  XCircle,
} from 'lucide-react';
import type { TranspileResult } from '@/lib/api';
import { highlightCpp } from '@/lib/prism';

type Tab = 'cpp' | 'run' | 'correction' | 'benchmark';

interface ResultPanelProps {
  result: TranspileResult | null;
  isLoading: boolean;
  error: string | null;
}

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'cpp', label: 'C++ Output', icon: <FileCode2 size={15} /> },
  { id: 'run', label: 'Execution', icon: <Terminal size={15} /> },
  { id: 'correction', label: 'Self-Correction', icon: <RefreshCcw size={15} /> },
  { id: 'benchmark', label: 'Benchmark', icon: <Timer size={15} /> },
];

const formatMs = (ms: number) => (ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${ms.toFixed(1)} ms`);

export function ResultPanel({ result, isLoading, error }: ResultPanelProps) {
  const [tab, setTab] = useState<Tab>('cpp');

  return (
    <div className="glass-panel flex h-full min-h-[560px] flex-col overflow-hidden">
      <div className="flex gap-1 overflow-x-auto border-b border-white/10 p-2" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition-colors ${
              tab === t.id ? 'bg-indigo-500/25 font-semibold text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
        {result && (
          <span
            className={`ml-auto flex shrink-0 items-center gap-1.5 self-center px-2 text-xs font-semibold ${
              result.compiled ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {result.compiled ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
            {result.compiled ? 'Compiled' : 'Compile failed'}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4" role="tabpanel">
        {isLoading ? (
          <Placeholder icon={<Loader2 className="animate-spin" size={28} />}>
            Transpiling, compiling and running…
          </Placeholder>
        ) : error ? (
          <div className="flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
            <AlertCircle size={18} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        ) : !result ? (
          <Placeholder icon={<FileCode2 size={28} />}>
            Write or pick a Python program, then press <kbd className="rounded bg-white/10 px-1.5 font-mono text-xs">Ctrl</kbd>{' '}
            + <kbd className="rounded bg-white/10 px-1.5 font-mono text-xs">Enter</kbd> or <b>Transpile</b>.
          </Placeholder>
        ) : tab === 'cpp' ? (
          <CppView code={result.cpp_code} />
        ) : tab === 'run' ? (
          <RunView result={result} />
        ) : tab === 'correction' ? (
          <CorrectionView result={result} />
        ) : (
          <BenchmarkView result={result} />
        )}
      </div>
    </div>
  );
}

function Placeholder({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center gap-3 text-center text-sm text-slate-400">
      <span className="text-slate-500">{icon}</span>
      <p className="max-w-xs">{children}</p>
    </div>
  );
}

function CppView({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  const gutterRef = useRef<HTMLDivElement>(null);

  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const download = () => {
    const url = URL.createObjectURL(new Blob([code], { type: 'text/x-c++src' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: 'transpiled.cpp' });
    a.click();
    URL.revokeObjectURL(url);
  };

  const highlightedHtml = useMemo(() => {
    return highlightCpp(code || '// (empty)');
  }, [code]);

  const lineCount = (code || '// (empty)').split('\n').length;

  const handleScroll = (e: React.UIEvent<HTMLPreElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">
          Target: <span className="font-mono text-indigo-300">C++20</span> (OpenMP + SIMD)
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={copy}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
          >
            {copied ? <CheckCircle2 size={14} className="text-emerald-400" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            type="button"
            onClick={download}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/5"
          >
            <Download size={14} /> .cpp
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden rounded-xl border border-white/10 bg-[#0b0f17] font-mono text-[13px] leading-6">
        {/* Line Numbers Gutter (extra bottom padding so it can follow the code past its scrollbar) */}
        <div
          ref={gutterRef}
          aria-hidden
          className="select-none overflow-hidden border-r border-white/5 px-3 pt-3 pb-12 text-right text-slate-600"
        >
          {Array.from({ length: lineCount }, (_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Highlighted C++ Code */}
        <pre
          onScroll={handleScroll}
          className="flex-1 overflow-auto p-3 text-slate-100 selection:bg-indigo-500/30"
        >
          <code
            className="language-cpp"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        </pre>
      </div>
    </div>
  );
}

function OutputBlock({ label, text, tone }: { label: string; text: string; tone: 'default' | 'error' }) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <pre
        className={`max-h-64 overflow-auto rounded-xl border bg-[#0b0f17] p-3 font-mono text-[13px] leading-6 ${
          tone === 'error' ? 'border-rose-500/20 text-rose-300' : 'border-white/10 text-slate-100'
        }`}
      >
        {text || <span className="text-slate-600">(no output)</span>}
      </pre>
    </div>
  );
}

function RunView({ result }: { result: TranspileResult }) {
  if (!result.run) {
    return (
      <Placeholder icon={<Terminal size={28} />}>
        {result.compiled ? 'The program was not executed.' : 'Nothing to run: the C++ code did not compile.'}
      </Placeholder>
    );
  }
  const { stdout, stderr, exit_code, duration_ms } = result.run;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-3 text-sm">
        <Stat label="Exit code" value={String(exit_code)} tone={exit_code === 0 ? 'good' : 'bad'} />
        <Stat label="Run time" value={formatMs(duration_ms)} />
      </div>
      <OutputBlock label="stdout" text={stdout} tone="default" />
      <OutputBlock label="stderr" text={stderr} tone="error" />
    </div>
  );
}

function CorrectionView({ result }: { result: TranspileResult }) {
  if (result.attempts.length === 0) {
    return (
      <Placeholder icon={<CheckCircle2 size={28} className="text-emerald-400" />}>
        Compiled on the first try. No corrections were needed.
      </Placeholder>
    );
  }
  return (
    <ol className="flex flex-col gap-3">
      {result.attempts.map((a) => (
        <li key={a.attempt} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-semibold text-slate-200">Attempt {a.attempt}</span>
            <span className={`flex items-center gap-1 text-xs font-semibold ${a.fixed ? 'text-emerald-400' : 'text-amber-400'}`}>
              {a.fixed ? <CheckCircle2 size={14} /> : <RefreshCcw size={14} />}
              {a.fixed ? 'Fixed' : 'Not fixed'}
            </span>
          </div>
          <pre className="max-h-48 overflow-auto rounded-lg bg-[#0b0f17] p-3 font-mono text-xs leading-5 text-rose-300">
            {a.compiler_errors}
          </pre>
        </li>
      ))}
    </ol>
  );
}

function BenchmarkView({ result }: { result: TranspileResult }) {
  const b = result.benchmark;
  if (!b) {
    return (
      <Placeholder icon={<Timer size={28} />}>
        No benchmark for this run. Turn on <b>Benchmark</b> and transpile again.
      </Placeholder>
    );
  }
  const max = Math.max(b.python_ms, b.cpp_ms) || 1;
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap gap-3">
        <Stat label="Speedup" value={`${b.speedup.toFixed(1)}×`} tone={b.speedup >= 1 ? 'good' : 'bad'} large />
        <Stat label="Outputs match" value={b.outputs_match ? 'Yes' : 'No'} tone={b.outputs_match ? 'good' : 'bad'} large />
      </div>
      {[
        { label: 'Python', ms: b.python_ms, bar: 'bg-amber-400/80' },
        { label: 'C++', ms: b.cpp_ms, bar: 'bg-gradient-to-r from-indigo-500 to-cyan-400' },
      ].map((row) => (
        <div key={row.label}>
          <div className="mb-1.5 flex justify-between text-sm">
            <span className="text-slate-300">{row.label}</span>
            <span className="font-mono text-slate-100">{formatMs(row.ms)}</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/5">
            <div className={`h-full rounded-full ${row.bar}`} style={{ width: `${Math.max(1, (row.ms / max) * 100)}%` }} />
          </div>
        </div>
      ))}
      {!b.outputs_match && (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-300">
          The C++ program printed something different from the Python original, so the speedup may not be meaningful.
        </p>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = 'default',
  large,
}: {
  label: string;
  value: string;
  tone?: 'default' | 'good' | 'bad';
  large?: boolean;
}) {
  const color = tone === 'good' ? 'text-emerald-400' : tone === 'bad' ? 'text-rose-400' : 'text-slate-100';
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`font-mono font-semibold ${color} ${large ? 'text-2xl' : 'text-base'}`}>{value}</p>
    </div>
  );
}
