'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api, AILog } from '@/lib/api';
import { Brain } from 'lucide-react';

export default function AdminAILogsPage() {
  const { t } = useLanguage();
  const [logs, setLogs] = useState<AILog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAILogs().then(setLogs).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6 flex items-center gap-2">
          <Brain className="w-6 h-6" /> {t.admin.aiLogs}
        </h1>

        {loading ? (
          <p className="text-gray-500">{t.common.loading}</p>
        ) : logs.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">AIログがありません</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 text-left text-sm text-gray-500">
                <tr>
                  <th className="px-6 py-3">Time</th>
                  <th className="px-6 py-3">Provider</th>
                  <th className="px-6 py-3">Model</th>
                  <th className="px-6 py-3">Agent</th>
                  <th className="px-6 py-3">Tokens</th>
                  <th className="px-6 py-3">Latency</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 text-sm">
                    <td className="px-6 py-4 text-gray-400">
                      {log.created_at ? new Date(log.created_at).toLocaleString('ja-JP') : '-'}
                    </td>
                    <td className="px-6 py-4">{log.provider}</td>
                    <td className="px-6 py-4 font-medium">{log.model}</td>
                    <td className="px-6 py-4 text-gray-500">{log.agent || '-'}</td>
                    <td className="px-6 py-4">{log.tokens?.toLocaleString() || '-'}</td>
                    <td className="px-6 py-4">{log.latency_ms ? `${log.latency_ms}ms` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
