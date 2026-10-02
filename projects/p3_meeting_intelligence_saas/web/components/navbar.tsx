'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Waves, LogIn, LogOut, User as UserIcon, Settings } from 'lucide-react';
import { LoginModal } from '@/components/login-modal';
import { SettingsModal } from '@/components/settings-modal';
import { LogoutModal } from '@/components/logout-modal';
import { getStoredUser, clearAuth, getAvatarUrl, User } from '@/lib/api';

export function Navbar() {
  const router = useRouter();
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLogoutOpen, setIsLogoutOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    // Load stored user on mount
    setCurrentUser(getStoredUser());

    const handleAuthChange = () => {
      setCurrentUser(getStoredUser());
    };

    window.addEventListener('auth_state_changed', handleAuthChange);
    return () => window.removeEventListener('auth_state_changed', handleAuthChange);
  }, []);

  const handleLogout = () => {
    clearAuth();
    setCurrentUser(null);
    setIsLogoutOpen(false);
  };

  return (
    <>
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

              {currentUser ? (
                <div
                  className="wave-ring"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-subtle)',
                    padding: '0.35rem 0.75rem',
                    borderRadius: 'var(--radius-full)',
                  }}
                >
                  <div
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: 'var(--gradient-brand)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: '#ffffff',
                      overflow: 'hidden',
                    }}
                  >
                    {getAvatarUrl(currentUser) ? (
                      // eslint-disable-next-line @next/next/no-img-element -- served by the API
                      <img
                        src={getAvatarUrl(currentUser)!}
                        alt=""
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      (currentUser.first_name || currentUser.email || 'U')[0].toUpperCase()
                    )}
                  </div>
                  <span style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: 500 }}>
                    {currentUser.first_name ? `${currentUser.first_name} ${currentUser.last_name || ''}`.trim() : currentUser.email}
                  </span>
                  <div style={{ display: 'flex', gap: '0.25rem', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '0.75rem', marginLeft: '0.25rem' }}>
                    <button
                      onClick={() => setIsSettingsOpen(true)}
                      title="Settings"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0.2rem',
                        transition: 'color 0.15s'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                    >
                      <Settings size={15} />
                    </button>
                    <button
                      onClick={() => setIsLogoutOpen(true)}
                      title="Sign Out"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0.2rem',
                        transition: 'color 0.15s'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                    >
                      <LogOut size={15} />
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsLoginOpen(true)}
                  style={{
                    background: 'none',
                    border: 'none',
                    font: 'inherit',
                    color: 'inherit',
                    cursor: 'pointer',
                    padding: 0,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    transition: 'color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  <LogIn size={16} />
                  <span>Login</span>
                </button>
              )}

            </nav>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
          router.push('/dashboard');
        }}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Logout Confirmation Modal */}
      <LogoutModal
        isOpen={isLogoutOpen}
        onClose={() => setIsLogoutOpen(false)}
        onConfirm={handleLogout}
      />
    </>
  );
}
