'use client';

import { useCallback, useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { api } from '@/lib/api';
import { CreditCard, RefreshCw, XCircle, ArrowUpCircle } from 'lucide-react';

const PLANS = ['free_trial', 'standard', 'premium', 'enterprise'] as const;
const STATUSES = ['trial', 'active', 'cancelled', 'expired', 'past_due'] as const;

type SubRow = {
  id: string;
  user_id: string;
  patient_name?: string;
  patient_email?: string;
  plan: string;
  status: string;
  active: boolean;
  trial_end?: string;
  current_period_end?: string;
  cancelled_at?: string;
};

export default function AdminSubscriptionsPage() {
  const [rows, setRows] = useState<SubRow[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [planFilter, setPlanFilter] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    api.getAdminSubscriptions({ status: statusFilter, plan: planFilter, q: query })
      .then(setRows)
      .catch(() => setMessage('Failed to load subscriptions'))
      .finally(() => setLoading(false));
  }, [statusFilter, planFilter, query]);

  useEffect(() => { load(); }, [load]);

  const handleCancel = async (id: string) => {
    if (!confirm('このサブスクリプションをキャンセルしますか？')) return;
    setMessage('');
    try {
      await api.adminCancelSubscription(id);
      setMessage('キャンセルしました');
      load();
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : 'Error');
    }
  };

  const handleUpgrade = async (id: string, plan: string) => {
    setMessage('');
    try {
      await api.adminUpdateSubscription(id, plan);
      setMessage(`プランを ${plan} に変更しました`);
      load();
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : 'Error');
    }
  };

  const statusBadge = (status: string, active: boolean) => {
    const colors: Record<string, string> = {
      active: 'bg-green-50 text-green-700',
      trial: 'bg-blue-50 text-blue-700',
      cancelled: 'bg-gray-100 text-gray-600',
      expired: 'bg-red-50 text-red-600',
      past_due: 'bg-orange-50 text-orange-700',
    };
    return (
      <span className={`text-xs px-2 py-1 rounded-full ${colors[status] || 'bg-gray-50 text-gray-600'}`}>
        {status}{!active && status !== 'cancelled' ? ' (inactive)' : ''}
      </span>
    );
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-primary-800 flex items-center gap-2">
            <CreditCard className="w-6 h-6" /> Subscriptions
          </h1>
          <button onClick={load} className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-800">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>

        <div className="flex flex-wrap gap-3 mb-6">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && load()}
            placeholder="患者名・メールで検索..."
            className="flex-1 min-w-[200px] px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm"
          />
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-2 bg-white border rounded-lg text-sm">
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={planFilter} onChange={(e) => setPlanFilter(e.target.value)} className="px-3 py-2 bg-white border rounded-lg text-sm">
            <option value="">All plans</option>
            {PLANS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button onClick={load} className="btn-primary text-sm px-4">Search</button>
        </div>

        {message && <p className="text-sm text-mint-700 mb-4">{message}</p>}

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead className="bg-gray-50 text-left text-sm text-gray-500">
              <tr>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Plan</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Trial / Period end</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {rows.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    <p className="font-medium">{r.patient_name || '—'}</p>
                    <p className="text-xs text-gray-400">{r.patient_email}</p>
                  </td>
                  <td className="px-4 py-3 text-sm capitalize">{r.plan.replace('_', ' ')}</td>
                  <td className="px-4 py-3">{statusBadge(r.status, r.active)}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {r.trial_end && <div>Trial: {new Date(r.trial_end).toLocaleDateString('ja-JP')}</div>}
                    {r.current_period_end && <div>Period: {new Date(r.current_period_end).toLocaleDateString('ja-JP')}</div>}
                    {r.cancelled_at && <div className="text-red-500">Cancelled: {new Date(r.cancelled_at).toLocaleDateString('ja-JP')}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      {r.status !== 'cancelled' && (
                        <>
                          <select
                            className="text-xs border rounded px-2 py-1"
                            defaultValue=""
                            onChange={(e) => {
                              if (e.target.value) handleUpgrade(r.id, e.target.value);
                              e.target.value = '';
                            }}
                          >
                            <option value="">Upgrade...</option>
                            {PLANS.filter((p) => p !== r.plan).map((p) => (
                              <option key={p} value={p}>{p}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleCancel(r.id)}
                            className="text-xs flex items-center gap-1 text-red-600 hover:bg-red-50 px-2 py-1 rounded"
                          >
                            <XCircle className="w-3 h-3" /> Cancel
                          </button>
                        </>
                      )}
                      {r.status === 'cancelled' && (
                        <button
                          onClick={() => handleUpgrade(r.id, 'standard')}
                          className="text-xs flex items-center gap-1 text-primary-600 hover:bg-primary-50 px-2 py-1 rounded"
                        >
                          <ArrowUpCircle className="w-3 h-3" /> Reactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No subscriptions found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
