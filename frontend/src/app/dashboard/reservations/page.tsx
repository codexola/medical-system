'use client';

import { useEffect, useState } from 'react';
import DashboardHeader from '@/components/DashboardHeader';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Images } from '@/lib/images';
import { Calendar, Clock, CheckCircle, XCircle } from 'lucide-react';

interface Reservation {
  id: string;
  date: string;
  time: string;
  status: string;
  department?: string;
}

export default function ReservationsPage() {
  const { t } = useLanguage();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReservations().then(setReservations).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const statusIcon = (status: string) => {
    if (status === 'confirmed') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'cancelled') return <XCircle className="w-4 h-4 text-red-500" />;
    return <Clock className="w-4 h-4 text-amber-500" />;
  };

  return (
    <main className="p-6 md:p-8">
        <DashboardHeader title={t.dashboard.reservations} subtitle="予約の確認・管理" image={Images.featureReservation.primary} imageFallback={Images.featureReservation.fallback} />

        {loading ? (
          <p className="text-gray-500">{t.common.loading}</p>
        ) : reservations.length === 0 ? (
          <div className="card text-center py-12">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">予約がありません</p>
            <p className="text-sm text-gray-400 mt-2">AIチャットから予約できます</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reservations.map((r) => (
              <div key={r.id} className="card flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {statusIcon(r.status)}
                  <div>
                    <p className="font-medium text-primary-800">
                      {new Date(r.date).toLocaleDateString('ja-JP')} {r.time}
                    </p>
                    {r.department && <p className="text-sm text-gray-500">{r.department}</p>}
                  </div>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full ${
                  r.status === 'confirmed' ? 'bg-green-50 text-green-700' :
                  r.status === 'cancelled' ? 'bg-red-50 text-red-700' :
                  'bg-amber-50 text-amber-700'
                }`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        )}
    </main>
  );
}
