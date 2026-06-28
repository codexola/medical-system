'use client';

import { useEffect, useState } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import HospitalCardList, { ChatHospital } from '@/components/HospitalCardList';

export default function HospitalsPage() {
  const { t } = useLanguage();
  const [symptoms, setSymptoms] = useState('');
  const [hospitals, setHospitals] = useState<ChatHospital[]>([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'nearest' | 'specialty' | 'rating'>('nearest');
  const [excellenceOnly, setExcellenceOnly] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get('symptoms');
    if (q) {
      setSymptoms(q);
      runSearch(q, 'nearest', false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runSearch = async (
    query: string,
    sort: 'nearest' | 'specialty' | 'rating',
    excellence: boolean,
  ) => {
    setLoading(true);
    setSortBy(sort);
    setExcellenceOnly(excellence);
    try {
      const results = await api.filterHospitals({
        symptoms: query || 'general',
        sort_by: sort,
        excellence_only: excellence,
      });
      setHospitals(results);
    } catch {
      setHospitals([]);
    } finally {
      setLoading(false);
    }
  };

  const search = () => runSearch(symptoms || 'general', sortBy, excellenceOnly);

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold text-primary-800 mb-2">{t.dashboard.hospitals}</h1>
      <p className="text-sm text-gray-500 mb-6">{t.dashboard.hospitalsHint}</p>

      <div className="card mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">{t.dashboard.symptomsLabel}</label>
        <div className="flex gap-3 mb-4">
          <input
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder={t.dashboard.symptomsPlaceholder}
            className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
          />
          <button onClick={search} disabled={loading} className="btn-primary whitespace-nowrap">
            {loading ? t.common.loading : t.common.search}
          </button>
        </div>

        <p className="text-xs text-gray-500 mb-2">{t.dashboard.filterLabel}</p>
        <div className="flex flex-wrap gap-2">
          {([
            { id: 'nearest' as const, label: t.dashboard.filterNearest },
            { id: 'specialty' as const, label: t.dashboard.filterSpecialty },
            { id: 'rating' as const, label: t.dashboard.filterRating },
          ]).map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => runSearch(symptoms || 'general', f.id, false)}
              className={`text-sm px-4 py-2 rounded-full border transition-colors ${
                sortBy === f.id && !excellenceOnly
                  ? 'bg-primary-500 text-white border-primary-500'
                  : 'bg-white text-primary-700 border-primary-200 hover:bg-sky-50'
              }`}
            >
              {f.label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => runSearch(symptoms || 'general', 'rating', true)}
            className={`text-sm px-4 py-2 rounded-full border transition-colors ${
              excellenceOnly
                ? 'bg-gold-500 text-white border-gold-500'
                : 'border-gold-200 bg-gold-50 text-gold-700 hover:bg-gold-100'
            }`}
          >
            {t.dashboard.filterExcellence}
          </button>
        </div>
      </div>

      {hospitals.length > 0 ? (
        <HospitalCardList hospitals={hospitals} />
      ) : (
        !loading && <p className="text-gray-400 text-sm text-center py-8">{t.dashboard.noHospitals}</p>
      )}
    </main>
  );
}
