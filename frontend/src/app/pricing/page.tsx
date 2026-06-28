'use client';

import Link from 'next/link';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import PageHero from '@/components/PageHero';
import SectionShell, { SectionHeader, HopeCard } from '@/components/SectionShell';
import SmartImage from '@/components/SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { Images } from '@/lib/images';
import { Check, Crown } from 'lucide-react';

export default function PricingPage() {
  const { t } = useLanguage();

  const plans = [
    { name: t.pricing.trial, price: '¥0', period: '7日間', features: [t.pricing.features.aiChat, t.pricing.features.hospitalSearch], cta: t.hero.cta, highlight: false },
    { name: t.pricing.standard, price: '¥980', period: t.pricing.perMonth, features: [t.pricing.features.aiChat, t.pricing.features.hospitalSearch, t.pricing.features.reminders], cta: 'プランを選択', highlight: false },
    { name: t.pricing.premium, price: '¥1,980', period: t.pricing.perMonth, features: [t.pricing.features.aiChat, t.pricing.features.hospitalSearch, t.pricing.features.reminders, t.pricing.features.family, t.pricing.features.analytics, t.pricing.features.priority], cta: 'プランを選択', highlight: true },
    { name: t.pricing.enterprise, price: 'お問い合わせ', period: '', features: ['クリニック管理', 'マルチユーザー', 'API連携', '専任サポート'], cta: 'お問い合わせ', highlight: false },
  ];

  return (
    <div className="min-h-screen pattern-bright">
      <Navbar />
      <PageHero title={t.pricing.title} subtitle="継続的なケアが、回復への力になります" image={Images.pricingHero.primary} imageFallback={Images.pricingHero.fallback} compact />

      <SectionShell variant="gradient">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {plans.map((plan) => (
            <div key={plan.name} className={`card-bright flex flex-col relative ${plan.highlight ? 'ring-2 ring-primary-300 shadow-glow scale-[1.02]' : ''}`}>
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary-400 to-mint-400 text-white text-xs px-4 py-1 rounded-full flex items-center gap-1 shadow-soft">
                  <Crown className="w-3 h-3" /> おすすめ
                </div>
              )}
              <h3 className="font-serif font-semibold text-primary-800">{plan.name}</h3>
              <div className="my-3">
                <span className="text-3xl font-bold text-primary-600">{plan.price}</span>
                {plan.period && <span className="text-sm text-slate-400">{plan.period}</span>}
              </div>
              <ul className="space-y-2 mb-6 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-slate-600">
                    <Check className="w-4 h-4 text-mint-500" />{f}
                  </li>
                ))}
              </ul>
              <Link href={plan.name === t.pricing.enterprise ? '/contact' : '/register'} className={`text-center py-3 rounded-2xl text-sm font-medium ${plan.highlight ? 'btn-primary' : 'btn-secondary'}`}>
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-14">
          <HopeCard
            message="健康への投資は、未来の笑顔への贈り物です。"
            submessage="無理のないペースで、あなたに合ったプランをお選びください。"
            image={Images.pricingHero.primary}
            imageFallback={Images.pricingHero.fallback}
          />
        </div>
      </SectionShell>
      <Footer />
    </div>
  );
}
