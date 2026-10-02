'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  ShieldCheck,
  Cloud,
  FileAudio,
  CheckCircle2,
  Loader2,
  AlertCircle,
  X,
} from 'lucide-react';
import { SensitivityLevel, MeetingMinutes, uploadAndProcessAudio } from '@/lib/api';

interface AudioUploaderProps {
  onSuccess: (data: MeetingMinutes) => void;
}

export function AudioUploader({ onSuccess }: AudioUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityLevel>('confidential');
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [progressStage, setProgressStage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav', 'audio/m4a', 'audio/mp4'];
    const isAudioExt = /\.(mp3|wav|m4a|aac)$/i.test(file.name);

    if (!validTypes.includes(file.type) && !isAudioExt) {
      setErrorMessage('Please upload a valid audio file (.mp3, .wav, or .m4a).');
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(URL.createObjectURL(file));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setErrorMessage(null);
    setProgressStage('Uploading audio to FastAPI backend...');

    try {
      const result = await uploadAndProcessAudio(
        selectedFile,
        sensitivity,
        (stage) => setProgressStage(stage)
      );
      onSuccess(result);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Transcription and synthesis failed.';
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
      setProgressStage('');
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '0.4rem' }}>
          Upload Meeting Audio
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Choose your data classification flag and ingest audio files for automated transcription and LLM synthesis.
        </p>
      </div>

      {/* Sensitivity Selector Switch */}
      <div style={{ marginBottom: '1.75rem' }}>
        <label
          style={{
            display: 'block',
            fontSize: '0.82rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-muted)',
            marginBottom: '0.75rem',
          }}
        >
          Select Data Sensitivity Flag
        </label>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem',
          }}
        >
          {/* Confidential Option */}
          <div
            onClick={() => setSensitivity('confidential')}
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${
                sensitivity === 'confidential' ? 'var(--accent-emerald)' : 'var(--border-subtle)'
              }`,
              background:
                sensitivity === 'confidential'
                  ? 'rgba(16, 185, 129, 0.08)'
                  : 'rgba(255, 255, 255, 0.02)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <ShieldCheck
                size={20}
                style={{
                  color: sensitivity === 'confidential' ? 'var(--accent-emerald)' : 'var(--text-muted)',
                }}
              />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Confidential (On-Prem)</span>
              {sensitivity === 'confidential' && (
                <span className="badge badge-confidential" style={{ marginLeft: 'auto' }}>
                  Active
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Routes to local <strong>faster-whisper</strong> on CPU with int8 quantization and VAD. Zero cloud retention.
            </p>
          </div>

          {/* Public Option */}
          <div
            onClick={() => setSensitivity('public')}
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${
                sensitivity === 'public' ? 'var(--accent-blue)' : 'var(--border-subtle)'
              }`,
              background:
                sensitivity === 'public'
                  ? 'rgba(59, 130, 246, 0.08)'
                  : 'rgba(255, 255, 255, 0.02)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
              <Cloud
                size={20}
                style={{
                  color: sensitivity === 'public' ? 'var(--accent-blue)' : 'var(--text-muted)',
                }}
              />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Public (Cloud API)</span>
              {sensitivity === 'public' && (
                <span className="badge badge-public" style={{ marginLeft: 'auto' }}>
                  Active
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              Routes to <strong>Cloud Deepgram API</strong>. Optimized for high throughput, team syncs, and webinars.
            </p>
          </div>
        </div>
      </div>

      {/* Drag & Drop Area */}
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${isDragging ? 'var(--accent-indigo)' : 'var(--border-subtle)'}`,
            borderRadius: 'var(--radius-md)',
            padding: '3rem 2rem',
            textAlign: 'center',
            backgroundColor: isDragging ? 'rgba(99, 102, 241, 0.06)' : 'rgba(0, 0, 0, 0.2)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            accept=".mp3,.wav,.m4a,audio/*"
            style={{ display: 'none' }}
          />
          <div
            style={{
              display: 'inline-flex',
              padding: '1rem',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(99, 102, 241, 0.1)',
              color: 'var(--accent-indigo)',
              marginBottom: '1rem',
            }}
          >
            <UploadCloud size={32} />
          </div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '0.35rem' }}>
            Click to upload or drag & drop meeting audio
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Supports MP3, WAV, M4A up to 100MB
          </p>
        </div>
      ) : (
        /* File Selected Preview */
        <div
          style={{
            padding: '1.25rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            background: 'rgba(255, 255, 255, 0.03)',
            marginBottom: '1.5rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div
                style={{
                  padding: '0.6rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(6, 182, 212, 0.15)',
                  color: 'var(--accent-cyan)',
                }}
              >
                <FileAudio size={24} />
              </div>
              <div>
                <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>{selectedFile.name}</p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for synthesis
                </p>
              </div>
            </div>

            {!isLoading && (
              <button
                onClick={clearSelection}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '0.4rem',
                }}
                title="Remove file"
              >
                <X size={18} />
              </button>
            )}
          </div>

          {/* Audio Player Preview */}
          {audioUrl && (
            <div style={{ marginTop: '0.75rem' }}>
              <audio
                controls
                src={audioUrl}
                style={{ width: '100%', height: '36px', borderRadius: 'var(--radius-sm)' }}
              />
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: 'var(--accent-rose)',
            fontSize: '0.85rem',
            marginTop: '1rem',
          }}
        >
          <AlertCircle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Progress Notification */}
      {isLoading && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Loader2 size={20} className="animate-spin" style={{ color: 'var(--accent-indigo)' }} />
            <div>
              <p style={{ fontSize: '0.9rem', fontWeight: 600 }}>{progressStage}</p>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Map-Reduce synthesis and Pydantic validation underway
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Action */}
      <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
        {selectedFile && !isLoading && (
          <button
            onClick={clearSelection}
            className="btn-secondary"
            type="button"
          >
            Cancel
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={!selectedFile || isLoading}
          className="btn-primary"
          style={{
            opacity: !selectedFile || isLoading ? 0.6 : 1,
            cursor: !selectedFile || isLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? (
            <>
              <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
              Processing Audio...
            </>
          ) : (
            <>
              <CheckCircle2 size={18} />
              Run Hybrid Engine
            </>
          )}
        </button>
      </div>
    </div>
  );
}
