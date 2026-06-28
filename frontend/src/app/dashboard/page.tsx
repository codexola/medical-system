'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import BrightGreeting from '@/components/BrightGreeting';
import SmartImage from '@/components/SmartImage';
import { HopeCard } from '@/components/SectionShell';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Images } from '@/lib/images';
import { Calendar, MessageCircle, MapPin, Activity, ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const { t } = useLanguage();
  const [profile, setProfile] = useState<{ name?: string }>({});
  const [subscription, setSubscription] = useState<{ active: boolean; trial_end?: string }>({ active: false });

  useEffect(() => {
    api.getProfile().then(setProfile).catch(() => {});
    api.getSubscriptionStatus().then(setSubscription).catch(() => {});
  }, []);

  const actions = [
    { href: '/dashboard/chat', icon: MessageCircle, label: t.dashboard.chat, img: Images.symptomCheck, gradient: 'from-sky-400 to-primary-400' },
    { href: '/dashboard/reservations', icon: Calendar, label: t.dashboard.reservations, img: Images.featureReservation, gradient: 'from-mint-400 to-mint-500' },
    { href: '/dashboard/hospitals', icon: MapPin, label: t.dashboard.hospitals, img: Images.featureHospital, gradient: 'from-peach-300 to-peach-400' },
    { href: '/dashboard/health', icon: Activity, label: t.dashboard.healthTimeline, img: Images.featureHealth, gradient: 'from-sunshine-300 to-peach-300' },
  ];

  return (
    <main className="p-5 md:p-8 overflow-auto max-w-5xl">
        <BrightGreeting name={profile.name} />

        {subscription.trial_end && subscription.active && (
          <div className="card-hope mb-6 text-sm text-mint-700">
            無料トライアル中（{new Date(subscription.trial_end).toLocaleDateString('ja-JP')}まで）— 焦らず、ご自身のペースでお試しください。
          </div>
        )}

        <p className="text-slate-500 text-sm mb-6 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-mint-400 animate-pulse" />
          {t.dashboard.gentleReminder}
        </p>

        <div className="grid sm:grid-cols-2 gap-4 mb-8">
          {actions.map((a) => (
            <Link key={a.href} href={a.href} className="group card-bright overflow-hidden !p-0 flex flex-col">
              <div className="relative h-32 overflow-hidden">
                <SmartImage src={a.img.primary} fallback={a.img.fallback} alt="" fill className="object-cover group-hover:scale-105 transition-transform duration-500" />
                <div className={`absolute inset-0 bg-gradient-to-t ${a.gradient} opacity-40`} />
              </div>
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <a.icon className="w-5 h-5 text-primary-500" />
                  <span className="font-medium text-primary-800">{a.label}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-primary-300 group-hover:text-primary-500 transition-colors" />
              </div>
            </Link>
          ))}
        </div>

        <HopeCard
          message={t.dashboard.greetingHope}
          submessage="今日の体調を記録して、小さな一歩を積み重ねましょう。"
          image={Images.consultation.primary}
          imageFallback={Images.consultation.fallback}
        />
    </main>
  );
}
