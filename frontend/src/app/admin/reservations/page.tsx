'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Calendar, Clock } from 'lucide-react';

interface Reservation {
  id: string;
  date?: string;
  time: string;
  status: string;
  patient_name?: string;
  department?: string;
}

export default function AdminReservationsPage() {
  const { t } = useLanguage();
  const [reservations, setReservations] = useState<Reservation[]>([]);

  useEffect(() => {
    api.getTodayReservations().then(setReservations).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6 flex items-center gap-2">
          <Calendar className="w-6 h-6" /> {t.admin.todayReservations}
        </h1>

        {reservations.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">本日の予約はありません</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {reservations.map((r) => (
              <div key={r.id} className="bg-white rounded-2xl p-6 shadow-sm border flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center">
                    <Clock className="w-5 h-5 text-primary-700" />
                  </div>
                  <div>
                    <p className="font-semibold text-primary-800">{r.patient_name || 'Patient'}</p>
                    <p className="text-sm text-gray-500">
                      {r.time} {r.department && `· ${r.department}`}
                    </p>
                  </div>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full ${
                  r.status === 'confirmed' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'
                }`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
