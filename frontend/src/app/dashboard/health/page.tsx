'use client';

import { useState } from 'react';
import SmartImage from '@/components/SmartImage';
import { HopeCard } from '@/components/SectionShell';
import { useLanguage } from '@/context/LanguageContext';
import { Images } from '@/lib/images';
import { Activity, Thermometer, Heart } from 'lucide-react';

export default function HealthTimelinePage() {
  const { t } = useLanguage();
  const [form, setForm] = useState({ mood: 3, symptoms: '', temperature: '', medication_taken: false, notes: '' });
  const [saved, setSaved] = useState(false);

  return (
    <main className="p-5 md:p-8 max-w-4xl">
        <div className="relative h-40 rounded-3xl overflow-hidden mb-6 shadow-soft ring-2 ring-white">
          <SmartImage src={Images.featureHealth.primary} fallback={Images.featureHealth.fallback} alt="" fill className="object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-white/90 to-transparent flex items-center px-6">
            <div>
              <h1 className="font-serif text-2xl font-bold text-primary-800">{t.dashboard.healthTimeline}</h1>
              <p className="text-sm text-slate-500 mt-1">小さな記録が、大きな回復につながります</p>
            </div>
          </div>
        </div>

        <HopeCard
          message="今日の体調を記録することは、自分を大切にする行動です。"
          submessage="良い日も、つらい日も、どちらも大切な記録になります。"
          image={Images.patientHope.primary}
          imageFallback={Images.patientHope.fallback}
        />

        <div className="grid lg:grid-cols-2 gap-6 mt-6">
          <div className="card-bright">
            <h2 className="font-semibold text-primary-800 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-mint-500" />
              今日のチェックイン
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-600 mb-2 block">今日の気分 (1-5)</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      onClick={() => setForm({ ...form, mood: n })}
                      className={`w-11 h-11 rounded-2xl text-sm font-medium transition-all ${
                        form.mood === n ? 'bg-gradient-to-br from-primary-400 to-mint-400 text-white shadow-soft scale-110' : 'bg-white border-2 border-primary-100 text-slate-500'
                      }`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-600 mb-1 block">症状・気になること</label>
                <input value={form.symptoms} onChange={(e) => setForm({ ...form, symptoms: e.target.value })} className="input-field" placeholder="つらいときは、そのまま書いてください" />
              </div>
              <div>
                <label className="text-sm text-slate-600 mb-1 flex items-center gap-1">
                  <Thermometer className="w-4 h-4" /> 体温 (°C)
                </label>
                <input type="number" step="0.1" value={form.temperature} onChange={(e) => setForm({ ...form, temperature: e.target.value })} className="input-field" />
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input type="checkbox" checked={form.medication_taken} onChange={(e) => setForm({ ...form, medication_taken: e.target.checked })} className="rounded accent-primary-500" />
                今日のお薬を服用しました
              </label>
              <button onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 3000); }} className="btn-primary w-full">
                {saved ? '記録しました ✓ お疲れさまでした' : 'チェックインを保存'}
              </button>
            </div>
          </div>

          <div className="card-bright">
            <h2 className="font-semibold text-primary-800 mb-4 flex items-center gap-2">
              <Heart className="w-5 h-5 text-peach-400 fill-peach-200" />
              健康タイムライン
            </h2>
            <div className="space-y-4">
              {[
                { date: '今日', mood: 3, note: 'チェックインをお待ちしています' },
                { date: '昨日', mood: 4, note: '体調良好 — 素晴らしいです' },
                { date: '2日前', mood: 2, note: '軽い頭痛 — 無理せず休みましょう' },
              ].map((entry, i) => (
                <div key={i} className="flex gap-4 items-start border-l-4 border-mint-200 pl-4 py-1">
                  <div className="text-xs text-slate-400 w-14">{entry.date}</div>
                  <div>
                    <span className="text-sm font-medium text-primary-700">気分 {entry.mood}/5</span>
                    <p className="text-sm text-slate-500">{entry.note}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
    </main>
  );
}
