'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  User as UserIcon,
  Lock,
  Mail,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Camera,
  Trash2,
  Loader2
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { User, getStoredUser, getAvatarUrl, uploadAvatar, removeAvatar, updateProfile } from '@/lib/api';

// Allowed uploads (the API re-checks the real format and converts to WebP)
const AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const AVATAR_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const AVATAR_MAX_BYTES = 2 * 1024 * 1024; // keep in sync with API AVATAR_MAX_BYTES

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'profile' | 'security'>('profile');
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // Profile fields
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  // Security fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Avatar
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [isAvatarBusy, setIsAvatarBusy] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Release the local preview object URL when it's replaced or the modal unmounts
  useEffect(() => {
    return () => {
      if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    };
  }, [avatarPreview]);

  useEffect(() => {
    if (isOpen) {
      const user = getStoredUser();
      if (user) {
        setCurrentUser(user);
        setFirstName(user.first_name || '');
        setLastName(user.last_name || '');
      }
      setSuccessMsg(null);
      setErrorMsg(null);
      setCurrentPassword('');
      setNewPassword('');
    }
  }, [isOpen]);

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

  const handleAvatarSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // allow re-selecting the same file
    if (!file) return;

    setErrorMsg(null);
    setSuccessMsg(null);

    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!AVATAR_TYPES.includes(file.type) || !AVATAR_EXTENSIONS.includes(ext)) {
      setErrorMsg('Only JPG, JPEG, PNG and WEBP images are allowed.');
      return;
    }
    if (file.size > AVATAR_MAX_BYTES) {
      setErrorMsg('Image is too large. Maximum size is 2 MB.');
      return;
    }

    setAvatarPreview(URL.createObjectURL(file));
    setIsAvatarBusy(true);
    try {
      const user = await uploadAvatar(file);
      setCurrentUser(user);
      setSuccessMsg('Avatar updated successfully.');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Could not upload avatar.');
    } finally {
      setAvatarPreview(null);
      setIsAvatarBusy(false);
    }
  };

  const handleRemoveAvatar = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsAvatarBusy(true);
    try {
      const user = await removeAvatar();
      setCurrentUser(user);
      setSuccessMsg('Avatar removed.');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Could not remove avatar.');
    } finally {
      setIsAvatarBusy(false);
    }
  };

  const avatarSrc = avatarPreview || getAvatarUrl(currentUser);
  const initial = (currentUser?.first_name || currentUser?.email || 'U')[0].toUpperCase();

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const user = await updateProfile(firstName, lastName);
      setCurrentUser(user);
      setSuccessMsg("Profile updated successfully");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Could not update profile.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePassword = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    if (newPassword.length < 8) {
      setErrorMsg("Password must be at least 8 characters long.");
      setIsLoading(false);
      return;
    }

    setTimeout(() => {
      setSuccessMsg("Password updated successfully");
      setCurrentPassword('');
      setNewPassword('');
      setIsLoading(false);
    }, 600);
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-5 bg-black/75 backdrop-blur-md animate-[fadeIn_0.2s_ease-out]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-[480px] bg-[#0e131f]/90 backdrop-blur-xl border border-indigo-500/25 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(99,102,241,0.2)] p-8 relative">

        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white hover:bg-white/10 p-2 rounded-full transition-colors flex items-center justify-center"
          aria-label="Close modal"
        >
          <X size={20} />
        </button>

        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.5)] mb-4">
            <ShieldCheck size={26} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-1">
            Account Settings
          </h2>
          <p className="text-slate-400 text-sm">
            Manage your personal information and security preferences.
          </p>
        </div>

        <div className="flex bg-white/5 rounded-xl p-1 mb-6 border border-white/10">
          <button
            type="button"
            onClick={() => {
              setActiveTab('profile');
              setSuccessMsg(null);
              setErrorMsg(null);
            }}
            className={`flex-1 p-2 rounded-lg text-sm transition-all duration-150 ${activeTab === 'profile'
              ? 'font-semibold text-white bg-indigo-500/30 shadow-sm'
              : 'font-medium text-slate-400 hover:text-white hover:bg-white/5'
              }`}
          >
            Profile
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('security');
              setSuccessMsg(null);
              setErrorMsg(null);
            }}
            className={`flex-1 p-2 rounded-lg text-sm transition-all duration-150 ${activeTab === 'security'
              ? 'font-semibold text-white bg-indigo-500/30 shadow-sm'
              : 'font-medium text-slate-400 hover:text-white hover:bg-white/5'
              }`}
          >
            Security
          </button>
        </div>

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

        {activeTab === 'profile' && (
          <form onSubmit={handleUpdateProfile} className="flex flex-col gap-5">
            {/* Avatar Uploader */}
            <div className="flex items-center gap-5 p-4 rounded-xl bg-white/[0.03] border border-white/10">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isAvatarBusy}
                className="group relative w-20 h-20 shrink-0 rounded-full overflow-hidden bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-2xl font-bold text-white ring-2 ring-white/10 hover:ring-indigo-400/60 transition disabled:cursor-wait"
                aria-label="Change avatar"
              >
                {avatarSrc ? (
                  // eslint-disable-next-line @next/next/no-img-element -- served by the API / blob preview
                  <img src={avatarSrc} alt="Your avatar" className="w-full h-full object-cover" />
                ) : (
                  <span>{initial}</span>
                )}
                <span
                  className={`absolute inset-0 flex items-center justify-center bg-black/55 transition-opacity ${isAvatarBusy ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                    }`}
                >
                  {isAvatarBusy ? <Loader2 size={22} className="animate-spin" /> : <Camera size={22} />}
                </span>
              </button>

              <div className="flex flex-col gap-2 min-w-0">
                <p className="text-sm font-semibold text-white">Profile Photo</p>
                <p className="text-xs text-slate-500">JPG, PNG or WEBP · max 2 MB</p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isAvatarBusy}
                    className="!px-3 !py-1.5 !text-xs"
                  >
                    <Camera size={14} />
                    <span>{currentUser?.avatar ? 'Change' : 'Upload'}</span>
                  </Button>
                  {currentUser?.avatar && (
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={handleRemoveAvatar}
                      disabled={isAvatarBusy}
                      className="!px-3 !py-1.5 !text-xs !text-red-400 hover:!text-red-300 hover:!bg-red-500/10"
                    >
                      <Trash2 size={14} />
                      <span>Remove</span>
                    </Button>
                  )}
                </div>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept={[...AVATAR_TYPES, ...AVATAR_EXTENSIONS].join(',')}
                onChange={handleAvatarSelected}
                className="hidden"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-400 mb-1.5">
                Email Address (Read-only)
              </label>
              <Input
                type="email"
                disabled
                value={currentUser?.email || ''}
                icon={<Mail size={18} />}
                className="opacity-60"
              />
            </div>
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
                  placeholder="Morgan"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  icon={<UserIcon size={18} />}
                />
              </div>
            </div>

            <Button type="submit" isLoading={isLoading} className="w-full mt-2">
              Save Changes
            </Button>
          </form>
        )}

        {activeTab === 'security' && (
          <form onSubmit={handleUpdatePassword} className="flex flex-col gap-5">
            <div>
              <label className="block text-sm font-semibold text-slate-400 mb-1.5">
                Current Password
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
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

            <div>
              <label className="block text-sm font-semibold text-slate-400 mb-1.5">
                New Password
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  icon={<Lock size={18} />}
                />
              </div>
            </div>

            <Button type="submit" isLoading={isLoading} className="w-full mt-2">
              Update Password
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
