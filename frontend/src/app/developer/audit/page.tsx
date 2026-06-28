'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

export default function DeveloperAuditPage() {
  const { t } = useLanguage();
  const [logs, setLogs] = useState<Array<{
    id: string;
    actor_email?: string;
    actor_role: string;
    action: string;
    resource?: string;
    created_at?: string;
  }>>([]);

  useEffect(() => {
    api.getDeveloperAuditLogs().then(setLogs).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">{t.developer.audit}</h1>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <th className="text-left p-4">Time</th>
                <th className="text-left p-4">Actor</th>
                <th className="text-left p-4">Role</th>
                <th className="text-left p-4">Action</th>
                <th className="text-left p-4">Resource</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t border-gray-50">
                  <td className="p-4 text-gray-500">{log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</td>
                  <td className="p-4">{log.actor_email || '—'}</td>
                  <td className="p-4"><span className="bg-slate-100 px-2 py-0.5 rounded text-xs">{log.actor_role}</span></td>
                  <td className="p-4 font-medium">{log.action}</td>
                  <td className="p-4 text-gray-500">{log.resource || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && <p className="p-8 text-center text-gray-400">{t.developer.noActivity}</p>}
        </div>
      </main>
    </div>
  );
}
