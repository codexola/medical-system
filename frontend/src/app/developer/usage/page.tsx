'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

export default function DeveloperUsagePage() {
  const { t } = useLanguage();
  const [usage, setUsage] = useState<{
    ai_by_provider: Array<{ provider: string; calls: number; tokens: number }>;
    ai_by_model: Array<{ model: string; calls: number; tokens: number }>;
    users_by_role: Array<{ role: string; count: number }>;
    subscriptions_by_plan: Array<{ plan: string; count: number }>;
  } | null>(null);

  useEffect(() => {
    api.getDeveloperUsage().then(setUsage).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">{t.developer.usage}</h1>

        <div className="grid lg:grid-cols-2 gap-6">
          <UsageTable title={t.developer.aiByProvider} rows={usage?.ai_by_provider.map((r) => ({
            label: r.provider,
            calls: r.calls,
            tokens: r.tokens,
          })) ?? []} />
          <UsageTable title={t.developer.aiByModel} rows={usage?.ai_by_model.map((r) => ({
            label: r.model,
            calls: r.calls,
            tokens: r.tokens,
          })) ?? []} />
          <UsageTable title={t.developer.usersByRole} rows={usage?.users_by_role.map((r) => ({
            label: r.role,
            calls: r.count,
          })) ?? []} showTokens={false} />
          <UsageTable title={t.developer.subsByPlan} rows={usage?.subscriptions_by_plan.map((r) => ({
            label: r.plan,
            calls: r.count,
          })) ?? []} showTokens={false} />
        </div>
      </main>
    </div>
  );
}

function UsageTable({
  title,
  rows,
  showTokens = true,
}: {
  title: string;
  rows: Array<{ label: string; calls: number; tokens?: number }>;
  showTokens?: boolean;
}) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h2 className="font-semibold text-slate-800 mb-4">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-gray-400 text-sm">—</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pb-2">Name</th>
              <th className="pb-2">Count</th>
              {showTokens && <th className="pb-2">Tokens</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-b border-gray-50">
                <td className="py-2">{row.label}</td>
                <td className="py-2">{row.calls}</td>
                {showTokens && <td className="py-2">{(row.tokens ?? 0).toLocaleString()}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
