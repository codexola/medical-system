'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Search, Trash2 } from 'lucide-react';

export default function AdminPatientsPage() {
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [patients, setPatients] = useState<Array<{
    id: string;
    name?: string;
    email?: string;
    phone?: string;
    created_at?: string;
    subscription?: { plan: string; status: string; active: boolean; trial_end?: string };
  }>>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const search = () => {
    api.searchPatients(query).then(setPatients).catch(() => {});
  };

  const deleteChatHistory = async (patientId: string) => {
    if (!window.confirm(t.admin.deleteChatHistoryConfirm)) return;
    setDeletingId(patientId);
    try {
      await api.adminDeleteChatHistory(patientId);
      window.alert(t.admin.deleteChatHistoryDone);
    } catch {
      window.alert(t.common.error);
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => { search(); }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6">{t.admin.patients}</h1>

        <div className="flex gap-3 mb-6">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
            placeholder="名前、メール、電話番号で検索..."
            className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button onClick={search} className="btn-primary flex items-center gap-2">
            <Search className="w-4 h-4" /> {t.common.search}
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-left text-sm text-gray-500">
              <tr>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Phone</th>
                <th className="px-6 py-3">Subscription</th>
                <th className="px-6 py-3">Registered</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {patients.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium">{p.name || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{p.email || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{p.phone || '-'}</td>
                  <td className="px-6 py-4 text-sm">
                    {p.subscription ? (
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        p.subscription.active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {p.subscription.plan} / {p.subscription.status}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">
                    {p.created_at ? new Date(p.created_at).toLocaleDateString('ja-JP') : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      type="button"
                      onClick={() => deleteChatHistory(p.id)}
                      disabled={deletingId === p.id}
                      className="inline-flex items-center gap-1.5 text-xs text-red-600 hover:text-red-700 border border-red-100 hover:border-red-200 px-2.5 py-1.5 rounded-lg disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {t.admin.deleteChatHistory}
                    </button>
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
