'use client';

import { useEffect, useState } from 'react';
import DeveloperSidebar from '@/components/DeveloperSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

interface PlatformSetting {
  key: string;
  value: Record<string, unknown>;
  category: string;
  description?: string;
}

export default function DeveloperSettingsPage() {
  const { t } = useLanguage();
  const [settings, setSettings] = useState<PlatformSetting[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.getDeveloperSettings().then(setSettings).catch(() => {});
  }, []);

  const grouped = settings.reduce<Record<string, PlatformSetting[]>>((acc, s) => {
    (acc[s.category] ||= []).push(s);
    return acc;
  }, {});

  const toggleFeature = async (setting: PlatformSetting) => {
    const newValue = { ...setting.value, enabled: !setting.value.enabled };
    setSaving(setting.key);
    try {
      await api.updateDeveloperSetting(setting.key, newValue);
      setSettings((prev) => prev.map((s) => (s.key === setting.key ? { ...s, value: newValue } : s)));
      setMessage(t.developer.saved);
    } catch {
      setMessage(t.common.error);
    } finally {
      setSaving(null);
    }
  };

  const updateNumeric = async (setting: PlatformSetting, field: string, raw: string) => {
    const num = Number(raw);
    if (Number.isNaN(num)) return;
    const newValue = { ...setting.value, [field]: num };
    setSaving(setting.key);
    try {
      await api.updateDeveloperSetting(setting.key, newValue);
      setSettings((prev) => prev.map((s) => (s.key === setting.key ? { ...s, value: newValue } : s)));
      setMessage(t.developer.saved);
    } catch {
      setMessage(t.common.error);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DeveloperSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">{t.developer.settings}</h1>
        <p className="text-sm text-gray-500 mb-8">{t.developer.settingsDesc}</p>

        {message && (
          <div className="bg-green-50 text-green-700 text-sm p-3 rounded-xl mb-6 border border-green-100">{message}</div>
        )}

        <div className="space-y-8">
          {Object.entries(grouped).map(([category, items]) => (
            <section key={category} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <h2 className="font-semibold text-slate-800 mb-4 capitalize">{category}</h2>
              <div className="space-y-4">
                {items.map((setting) => (
                  <div key={setting.key} className="flex items-start justify-between gap-4 py-3 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="font-medium text-sm text-slate-800">{setting.key}</p>
                      {setting.description && <p className="text-xs text-gray-500 mt-1">{setting.description}</p>}
                    </div>
                    <div className="shrink-0">
                      {'enabled' in setting.value && (
                        <button
                          onClick={() => toggleFeature(setting)}
                          disabled={saving === setting.key}
                          className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                            setting.value.enabled
                              ? 'bg-violet-100 text-violet-700'
                              : 'bg-gray-100 text-gray-500'
                          }`}
                        >
                          {setting.value.enabled ? 'ON' : 'OFF'}
                        </button>
                      )}
                      {'days' in setting.value && (
                        <input
                          type="number"
                          defaultValue={String(setting.value.days)}
                          onBlur={(e) => updateNumeric(setting, 'days', e.target.value)}
                          className="input-field w-24 text-sm"
                        />
                      )}
                      {'temperature' in setting.value && (
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="2"
                          defaultValue={String(setting.value.temperature)}
                          onBlur={(e) => updateNumeric(setting, 'temperature', e.target.value)}
                          className="input-field w-24 text-sm"
                        />
                      )}
                      {'model' in setting.value && (
                        <span className="text-sm text-gray-600">{String(setting.value.model)}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      </main>
    </div>
  );
}
