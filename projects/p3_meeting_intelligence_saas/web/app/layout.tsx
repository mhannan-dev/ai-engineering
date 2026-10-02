import type { Metadata } from 'next';
import Link from 'next/link';
import { Waves, Sparkles, Activity, ShieldCheck } from 'lucide-react';
import './globals.css';

export const metadata: Metadata = {
  title: 'MeetingIntel AI | Hybrid Audio Minutes & Action Engine',
  description:
    'Enterprise Meeting Intelligence SaaS featuring hybrid transcription (Faster-Whisper on CPU + Deepgram Cloud) and map-reduce LLM synthesis.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {/* Navigation Bar */}
        <header className="navbar">
          <div className="container">
            <div className="navbar-inner">
              <Link href="/" className="nav-logo">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'var(--gradient-brand)',
                    color: '#ffffff',
                    boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)',
                  }}
                >
                  <Waves size={20} />
                </div>
                <span>
                  Meeting<span className="gradient-text">Intel</span>.ai
                </span>
              </Link>

              <nav className="nav-links">
                <Link href="/">Home</Link>
                <Link href="/dashboard">Dashboard</Link>
                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    fontSize: '0.8rem',
                    padding: '0.3rem 0.75rem',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    color: 'var(--accent-emerald)',
                  }}
                >
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: 'var(--accent-emerald)',
                      display: 'inline-block',
                    }}
                  />
                  Backend: Ready
                </div>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Application Body */}
        <main style={{ flex: 1 }}>{children}</main>

        {/* Global Footer */}
        <footer
          style={{
            borderTop: '1px solid var(--border-subtle)',
            padding: '2.5rem 0',
            marginTop: '4rem',
            background: 'rgba(10, 13, 20, 0.6)',
          }}
        >
          <div className="container">
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '1.5rem',
                fontSize: '0.85rem',
                color: 'var(--text-muted)',
              }}
            >
              <div>
                <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  Hybrid Audio Meeting Minutes & Action Items Engine
                </p>
                <p>FastAPI • Faster-Whisper (CPU int8 VAD) • Deepgram API • LiteLLM + Instructor</p>
              </div>

              <div style={{ display: 'flex', gap: '1.25rem' }}>
                <Link href="/" style={{ color: 'var(--text-secondary)' }}>
                  Home
                </Link>
                <Link href="/dashboard" style={{ color: 'var(--text-secondary)' }}>
                  Intelligence Dashboard
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
