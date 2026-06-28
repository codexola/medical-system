'use client';

import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { Clock, User } from 'lucide-react';

const SCHEDULES = [
  { doctor: 'Dr. Suzuki', specialty: 'Internal Medicine', days: 'Mon-Fri', hours: '9:00-17:00', slots: 30 },
  { doctor: 'Dr. Tanaka', specialty: 'Internal Medicine', days: 'Mon-Fri', hours: '9:00-17:00', slots: 30 },
];

export default function AdminSchedulesPage() {
  const { t } = useLanguage();

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6 flex items-center gap-2">
          <Clock className="w-6 h-6" /> {t.admin.schedules}
        </h1>

        <div className="grid md:grid-cols-2 gap-6">
          {SCHEDULES.map((s) => (
            <div key={s.doctor} className="bg-white rounded-2xl p-6 shadow-sm border">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-primary-700" />
                </div>
                <div>
                  <h3 className="font-semibold text-primary-800">{s.doctor}</h3>
                  <p className="text-sm text-gray-500">{s.specialty}</p>
                </div>
              </div>
              <div className="space-y-2 text-sm text-gray-600">
                <p><span className="text-gray-400">Days:</span> {s.days}</p>
                <p><span className="text-gray-400">Hours:</span> {s.hours}</p>
                <p><span className="text-gray-400">Slot:</span> {s.slots} min</p>
              </div>
              <button className="mt-4 text-sm text-primary-700 hover:underline">Edit Schedule</button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
