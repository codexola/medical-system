'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Users, Calendar, Brain, CreditCard, Bell } from 'lucide-react';

export default function AdminDashboardPage() {
  const { t } = useLanguage();
  const [stats, setStats] = useState({
    today_reservations: 0,
    total_patients: 0,
    active_subscriptions: 0,
    ai_calls_today: 0,
  });

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(() => {});
  }, []);

  const cards = [
    { label: t.admin.todayReservations, value: stats.today_reservations, icon: Calendar, color: 'bg-blue-50 text-blue-600' },
    { label: 'Total Patients', value: stats.total_patients, icon: Users, color: 'bg-green-50 text-green-600' },
    { label: 'Active Subscriptions', value: stats.active_subscriptions, icon: CreditCard, color: 'bg-purple-50 text-purple-600' },
    { label: t.admin.aiLogs, value: stats.ai_calls_today, icon: Brain, color: 'bg-orange-50 text-orange-600' },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-8">{t.admin.title}</h1>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {cards.map((card) => (
            <div key={card.label} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${card.color}`}>
                <card.icon className="w-5 h-5" />
              </div>
              <p className="text-2xl font-bold text-primary-800">{card.value}</p>
              <p className="text-sm text-gray-500">{card.label}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h2 className="font-semibold text-primary-800 mb-4">{t.admin.todayReservations}</h2>
            <TodayReservations />
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h2 className="font-semibold text-primary-800 mb-4">Recent AI Activity</h2>
            <RecentAILogs />
          </div>
        </div>
      </main>
    </div>
  );
}

function TodayReservations() {
  const [reservations, setReservations] = useState<Array<{ id: string; time: string; patient_name?: string; status: string }>>([]);

  useEffect(() => {
    api.getTodayReservations().then(setReservations).catch(() => {});
  }, []);

  if (reservations.length === 0) {
    return <p className="text-gray-400 text-sm">本日の予約はありません</p>;
  }

  return (
    <div className="space-y-3">
      {reservations.map((r) => (
        <div key={r.id} className="flex justify-between items-center py-2 border-b border-gray-50">
          <div>
            <p className="text-sm font-medium">{r.patient_name || 'Patient'}</p>
            <p className="text-xs text-gray-400">{r.time}</p>
          </div>
          <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">{r.status}</span>
        </div>
      ))}
    </div>
  );
}

function RecentAILogs() {
  const [logs, setLogs] = useState<Array<{ provider: string; model: string; tokens?: number; latency_ms?: number }>>([]);

  useEffect(() => {
    api.getAILogs().then((data) => setLogs(data.slice(0, 5))).catch(() => {});
  }, []);

  if (logs.length === 0) {
    return <p className="text-gray-400 text-sm">AIログがありません</p>;
  }

  return (
    <div className="space-y-3">
      {logs.map((log, i) => (
        <div key={i} className="flex justify-between items-center py-2 border-b border-gray-50 text-sm">
          <div>
            <p className="font-medium">{log.model}</p>
            <p className="text-xs text-gray-400">{log.provider}</p>
          </div>
          <div className="text-right text-xs text-gray-500">
            <p>{log.tokens} tokens</p>
            <p>{log.latency_ms}ms</p>
          </div>
        </div>
      ))}
    </div>
  );
}
