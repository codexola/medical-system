'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

export default function DeveloperStaffPage() {
  const { t } = useLanguage();
  const [staff, setStaff] = useState<Array<{
    id: string;
    email: string;
    name: string;
    role: string;
    is_active: boolean;
    last_login?: string;
  }>>([]);

  useEffect(() => {
    api.getDeveloperStaff().then(setStaff).catch(() => {});
  }, []);

  const roleLabel = (role: string) => {
    if (role === 'developer') return t.developer.roleDeveloper;
    if (role === 'admin') return t.developer.roleAdmin;
    return role;
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">{t.developer.staff}</h1>
        <p className="text-sm text-gray-500 mb-8">{t.developer.staffDesc}</p>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <th className="text-left p-4">{t.auth.name}</th>
                <th className="text-left p-4">{t.auth.email}</th>
                <th className="text-left p-4">{t.developer.accountType}</th>
                <th className="text-left p-4">Status</th>
                <th className="text-left p-4">Last Login</th>
              </tr>
            </thead>
            <tbody>
              {staff.map((account) => (
                <tr key={account.id} className="border-t border-gray-50">
                  <td className="p-4 font-medium">{account.name}</td>
                  <td className="p-4">{account.email}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      account.role === 'developer' ? 'bg-violet-100 text-violet-700' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {roleLabel(account.role)}
                    </span>
                  </td>
                  <td className="p-4">{account.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="p-4 text-gray-500">
                    {account.last_login ? new Date(account.last_login).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
