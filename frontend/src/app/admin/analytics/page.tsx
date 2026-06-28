'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminAnalyticsPage() {
  const { t } = useLanguage();
  const [analytics, setAnalytics] = useState({
    total_users: 0,
    total_reservations: 0,
    confirmed_reservations: 0,
    total_ai_calls: 0,
    total_tokens_used: 0,
  });

  useEffect(() => {
    api.getAnalytics().then(setAnalytics).catch(() => {});
  }, []);

  const chartData = [
    { name: 'Users', value: analytics.total_users },
    { name: 'Reservations', value: analytics.total_reservations },
    { name: 'Confirmed', value: analytics.confirmed_reservations },
    { name: 'AI Calls', value: analytics.total_ai_calls },
  ];

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-8">{t.admin.analytics}</h1>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Total Users', value: analytics.total_users },
            { label: 'Reservations', value: analytics.total_reservations },
            { label: 'AI Calls', value: analytics.total_ai_calls },
            { label: 'Tokens Used', value: analytics.total_tokens_used?.toLocaleString() },
          ].map((item) => (
            <div key={item.label} className="bg-white rounded-2xl p-6 shadow-sm border">
              <p className="text-2xl font-bold text-primary-800">{item.value}</p>
              <p className="text-sm text-gray-500">{item.label}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border">
          <h2 className="font-semibold text-primary-800 mb-4">Platform Overview</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#1a365d" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </main>
    </div>
  );
}
