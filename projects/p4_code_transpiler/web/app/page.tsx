'use client';

import { useRef, useState } from 'react';
import { Cpu, Sparkles, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { CodeEditor } from '@/components/transpiler/code-editor';
import { OptionsPanel, type TranspileOptions } from '@/components/transpiler/options-panel';
import { ResultPanel } from '@/components/transpiler/result-panel';
import { transpile, type TranspileResult } from '@/lib/api';
import { EXAMPLES } from '@/lib/examples';

const DEFAULT_OPTIONS: TranspileOptions = {
  optimizationLevel: 'O2',
  selfCorrection: true,
  maxAttempts: 3,
  runBenchmark: true,
};

export default function TranspilerPage() {
  const [source, setSource] = useState(EXAMPLES[0].source);
  const [exampleId, setExampleId] = useState<string | null>(EXAMPLES[0].id);
  const [options, setOptions] = useState(DEFAULT_OPTIONS);
  const [result, setResult] = useState<TranspileResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const canSubmit = source.trim().length > 0 && !isLoading;

  const handleTranspile = async () => {
    if (!canSubmit) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(
        await transpile(
          {
            source,
            optimization_level: options.optimizationLevel,
            self_correction: options.selfCorrection,
            max_attempts: options.maxAttempts,
            run_benchmark: options.runBenchmark,
          },
          controller.signal
        )
      );
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : 'Transpilation failed.');
    } finally {
      if (abortRef.current === controller) setIsLoading(false);
    }
  };

  return (
    <div className="container py-10">
      {/* Intro */}
      <section className="mb-8">
        <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">
          <Sparkles size={13} /> LLM-assisted · self-correcting · benchmarked
        </span>
        <h1 className="mb-2 text-3xl font-bold tracking-tight md:text-4xl">
          Python → <span className="gradient-text">C++</span> Transpiler
        </h1>
        <p className="max-w-2xl text-slate-400">
          Translate Python into optimized C++, compile it, let the self-correction loop fix any build errors, then
          compare run time against the original.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input */}
        <section className="glass-panel flex flex-col gap-4 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Cpu size={16} className="text-indigo-400" /> Python source
            </h2>
            <div className="flex flex-wrap gap-2" aria-label="Examples">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.id}
                  type="button"
                  title={ex.description}
                  disabled={isLoading}
                  onClick={() => {
                    setSource(ex.source);
                    setExampleId(ex.id);
                  }}
                  className={`rounded-lg border px-3 py-1.5 text-xs transition-colors disabled:opacity-50 ${
                    exampleId === ex.id
                      ? 'border-indigo-500/50 bg-indigo-500/15 text-white'
                      : 'border-white/10 text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  {ex.title}
                </button>
              ))}
            </div>
          </div>

          <CodeEditor
            value={source}
            onChange={(value) => {
              setSource(value);
              setExampleId(null);
            }}
            onSubmit={handleTranspile}
            disabled={isLoading}
          />

          <OptionsPanel options={options} onChange={setOptions} disabled={isLoading} />

          <Button onClick={handleTranspile} isLoading={isLoading} disabled={!canSubmit} className="w-full">
            {!isLoading && <Zap size={18} />}
            {isLoading ? 'Transpiling…' : 'Transpile'}
          </Button>
        </section>

        {/* Output */}
        <ResultPanel result={result} isLoading={isLoading} error={error} />
      </div>
    </div>
  );
}
