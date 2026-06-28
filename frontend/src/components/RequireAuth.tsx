'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

const ROLE_HOME: Record<string, string> = {
  patient: '/dashboard',
  admin: '/admin',
  developer: '/developer',
};

interface RequireAuthProps {
  children: React.ReactNode;
  allowedRoles: string[];
}

export default function RequireAuth({ children, allowedRoles }: RequireAuthProps) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    api.syncAuthCookies();

    const token = api.getToken();
    const role = api.getRole();

    if (!token) {
      router.replace('/login');
      return;
    }

    if (role && !allowedRoles.includes(role)) {
      router.replace(ROLE_HOME[role] || '/login');
      return;
    }

    if (!role && allowedRoles.includes('patient')) {
      api.setRole('patient');
    }

    setAuthorized(true);
  }, [router, allowedRoles]);

  if (!authorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-2 border-primary-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}
