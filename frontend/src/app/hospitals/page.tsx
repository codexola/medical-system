'use client';

import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import PageHero from '@/components/PageHero';
import SectionShell, { SectionHeader, HopeCard } from '@/components/SectionShell';
import SmartImage from '@/components/SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { Images } from '@/lib/images';
import { MapPin, Shield, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function HospitalsPublicPage() {
  const { t } = useLanguage();
  const [hospitals, setHospitals] = useState<Array<{ id: string; name: string; prefecture: string; city: string; departments: string[]; emergency_available: boolean }>>([]);

  useEffect(() => {
    api.listHospitals('東京都').then(setHospitals).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen pattern-bright">
      <Navbar />
      <PageHero
        title={t.nav.hospitals}
        subtitle="あなたに合った医療機関へ、やさしくご案内します。受診は回復への大切な一歩です。"
        image={Images.hospitalBanner.primary}
        imageFallback={Images.hospitalBanner.fallback}
      />

      <SectionShell variant="white">
        <div className="grid md:grid-cols-3 gap-5 mb-12">
          {[
            { icon: Search, title: 'AI推薦', desc: '症状と距離から、安心できる病院をご提案' },
            { icon: MapPin, title: '近くの病院', desc: 'すぐに頼れる医療機関を検索' },
            { icon: Shield, title: '救急対応', desc: '緊急時も、適切な施設をご案内' },
          ].map((item) => (
            <div key={item.title} className="card-bright text-center">
              <div className="w-14 h-14 bg-sky-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <item.icon className="w-7 h-7 text-primary-500" />
              </div>
              <h3 className="font-semibold text-primary-800 mb-1">{item.title}</h3>
              <p className="text-slate-500 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>

        <div className="relative rounded-3xl overflow-hidden mb-10 h-56 shadow-soft ring-2 ring-white">
          <SmartImage src={Images.featureHospital.primary} fallback={Images.featureHospital.fallback} alt="" fill className="object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-white/90 via-transparent to-transparent flex items-end p-6">
            <p className="text-primary-800 font-medium">笑顔で迎えてくれる医療機関を、一緒に見つけましょう</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {hospitals.map((h) => (
            <div key={h.id} className="card-bright hover:shadow-glow transition-shadow">
              <h3 className="font-semibold text-primary-800 mb-2">{h.name}</h3>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                <MapPin className="w-4 h-4" />{h.prefecture} {h.city}
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {(h.departments || []).slice(0, 3).map((d) => (
                  <span key={d} className="text-xs bg-sky-50 text-primary-600 px-2 py-0.5 rounded-full">{d}</span>
                ))}
              </div>
              {h.emergency_available && (
                <span className="text-xs bg-peach-50 text-peach-600 px-2 py-1 rounded-full inline-flex items-center gap-1">
                  <Shield className="w-3 h-3" /> 救急対応
                </span>
              )}
            </div>
          ))}
        </div>
      </SectionShell>

      <SectionShell variant="mint" className="!py-12">
        <HopeCard
          message="受診をためらわないでください。早めの相談が、安心への近道です。"
          image={Images.doctor.primary}
          imageFallback={Images.doctor.fallback}
        />
      </SectionShell>
      <Footer />
    </div>
  );
}
