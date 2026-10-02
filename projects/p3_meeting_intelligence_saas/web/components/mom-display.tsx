'use client';

import React, { useState } from 'react';
import {
  FileText,
  Calendar,
  Cpu,
  CheckCircle,
  Copy,
  Check,
  Download,
  Share2,
  Clock,
  Sparkles,
} from 'lucide-react';
import { MeetingMinutes } from '@/lib/api';

interface MoMDisplayProps {
  minutes: MeetingMinutes;
}

export function MoMDisplay({ minutes }: MoMDisplayProps) {
  const [copied, setCopied] = useState(false);

  const copyMarkdown = () => {
    const md = `
# ${minutes.meeting_title}
**Date:** ${minutes.date}  
**Engine:** ${minutes.transcription_metadata.engine}  
**Classification:** ${minutes.transcription_metadata.sensitivity.toUpperCase()}  

## Executive Summary
${minutes.executive_summary}

## Key Discussion Points
${minutes.key_discussion_points.map((pt) => `- ${pt}`).join('\n')}

## Decisions Made
${minutes.decisions_made.map((dec) => `- [x] ${dec}`).join('\n')}

## Action Items
| Task | Assignee | Due Date | Priority | Status |
|------|----------|----------|----------|--------|
${minutes.action_items
  .map(
    (item) =>
      `| ${item.task} | ${item.assignee} | ${item.due_date} | ${item.priority} | ${item.status} |`
  )
  .join('\n')}
    `.trim();

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(minutes, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${minutes.meeting_title.toLowerCase().replace(/\s+/g, '_')}_mom.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      {/* Header with Title and Actions */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '1rem',
          paddingBottom: '1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '1.75rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <span
              className={`badge ${
                minutes.transcription_metadata.sensitivity === 'confidential'
                  ? 'badge-confidential'
                  : 'badge-public'
              }`}
            >
              {minutes.transcription_metadata.sensitivity}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Calendar size={14} />
              {minutes.date}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Clock size={14} />
              {Math.floor(minutes.transcription_metadata.duration_seconds / 60)}m {minutes.transcription_metadata.duration_seconds % 60}s
            </span>
          </div>

          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            {minutes.meeting_title}
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
            <Cpu size={14} style={{ color: 'var(--accent-cyan)' }} />
            <span>Engine: <strong>{minutes.transcription_metadata.engine}</strong></span>
            {minutes.transcription_metadata.confidence_score && (
              <span style={{ marginLeft: '0.5rem', color: 'var(--accent-emerald)' }}>
                • {(minutes.transcription_metadata.confidence_score * 100).toFixed(1)}% Confidence
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={copyMarkdown}
            className="btn-secondary"
            style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
          >
            {copied ? <Check size={16} style={{ color: 'var(--accent-emerald)' }} /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy Markdown'}
          </button>
          <button
            onClick={downloadJSON}
            className="btn-secondary"
            style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
          >
            <Download size={16} />
            Export JSON
          </button>
        </div>
      </div>

      {/* Executive Summary Card */}
      <div
        style={{
          marginBottom: '2rem',
          padding: '1.25rem 1.5rem',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(99, 102, 241, 0.05)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
          <Sparkles size={18} style={{ color: 'var(--accent-indigo)' }} />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Executive Synthesis</h3>
        </div>
        <p style={{ color: '#cbd5e1', lineHeight: 1.65, fontSize: '0.95rem' }}>
          {minutes.executive_summary}
        </p>
      </div>

      {/* Grid: Discussion Points & Decisions */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.75rem',
        }}
      >
        {/* Key Discussion Points */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FileText size={18} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Key Discussion Points</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
            {minutes.key_discussion_points.map((item, idx) => (
              <li
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  fontSize: '0.9rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                }}
              >
                <div
                  style={{
                    minWidth: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--accent-cyan)',
                    marginTop: '0.5rem',
                  }}
                />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Decisions Made */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <CheckCircle size={18} style={{ color: 'var(--accent-emerald)' }} />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Decisions Made</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {minutes.decisions_made.map((decision, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  padding: '0.85rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(16, 185, 129, 0.05)',
                  border: '1px solid rgba(16, 185, 129, 0.15)',
                  fontSize: '0.88rem',
                  lineHeight: 1.45,
                }}
              >
                <Check size={16} style={{ color: 'var(--accent-emerald)', marginTop: '0.15rem', flexShrink: 0 }} />
                <span>{decision}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
