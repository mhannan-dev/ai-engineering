'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  UploadCloud,
  FileAudio,
  ShieldAlert,
  Globe2,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { uploadAndProcessAudio } from '@/lib/api';

interface AudioUploaderModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AudioUploaderModal({ isOpen, onClose }: AudioUploaderModalProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sensitivity, setSensitivity] = useState<'confidential' | 'public'>('confidential');
  const [language, setLanguage] = useState<string>('auto');
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedFile(null);
      setSensitivity('confidential');
      setLanguage('auto');
      setIsUploading(false);
      setUploadProgress(0);
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (file: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    
    // Validate file type (basic)
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/mp4'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a)$/i)) {
      setErrorMsg('Unsupported file format. Please upload MP3, WAV, or M4A.');
      return;
    }
    
    // Validate size (e.g., max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      setErrorMsg('File is too large. Maximum size is 20MB.');
      return;
    }
    
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    setErrorMsg(null);
    setUploadProgress(0);
    setStatusMessage('Initializing...');
    
    // We will track real upload progress
    try {
      const minutes = await uploadAndProcessAudio(
        selectedFile, 
        sensitivity, 
        language,
        (stage) => {
          // Status updates from the API wrapper
          setStatusMessage(stage);
          setUploadProgress(99);
        },
        (percent) => {
          // Real-time network upload progress
          setUploadProgress(Math.floor(percent * 0.9));
        }
      );
      
      setUploadProgress(100);
      setStatusMessage('Complete!');
      setSuccessMsg('Meeting Minutes Generated Successfully!');
      
      // In a real app, you might pass 'minutes' back to a parent or redirect to a details page
      console.log('Generated Minutes:', minutes);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Processing failed.');
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-5 bg-black/75 backdrop-blur-md animate-[fadeIn_0.2s_ease-out]"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isUploading) onClose();
      }}
    >
      <div className="w-full max-w-[500px] bg-[#0e131f]/90 backdrop-blur-xl border border-indigo-500/25 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(99,102,241,0.2)] p-8 relative flex flex-col">
        
        {!isUploading && (
          <button
            onClick={onClose}
            className="absolute top-5 right-5 text-slate-400 hover:text-white hover:bg-white/10 p-2 rounded-full transition-colors flex items-center justify-center z-10"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        )}

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.5)] mb-4">
            <UploadCloud size={24} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-1">
            Upload Meeting Audio
          </h2>
          <p className="text-slate-400 text-sm">
            Upload your recording to generate minutes and action items.
          </p>
        </div>

        {errorMsg && (
          <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm mb-5">
            <AlertCircle size={18} className="shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="flex flex-col items-center gap-3 px-4 py-6 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm mb-5 text-center">
            <CheckCircle2 size={48} className="shrink-0 text-emerald-500 mb-2" />
            <span className="text-lg font-semibold">{successMsg}</span>
            <Button className="mt-4" onClick={onClose}>Close Window</Button>
          </div>
        )}

        {!successMsg && (
          <>
            {/* Drag and Drop Zone */}
            <div
              className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition-all duration-200 mb-6 ${
                dragActive 
                  ? 'border-indigo-400 bg-indigo-500/10' 
                  : selectedFile
                    ? 'border-emerald-500/50 bg-emerald-500/5'
                    : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".mp3,.wav,.m4a"
                onChange={handleChange}
                className="hidden"
                disabled={isUploading}
              />
              
              {selectedFile ? (
                <>
                  <FileAudio size={40} className="text-emerald-400 mb-3" />
                  <p className="font-semibold text-emerald-300 mb-1 truncate max-w-full px-4">{selectedFile.name}</p>
                  <p className="text-xs text-slate-400">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  {!isUploading && (
                    <button 
                      onClick={() => setSelectedFile(null)}
                      className="text-xs text-red-400 hover:text-red-300 mt-4 underline"
                    >
                      Remove file
                    </button>
                  )}
                </>
              ) : (
                <>
                  <UploadCloud size={40} className="text-slate-400 mb-3" />
                  <p className="font-semibold text-slate-200 mb-1">Drag & drop your audio file here</p>
                  <p className="text-xs text-slate-400 mb-4">Supports MP3, WAV, M4A (Max 20MB)</p>
                  <Button 
                    variant="secondary" 
                    className="!px-4 !py-2 !text-xs"
                    onClick={() => inputRef.current?.click()}
                  >
                    Browse Files
                  </Button>
                </>
              )}
            </div>

            {/* Settings */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-slate-300 mb-3">
                Processing Engine & Sensitivity
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setSensitivity('confidential')}
                  disabled={isUploading}
                  className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all ${
                    sensitivity === 'confidential'
                      ? 'border-indigo-500 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                      : 'border-white/10 bg-white/5 opacity-60 hover:opacity-100 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1.5 font-semibold text-sm">
                    <ShieldAlert size={16} className={sensitivity === 'confidential' ? 'text-indigo-400' : ''} />
                    <span>Confidential</span>
                  </div>
                  <span className="text-[11px] text-slate-400 leading-tight">
                    Local CPU transcription. Zero cloud retention.
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setSensitivity('public')}
                  disabled={isUploading}
                  className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all ${
                    sensitivity === 'public'
                      ? 'border-cyan-500 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                      : 'border-white/10 bg-white/5 opacity-60 hover:opacity-100 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1.5 font-semibold text-sm">
                    <Globe2 size={16} className={sensitivity === 'public' ? 'text-cyan-400' : ''} />
                    <span>Public / Fast</span>
                  </div>
                  <span className="text-[11px] text-slate-400 leading-tight">
                    Cloud API routing for maximum speed.
                  </span>
                </button>
              </div>
            </div>

            {/* Language Selection */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Spoken Language
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'auto', label: 'Auto Detect' },
                  { id: 'bn', label: 'বাংলা (Bengali)' },
                  { id: 'en', label: 'English' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setLanguage(item.id)}
                    disabled={isUploading}
                    className={`py-2 px-2.5 rounded-xl text-xs font-medium border text-center transition-all ${
                      language === item.id
                        ? 'border-indigo-500 bg-indigo-500/20 text-white shadow-[0_0_12px_rgba(99,102,241,0.25)] font-semibold'
                        : 'border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Upload Progress Bar */}
            {isUploading && (
              <div className="mb-6">
                <div className="flex justify-between text-xs font-medium text-slate-400 mb-1.5">
                  <span className="truncate pr-4">{statusMessage}</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500 transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            <Button 
              className="w-full" 
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              isLoading={isUploading}
            >
              {isUploading ? 'Synthesizing Minutes...' : 'Generate Intelligence'}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
