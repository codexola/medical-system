'use client';

import Link from 'next/link';
import { MapPin, Star, Navigation, Clock } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';

export interface ChatHospital {
  id?: string;
  name: string;
  address: string;
  distance_km?: number;
  phone?: string;
  rating?: number;
  reason?: string;
  travel_time_minutes?: number;
  directions_url?: string;
  emergency_available?: boolean;
}

export interface ChatPharmacy {
  id?: string;
  name: string;
  address: string;
  distance_km?: number;
  phone?: string;
  rating?: number;
}

export interface ChatSpecialist {
  name?: string;
  rank?: string;
  specialty?: string;
  experience_years?: number;
  phone?: string;
  office_address?: string;
  hospital_name?: string;
  route_summary?: string;
  directions_url?: string;
}

interface Props {
  hospitals: ChatHospital[];
  pharmacies?: ChatPharmacy[];
  specialists?: ChatSpecialist[];
  symptoms?: string;
  showFilters?: boolean;
  onFilter?: (sortBy: 'nearest' | 'specialty' | 'rating', excellenceOnly?: boolean) => void;
  activeFilter?: string;
  loading?: boolean;
}

export default function HospitalCardList({
  hospitals,
  pharmacies = [],
  specialists = [],
  symptoms,
  showFilters,
  onFilter,
  activeFilter = 'nearest',
  loading,
}: Props) {
  const { t, locale } = useLanguage();

  if (!hospitals.length && !pharmacies.length && !showFilters) return null;

  const filters = [
    { id: 'nearest' as const, label: t.dashboard.filterNearest },
    { id: 'specialty' as const, label: t.dashboard.filterSpecialty },
    { id: 'rating' as const, label: t.dashboard.filterRating },
  ];

  return (
    <div className="mt-3 space-y-3 max-w-lg">
      {showFilters && onFilter && (
        <div className="flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f.id}
              type="button"
              disabled={loading}
              onClick={() => onFilter(f.id)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                activeFilter === f.id
                  ? 'bg-primary-500 text-white border-primary-500'
                  : 'bg-white text-primary-700 border-primary-200 hover:bg-sky-50'
              }`}
            >
              {f.label}
            </button>
          ))}
          <button
            type="button"
            disabled={loading}
            onClick={() => onFilter('rating', true)}
            className="text-xs px-3 py-1.5 rounded-full border border-gold-200 bg-gold-50 text-gold-700 hover:bg-gold-100"
          >
            {t.dashboard.filterExcellence}
          </button>
        </div>
      )}

      {hospitals.map((h, i) => (
        <div key={h.id || i} className="bg-sky-50/80 border border-sky-100 rounded-xl p-3 text-sm">
          <div className="flex justify-between items-start gap-2 mb-1">
            <p className="font-semibold text-primary-800">{h.name}</p>
            {h.rating != null && (
              <span className="flex items-center gap-0.5 text-gold-500 text-xs shrink-0">
                <Star className="w-3 h-3 fill-current" />
                {h.rating}
              </span>
            )}
          </div>
          <p className="text-slate-600 flex items-start gap-1 text-xs">
            <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {h.address}
            {h.distance_km != null && <span className="text-primary-600 ml-1">({h.distance_km}km)</span>}
          </p>
          {h.phone && (
            <p className="text-xs text-slate-700 mt-1">
              📞 <a href={`tel:${h.phone.replace(/\s/g, '')}`} className="hover:underline">{h.phone}</a>
            </p>
          )}
          {h.travel_time_minutes != null && (
            <p className="text-xs text-primary-700 flex items-center gap-1 mt-1">
              <Clock className="w-3.5 h-3.5" />
              {t.dashboard.travelTime}: {h.travel_time_minutes}{t.dashboard.minutes}
            </p>
          )}
          {h.reason && (
            <p className="text-xs text-mint-700 bg-mint-50 px-2 py-0.5 rounded mt-2 inline-block">{h.reason}</p>
          )}
          {h.directions_url && (
            <a
              href={h.directions_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary-600 mt-2 hover:underline"
            >
              <Navigation className="w-3.5 h-3.5" />
              {t.dashboard.openMaps}
            </a>
          )}
        </div>
      ))}

      {pharmacies.length > 0 && (
        <p className="text-xs font-semibold text-primary-700 pt-1">
          {locale === 'ja' ? 'お近くの薬局・ドラッグストア' : 'Nearby pharmacies'}
        </p>
      )}
      {pharmacies.map((p, i) => (
        <div key={p.id || `pharmacy-${i}`} className="bg-mint-50/80 border border-mint-100 rounded-xl p-3 text-sm">
          <p className="font-semibold text-primary-800">{p.name}</p>
          <p className="text-slate-600 flex items-start gap-1 text-xs mt-1">
            <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {p.address}
            {p.distance_km != null && <span className="text-primary-600 ml-1">({p.distance_km}km)</span>}
          </p>
          {p.phone && (
            <p className="text-xs text-slate-700 mt-1">
              📞 <a href={`tel:${p.phone.replace(/\s/g, '')}`} className="hover:underline">{p.phone}</a>
            </p>
          )}
        </div>
      ))}

      {specialists.length > 0 && (
        <p className="text-xs font-semibold text-primary-700 pt-2">
          {locale === 'ja' ? '専門医のご案内' : 'Specialist guidance'}
        </p>
      )}
      {specialists.map((s, i) => (
        <div key={`spec-${i}`} className="bg-white border border-primary-100 rounded-xl p-3 text-sm">
          <p className="font-semibold text-primary-800">{s.name}</p>
          <p className="text-xs text-slate-600 mt-1">
            {s.rank} · {s.specialty}
            {s.experience_years != null && (
              <span> · {locale === 'ja' ? `${s.experience_years}年の経験` : `${s.experience_years} yrs`}</span>
            )}
          </p>
          <p className="text-xs text-slate-600 mt-1">{s.hospital_name}</p>
          <p className="text-xs text-slate-600 flex items-start gap-1 mt-1">
            <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {s.office_address}
          </p>
          {s.phone && (
            <p className="text-xs text-slate-700 mt-1">
              📞 <a href={`tel:${s.phone.replace(/\s/g, '')}`} className="hover:underline">{s.phone}</a>
            </p>
          )}
          {s.route_summary && (
            <p className="text-xs text-primary-700 mt-1">🚗 {s.route_summary}</p>
          )}
          {s.directions_url && (
            <a
              href={s.directions_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary-600 mt-2 hover:underline"
            >
              <Navigation className="w-3.5 h-3.5" />
              {t.dashboard.openMaps}
            </a>
          )}
        </div>
      ))}

      {showFilters && symptoms && (
        <Link
          href={`/dashboard/hospitals?symptoms=${encodeURIComponent(symptoms)}`}
          className="text-xs text-primary-600 hover:underline block text-center"
        >
          {t.dashboard.viewAllHospitals}
        </Link>
      )}
    </div>
  );
}
