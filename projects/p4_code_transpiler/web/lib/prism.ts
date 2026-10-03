import Prism from 'prismjs';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-python';

/** Escape for safe insertion via dangerouslySetInnerHTML (Prism escapes on success; this covers failures). */
function escapeHtml(code: string): string {
  return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function highlight(code: string, grammar: Prism.Grammar | undefined, language: string): string {
  if (!grammar) return escapeHtml(code);
  try {
    return Prism.highlight(code, grammar, language);
  } catch {
    // Never return raw code: it is rendered as HTML, so unescaped C++/Python could inject markup
    return escapeHtml(code);
  }
}

/** Returns HTML-escaped, token-wrapped markup for Python source. */
export function highlightPython(code: string): string {
  return highlight(code, Prism.languages.python, 'python');
}

/** Returns HTML-escaped, token-wrapped markup for C++ source. */
export function highlightCpp(code: string): string {
  return highlight(code, Prism.languages.cpp, 'cpp');
}
