'use client';

import { useMemo, useRef } from 'react';
import { highlightPython } from '@/lib/prism';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  /** Called on Ctrl/Cmd+Enter. */
  onSubmit?: () => void;
  disabled?: boolean;
}

const INDENT = '    ';

/**
 * Syntax-highlighted Python editor.
 * Uses an interactive transparent textarea synchronized with an underlying Prism-highlighted pre layer.
 */
export function CodeEditor({ value, onChange, onSubmit, disabled }: CodeEditorProps) {
  const gutterRef = useRef<HTMLDivElement>(null);
  const preRef = useRef<HTMLPreElement>(null);

  const lineCount = value.split('\n').length;

  const highlightedHtml = useMemo(() => {
    // Add trailing space if ending with newline so height remains aligned with textarea
    const codeToHighlight = value.endsWith('\n') ? value + ' ' : value || ' ';
    return highlightPython(codeToHighlight);
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onSubmit?.();
      return;
    }
    if (e.key === 'Tab' && !e.shiftKey) {
      e.preventDefault();
      const el = e.currentTarget;
      const { selectionStart: start, selectionEnd: end } = el;
      onChange(value.slice(0, start) + INDENT + value.slice(end));
      requestAnimationFrame(() => el.setSelectionRange(start + INDENT.length, start + INDENT.length));
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    const { scrollTop, scrollLeft } = e.currentTarget;
    if (gutterRef.current) gutterRef.current.scrollTop = scrollTop;
    if (preRef.current) {
      preRef.current.scrollTop = scrollTop;
      preRef.current.scrollLeft = scrollLeft;
    }
  };

  return (
    <div className="flex h-[440px] overflow-hidden rounded-xl border border-white/10 bg-[#0b0f17] font-mono text-[13px] leading-6 focus-within:border-indigo-500/60">
      {/* Line Numbers Gutter. Extra bottom padding: the textarea's horizontal scrollbar lets it
          scroll further than this un-scrollbarred layer, which would otherwise clamp and drift. */}
      <div
        ref={gutterRef}
        aria-hidden
        className="select-none overflow-hidden border-r border-white/5 px-3 pt-3 pb-12 text-right text-slate-600"
      >
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i}>{i + 1}</div>
        ))}
      </div>

      {/* Synchronized Editor Surface */}
      <div className="relative flex-1 overflow-hidden">
        {/* Syntax-highlighted background. pb/pr exceed the textarea's py/px by more than a scrollbar,
            so this layer can always scroll as far as the textarea (keeps colors under the caret). */}
        <pre
          ref={preRef}
          aria-hidden
          className="pointer-events-none absolute inset-0 m-0 overflow-hidden whitespace-pre pt-3 pb-12 pl-4 pr-12 font-mono text-[13px] leading-6"
        >
          <code
            className="language-python"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        </pre>

        {/* Transparent Interactive Textarea */}
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          disabled={disabled}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          aria-label="Python source code"
          placeholder="# Paste or write Python code here…"
          className="absolute inset-0 m-0 h-full w-full resize-none whitespace-pre border-none bg-transparent px-4 py-3 font-mono text-[13px] leading-6 text-transparent caret-indigo-400 selection:bg-indigo-500/30 outline-none placeholder:text-slate-600 disabled:opacity-60"
        />
      </div>
    </div>
  );
}
