'use client';

import { Gauge, RefreshCcw, Timer } from 'lucide-react';
import type { OptimizationLevel } from '@/lib/api';

export interface TranspileOptions {
  optimizationLevel: OptimizationLevel;
  selfCorrection: boolean;
  maxAttempts: number;
  runBenchmark: boolean;
}

interface OptionsPanelProps {
  options: TranspileOptions;
  onChange: (options: TranspileOptions) => void;
  disabled?: boolean;
}

const LEVELS: OptimizationLevel[] = ['O0', 'O1', 'O2', 'O3'];

function Toggle({
  checked,
  onChange,
  disabled,
  label,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50 ${
        checked ? 'bg-indigo-500' : 'bg-white/10'
      }`}
    >
      <span
        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${checked ? 'left-[22px]' : 'left-0.5'}`}
      />
    </button>
  );
}

export function OptionsPanel({ options, onChange, disabled }: OptionsPanelProps) {
  const set = <K extends keyof TranspileOptions>(key: K, value: TranspileOptions[K]) =>
    onChange({ ...options, [key]: value });

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {/* Optimization level */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Gauge size={16} className="text-cyan-400" /> Optimization
        </div>
        <div className="flex rounded-lg border border-white/10 bg-black/20 p-0.5" role="radiogroup" aria-label="Optimization level">
          {LEVELS.map((level) => (
            <button
              key={level}
              type="button"
              role="radio"
              aria-checked={options.optimizationLevel === level}
              disabled={disabled}
              onClick={() => set('optimizationLevel', level)}
              className={`flex-1 rounded-md py-1.5 font-mono text-xs transition-colors ${
                options.optimizationLevel === level
                  ? 'bg-indigo-500/30 font-semibold text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              -{level}
            </button>
          ))}
        </div>
      </div>

      {/* Self-correction loop */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <RefreshCcw size={16} className="text-violet-400" /> Self-correction
          </span>
          <Toggle
            label="Self-correction"
            checked={options.selfCorrection}
            disabled={disabled}
            onChange={(v) => set('selfCorrection', v)}
          />
        </div>
        <label className="flex items-center justify-between text-xs text-slate-400">
          Max attempts
          <input
            type="number"
            min={1}
            max={10}
            value={options.maxAttempts}
            disabled={disabled || !options.selfCorrection}
            onChange={(e) => set('maxAttempts', Math.min(10, Math.max(1, Number(e.target.value) || 1)))}
            className="w-16 rounded-md border border-white/10 bg-black/30 px-2 py-1 text-right font-mono text-slate-100 outline-none focus:border-indigo-500 disabled:opacity-50"
          />
        </label>
      </div>

      {/* Benchmark */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Timer size={16} className="text-emerald-400" /> Benchmark
          </span>
          <Toggle
            label="Run benchmark"
            checked={options.runBenchmark}
            disabled={disabled}
            onChange={(v) => set('runBenchmark', v)}
          />
        </div>
        <p className="text-xs text-slate-400">Time Python vs compiled C++ and verify identical output.</p>
      </div>
    </div>
  );
}
