'use client';

import DashboardSidebar from '@/components/DashboardSidebar';
import RequireAuth from '@/components/RequireAuth';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth allowedRoles={['patient']}>
      <div className="min-h-screen page-shell">
        <DashboardSidebar />
        <div className="ml-72 min-h-screen">{children}</div>
      </div>
    </RequireAuth>
  );
}
