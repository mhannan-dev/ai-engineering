'use client';

import { Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LoginModal } from '@/components/login-modal';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // LoginModal calls onClose right after onSuccess; don't let it override the redirect
  const didLogin = useRef(false);

  // Only allow same-origin relative paths to avoid open redirects
  const next = searchParams.get('next');
  const redirectTo = next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard';

  return (
    <div style={{ minHeight: 'calc(100vh - 180px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <LoginModal
        isOpen={true}
        onClose={() => {
          if (!didLogin.current) router.push('/');
        }}
        onSuccess={() => {
          didLogin.current = true;
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
