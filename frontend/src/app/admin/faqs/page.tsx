'use client';

import { useEffect, useState } from 'react';
import AdminSidebar from '@/components/AdminSidebar';
import { useLanguage } from '@/context/LanguageContext';
import { api, FAQ } from '@/lib/api';
import { HelpCircle, Plus } from 'lucide-react';

export default function AdminFAQsPage() {
  const { t, locale } = useLanguage();
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getFAQs().then(setFaqs).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminSidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-primary-800 flex items-center gap-2">
            <HelpCircle className="w-6 h-6" /> {t.admin.faqs}
          </h1>
          <button className="btn-primary text-sm flex items-center gap-2">
            <Plus className="w-4 h-4" /> FAQ追加
          </button>
        </div>

        {loading ? (
          <p className="text-gray-500">{t.common.loading}</p>
        ) : (
          <div className="space-y-4">
            {faqs.map((faq) => (
              <div key={faq.id} className="bg-white rounded-2xl p-6 shadow-sm border">
                <span className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded">{faq.category}</span>
                <h3 className="font-semibold text-primary-800 mt-2">
                  {locale === 'ja' ? faq.question : (faq.question_en || faq.question)}
                </h3>
                <p className="text-gray-600 text-sm mt-2 leading-relaxed">
                  {locale === 'ja' ? faq.answer : (faq.answer_en || faq.answer)}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
