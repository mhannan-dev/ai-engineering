'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Binary } from 'lucide-react';
import { API_BASE_URL, checkApiHealth } from '@/lib/api';

type ApiStatus = 'checking' | 'online' | 'offline';

const STATUS_STYLES: Record<ApiStatus, { dot: string; label: string }> = {
  checking: { dot: 'bg-slate-500', label: 'Checking API…' },
  online: { dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]', label: 'API online' },
  offline: { dot: 'bg-rose-500', label: 'API offline' },
};

export function SiteHeader() {
  const [status, setStatus] = useState<ApiStatus>('checking');

  // Re-check periodically so the indicator recovers when the backend is started
  useEffect(() => {
    const controller = new AbortController();
    const check = async () => setStatus((await checkApiHealth(controller.signal)) ? 'online' : 'offline');
    check();
    const timer = setInterval(check, 15000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, []);

  const { dot, label } = STATUS_STYLES[status];

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <Link href="/" className="nav-logo">
          <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-[0_0_16px_rgba(99,102,241,0.4)]">
            <Binary size={20} />
          </span>
          <span>
            Py<span className="gradient-text">2</span>Cpp Transpiler
          </span>
        </Link>

        <div
          className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300"
          title={`Backend: ${API_BASE_URL}`}
        >
          <span className={`h-2 w-2 rounded-full ${dot}`} />
          {label}
        </div>
      </div>
    </header>
  );
}
