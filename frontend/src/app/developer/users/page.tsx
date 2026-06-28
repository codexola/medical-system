'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Search, Trash2 } from 'lucide-react';

export default function DeveloperUsersPage() {
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [users, setUsers] = useState<Array<{
    id: string;
    name?: string;
    email?: string;
    phone?: string;
    created_at?: string;
    message_count: number;
  }>>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const search = () => {
    api.getDeveloperUsers(query).then(setUsers).catch(() => {});
  };

  useEffect(() => { search(); }, []);

  const deleteChatHistory = async (userId: string) => {
    if (!window.confirm(t.developer.deleteChatHistoryConfirm)) return;
    setDeletingId(userId);
    try {
      const result = await api.developerDeleteChatHistory(userId);
      window.alert(t.developer.deleteChatHistoryDone);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, message_count: 0 } : u))
      );
      if (result.deleted_messages === 0 && result.deleted_memories === 0) {
        /* already empty */
      }
    } catch {
      window.alert(t.common.error);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-2">{t.developer.users}</h1>
        <p className="text-sm text-gray-500 mb-6">{t.developer.usersDesc}</p>

        <div className="flex gap-3 mb-6">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
            placeholder="名前、メール、電話番号で検索..."
            className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-violet-500"
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
                <th className="px-6 py-3">{t.developer.messageCount}</th>
                <th className="px-6 py-3">Registered</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium">{u.name || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{u.email || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{u.phone || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{u.message_count}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('ja-JP') : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      type="button"
                      onClick={() => deleteChatHistory(u.id)}
                      disabled={deletingId === u.id || u.message_count === 0}
                      className="inline-flex items-center gap-1.5 text-xs text-red-600 hover:text-red-700 border border-red-100 hover:border-red-200 px-2.5 py-1.5 rounded-lg disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {t.developer.deleteChatHistory}
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
