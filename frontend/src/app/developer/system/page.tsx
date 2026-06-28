'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

export default function DeveloperSystemPage() {
  const { t } = useLanguage();
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.getDeveloperSystemInfo().then(setInfo).catch(() => {});
  }, []);

  if (!info) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DeveloperSidebar />
        <main className="flex-1 p-8"><p className="text-gray-400">{t.common.loading}</p></main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-8">{t.developer.system}</h1>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 max-w-2xl">
          <dl className="space-y-4">
            {Object.entries(info).map(([key, value]) => (
              <div key={key} className="flex justify-between py-2 border-b border-gray-50">
                <dt className="text-sm text-gray-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                <dd className="text-sm font-medium text-slate-800">
                  {Array.isArray(value) ? value.join(', ') : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </main>
    </div>
  );
}
