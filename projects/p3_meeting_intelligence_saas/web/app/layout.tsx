import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/navbar';
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
        {/* Navigation Bar & Auth Modal */}
        <Navbar />

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
