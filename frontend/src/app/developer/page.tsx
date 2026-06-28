'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Users, Brain, CreditCard, Activity } from 'lucide-react';

export default function DeveloperDashboardPage() {
  const { t } = useLanguage();
  const [data, setData] = useState<{
    stats: {
      total_users: number;
      total_staff: number;
      active_subscriptions: number;
      total_ai_calls: number;
      total_tokens_used: number;
    };
    recent_audit: Array<{ action: string; resource?: string; actor_email?: string; created_at?: string }>;
  } | null>(null);

  useEffect(() => {
    api.getDeveloperDashboard().then(setData).catch(() => {});
  }, []);

  const stats = data?.stats ?? {
    total_users: 0,
    total_staff: 0,
    active_subscriptions: 0,
    total_ai_calls: 0,
    total_tokens_used: 0,
  };

  const cards = [
    { label: t.developer.totalUsers, value: stats.total_users, icon: Users, color: 'bg-blue-50 text-blue-600' },
    { label: t.developer.staffAccounts, value: stats.total_staff, icon: Users, color: 'bg-violet-50 text-violet-600' },
    { label: t.developer.activeSubs, value: stats.active_subscriptions, icon: CreditCard, color: 'bg-green-50 text-green-600' },
    { label: t.developer.aiCalls, value: stats.total_ai_calls, icon: Brain, color: 'bg-orange-50 text-orange-600' },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">{t.developer.title}</h1>
        <p className="text-sm text-gray-500 mb-8">{t.developer.subtitle}</p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {cards.map((card) => (
            <div key={card.label} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${card.color}`}>
                <card.icon className="w-5 h-5" />
              </div>
              <p className="text-2xl font-bold text-slate-800">{card.value}</p>
              <p className="text-sm text-gray-500">{card.label}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-violet-600" />
              <h2 className="font-semibold text-slate-800">{t.developer.tokenUsage}</h2>
            </div>
            <p className="text-3xl font-bold text-slate-800">{stats.total_tokens_used.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-1">{t.developer.tokensTotal}</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h2 className="font-semibold text-slate-800 mb-4">{t.developer.recentActivity}</h2>
            {!data?.recent_audit?.length ? (
              <p className="text-gray-400 text-sm">{t.developer.noActivity}</p>
            ) : (
              <div className="space-y-3">
                {data.recent_audit.map((item, i) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b border-gray-50 text-sm">
                    <div>
                      <p className="font-medium">{item.action}</p>
                      <p className="text-xs text-gray-400">{item.actor_email}</p>
                    </div>
                    <span className="text-xs text-gray-400">{item.resource || '—'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
