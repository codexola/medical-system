'use client';

import RequireAuth from '@/components/RequireAuth';

export default function DeveloperLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth allowedRoles={['developer']}>{children}</RequireAuth>;
}
