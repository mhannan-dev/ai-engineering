'use client';

import React, { useEffect } from 'react';
import { LogOut, X } from 'lucide-react';
import { Button } from './ui/button';

interface LogoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function LogoutModal({ isOpen, onClose, onConfirm }: LogoutModalProps) {
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

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-5 bg-black/75 backdrop-blur-md animate-[fadeIn_0.2s_ease-out]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="logout-title"
        className="w-full max-w-[400px] bg-[#0e131f]/90 backdrop-blur-xl border border-red-500/25 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(239,68,68,0.15)] p-8 relative"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white hover:bg-white/10 p-2 rounded-full transition-colors flex items-center justify-center"
          aria-label="Close modal"
        >
          <X size={20} />
        </button>

        {/* Modal Header */}
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400 mb-4">
            <LogOut size={24} />
          </div>
          <h2 id="logout-title" className="text-2xl font-bold tracking-tight mb-1">
            Sign Out?
          </h2>
          <p className="text-slate-400 text-sm">
            You&apos;ll need to sign in again to access your meeting archives &amp; summaries.
          </p>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-3">
          <Button type="button" variant="secondary" onClick={onClose} autoFocus>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            className="!bg-none !bg-red-500 hover:!bg-red-600 !shadow-[0_4px_15px_rgba(239,68,68,0.35)]"
          >
            Sign Out
          </Button>
        </div>
      </div>
    </div>
  );
}
