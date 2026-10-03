'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginModal } from '@/components/login-modal';
import { getStoredUser } from '@/lib/api';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // LoginModal calls onClose right after onSuccess; don't let it override the redirect
  const didLogin = useRef(false);
  // Only show the modal once we know the visitor is logged out (avoids a flash for logged-in users)
  const [showModal, setShowModal] = useState(false);

  // Only allow same-origin relative paths to avoid open redirects
  const next = searchParams.get('next');
  const redirectTo = next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard';

  // Already logged in: skip the login modal entirely
  useEffect(() => {
    if (getStoredUser()) {
      router.replace(redirectTo);
    } else {
      setShowModal(true);
    }
  }, [router, redirectTo]);

  if (!showModal) return null;

  return (
    <div style={{ minHeight: 'calc(100vh - 180px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <LoginModal
        isOpen={true}
        onClose={() => {
          if (!didLogin.current) router.push('/');
        }}
        onSuccess={() => {
          didLogin.current = true;
          setShowModal(false);
          router.replace(redirectTo);
        }}
      />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
