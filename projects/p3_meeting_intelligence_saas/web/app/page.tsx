'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Cpu,
  Layers,
  Sparkles,
  BarChart3,
  FileCheck2,
} from 'lucide-react';
import { AudioUploader } from '@/components/audio-uploader';
import { MoMDisplay } from '@/components/mom-display';
import { ActionItemsTable } from '@/components/action-items-table';
import { MeetingMinutes, generateMockMeetingMinutes } from '@/lib/api';

export default function HomePage() {
  const [currentResult, setCurrentResult] = useState<MeetingMinutes | null>(null);

  const loadSampleData = () => {
    const sample = generateMockMeetingMinutes('quarterly_strategic_sync.mp3', 'confidential');
    setCurrentResult(sample);
  };

  return (
    <div style={{ paddingBottom: '4rem' }}>
      {/* Hero Section */}
      <section
        style={{
          position: 'relative',
          padding: '4.5rem 0 3.5rem',
          textAlign: 'center',
          overflow: 'hidden',
        }}
      >
        <div className="container">
          {/* Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.4rem 1rem',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.25)',
              fontSize: '0.85rem',
              color: 'var(--accent-indigo)',
              marginBottom: '1.5rem',
            }}
          >
            <Sparkles size={16} />
            <span>Hybrid Audio Transcription & Map-Reduce LLM Synthesis</span>
          </div>

          {/* Heading */}
          <h1
            style={{
              fontSize: 'clamp(2.4rem, 5vw, 3.8rem)',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              lineHeight: 1.15,
              maxWidth: '850px',
              margin: '0 auto 1.25rem',
            }}
          >
            Transform Meeting Audio into{' '}
            <span className="gradient-text">Precision Action Items</span> & MoM
          </h1>

          <p
            style={{
              fontSize: '1.15rem',
              color: 'var(--text-secondary)',
              maxWidth: '680px',
              margin: '0 auto 2.5rem',
              lineHeight: 1.6,
            }}
          >
            Dual-path intelligence engine. Route confidential audio to local{' '}
            <strong style={{ color: 'var(--accent-emerald)' }}>Faster-Whisper (CPU, int8, VAD)</strong> with zero data retention, or stream public syncs via{' '}
            <strong style={{ color: 'var(--accent-blue)' }}>Cloud Deepgram</strong>.
          </p>

          {/* Quick CTAs */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <a href="#upload-section" className="btn-primary">
              <Zap size={18} />
              Process New Audio
            </a>
            <button onClick={loadSampleData} className="btn-secondary">
              <FileCheck2 size={18} />
              Preview Sample MoM
            </button>
            <Link href="/dashboard" className="btn-secondary">
              <BarChart3 size={18} />
              Open Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section style={{ padding: '2rem 0' }}>
        <div className="container">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.5rem',
              marginBottom: '3.5rem',
            }}
          >
            {/* Feature 1 */}
            <div className="glass-panel" style={{ padding: '1.75rem' }}>
              <div
                style={{
                  display: 'inline-flex',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(16, 185, 129, 0.1)',
                  color: 'var(--accent-emerald)',
                  marginBottom: '1rem',
                }}
              >
                <ShieldCheck size={24} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Confidential On-Prem Engine
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                Local faster-whisper on CPU with int8 quantization and Silero VAD. Zero third-party audio transmission.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-panel" style={{ padding: '1.75rem' }}>
              <div
                style={{
                  display: 'inline-flex',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(59, 130, 246, 0.1)',
                  color: 'var(--accent-blue)',
                  marginBottom: '1rem',
                }}
              >
                <Cpu size={24} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                High-Speed Cloud Deepgram
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                Sub-second public stream transcription with automated speaker diarization and noise cancellation.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-panel" style={{ padding: '1.75rem' }}>
              <div
                style={{
                  display: 'inline-flex',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(99, 102, 241, 0.1)',
                  color: 'var(--accent-indigo)',
                  marginBottom: '1rem',
                }}
              >
                <Layers size={24} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Map-Reduce & Pydantic Validation
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                LiteLLM + Instructor guarantee 100% structured JSON conforming to strict enterprise meeting schemas.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Upload & Results Section */}
      <section id="upload-section">
        <div className="container">
          <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Audio Uploader Component */}
            <AudioUploader onSuccess={(data) => setCurrentResult(data)} />

            {/* Generated Results Preview */}
            {currentResult && (
              <>
                <MoMDisplay minutes={currentResult} />
                <ActionItemsTable initialItems={currentResult.action_items} />
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
