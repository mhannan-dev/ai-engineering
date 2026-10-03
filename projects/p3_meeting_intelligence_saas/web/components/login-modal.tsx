'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Mail,
  Lock,
  User as UserIcon,
  Eye,
  EyeOff,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';
import { loginUser, registerUser, User } from '@/lib/api';
import { Button } from './ui/button';
import { Input } from './ui/input';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (user: User) => void;
}

export function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

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

  // Reset errors when modal opens or mode switches
  useEffect(() => {
    setErrorMsg(null);
    setSuccessMsg(null);
  }, [isOpen, mode]);

  if (!isOpen) return null;

  const handleFillDemo = () => {
    setEmail('test@yopmail.com');
    setPassword('Test@1234');
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      if (mode === 'signin') {
        const { user } = await loginUser(email, password);
        setSuccessMsg(`Welcome back, ${user.first_name || user.email}!`);
        setTimeout(() => {
          setIsLoading(false);
          onSuccess?.(user);
          onClose();
        }, 800);
      } else {
        await registerUser(email, password, firstName.trim(), lastName.trim());
        // Automatically login after successful registration
        const { user } = await loginUser(email, password);
        setSuccessMsg('Account created successfully!');
        setTimeout(() => {
          setIsLoading(false);
          onSuccess?.(user);
          onClose();
        }, 800);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed.';
      setErrorMsg(msg);
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-5 bg-black/75 backdrop-blur-md animate-[fadeIn_0.2s_ease-out]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-[440px] bg-[#0e131f]/90 backdrop-blur-xl border border-indigo-500/25 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(99,102,241,0.2)] p-8 relative">
        
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
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.5)] mb-4">
            <ShieldCheck size={26} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-1">
            {mode === 'signin' ? 'Welcome Back' : 'Create an Account'}
          </h2>
          <p className="text-slate-400 text-sm">
            {mode === 'signin'
              ? 'Sign in to access your meeting archives & summaries'
              : 'Sign up to start synthesizing hybrid audio meeting notes'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex bg-white/5 rounded-xl p-1 mb-6 border border-white/10">
          <button
            type="button"
            onClick={() => setMode('signin')}
            className={`flex-1 p-2 rounded-lg text-sm transition-all duration-150 ${
              mode === 'signin'
                ? 'font-semibold text-white bg-indigo-500/30 shadow-sm'
                : 'font-medium text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode('signup')}
            className={`flex-1 p-2 rounded-lg text-sm transition-all duration-150 ${
              mode === 'signup'
                ? 'font-semibold text-white bg-indigo-500/30 shadow-sm'
                : 'font-medium text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Status Alerts */}
        {errorMsg && (
          <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm mb-5">
            <AlertCircle size={18} className="shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="flex items-center gap-3 px-4 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm mb-5">
            <CheckCircle2 size={18} className="shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {mode === 'signup' && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-slate-400 mb-1.5">
                  First Name
                </label>
                <Input
                  required
                  placeholder="Alex"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  icon={<UserIcon size={18} />}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-400 mb-1.5">
                  Last Name
                </label>
                <Input
                  required
                  placeholder="Morgan"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  icon={<UserIcon size={18} />}
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-slate-400 mb-1.5">
              Email Address
            </label>
            <Input
              type="email"
              required
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={18} />}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-400 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={18} />}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Quick Demo Fill Helper */}
          {mode === 'signin' && (
            <div className="flex justify-between items-center text-xs">
              <Button
                type="button"
                variant="ghost"
                onClick={handleFillDemo}
                className="flex items-center gap-1.5 !px-2 !py-1 !h-auto"
              >
                <Sparkles size={14} />
                <span>Fill Demo Credentials</span>
              </Button>
              <span className="text-slate-500">test@yopmail.com / Test@1234</span>
            </div>
          )}

          {/* Submit Button */}
          <Button type="submit" isLoading={isLoading} className="w-full mt-2">
            {mode === 'signin' ? 'Sign In' : 'Create Account'}
          </Button>
        </form>
      </div>
    </div>
  );
}
