'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { getStoredUser } from '@/lib/api';

/**
 * Client-side route guard. Renders children only when a user is stored;
 * otherwise redirects to /login?next=<current path>. Also reacts to
 * sign-out while the protected page is open.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    const check = () => {
      if (getStoredUser()) {
        setIsAuthed(true);
      } else {
        setIsAuthed(false);
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      }
    };

    check();
    window.addEventListener('auth_state_changed', check);
    // Keep multiple tabs in sync (logout in another tab)
    window.addEventListener('storage', check);
    return () => {
      window.removeEventListener('auth_state_changed', check);
      window.removeEventListener('storage', check);
    };
  }, [router, pathname]);

  if (!isAuthed) return null;

  return <>{children}</>;
}
