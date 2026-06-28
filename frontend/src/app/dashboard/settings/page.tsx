'use client';

import { useLanguage } from '@/context/LanguageContext';
import { Settings, Globe, Bell } from 'lucide-react';

export default function SettingsPage() {
  const { t, locale, setLocale } = useLanguage();

  return (
    <main className="p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6 flex items-center gap-2">
          <Settings className="w-6 h-6" /> {t.dashboard.settings}
        </h1>

        <div className="space-y-6 max-w-lg">
          <div className="card">
            <h2 className="font-semibold text-primary-800 mb-4 flex items-center gap-2">
              <Globe className="w-4 h-4" /> {t.common.language}
            </h2>
            <div className="flex gap-3">
              <button
                onClick={() => setLocale('ja')}
                className={`px-4 py-2 rounded-lg text-sm ${locale === 'ja' ? 'bg-primary-700 text-white' : 'bg-gray-100'}`}
              >
                日本語
              </button>
              <button
                onClick={() => setLocale('en')}
                className={`px-4 py-2 rounded-lg text-sm ${locale === 'en' ? 'bg-primary-700 text-white' : 'bg-gray-100'}`}
              >
                English
              </button>
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold text-primary-800 mb-4 flex items-center gap-2">
              <Bell className="w-4 h-4" /> 通知設定
            </h2>
            <div className="space-y-3">
              {['予約リマインダー', '健康チェックイン', 'AIフォローアップ'].map((label) => (
                <label key={label} className="flex items-center justify-between text-sm">
                  <span>{label}</span>
                  <input type="checkbox" defaultChecked className="rounded" />
                </label>
              ))}
            </div>
          </div>
        </div>
    </main>
  );
}
