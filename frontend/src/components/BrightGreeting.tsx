'use client';

import SmartImage from './SmartImage';
import { Images } from '@/lib/images';
import { Sun, Heart, Sparkles } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';

interface BrightGreetingProps {
  name?: string;
}

function getGreeting(hour: number, locale: string): string {
  if (locale === 'ja') {
    if (hour < 11) return 'おはようございます';
    if (hour < 17) return 'こんにちは';
    return 'こんばんは';
  }
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function BrightGreeting({ name }: BrightGreetingProps) {
  const { locale } = useLanguage();
  const hour = new Date().getHours();
  const greeting = getGreeting(hour, locale);

  const messages = locale === 'ja'
    ? {
        main: '一歩ずつ、必ず良くなれます。',
        sub: '不安なときも、私たちがやさしく寄り添います。気になることがあれば、いつでもご相談ください。',
        cta: '今日もあなたの健康を応援しています',
      }
    : {
        main: 'Step by step, things can get better.',
        sub: 'When you feel anxious, we are here with gentle support. Please reach out anytime.',
        cta: 'We are cheering for your health today',
      };

  return (
    <div className="greeting-banner mb-8 animate-fade-up">
      <div className="absolute inset-0">
        <SmartImage
          src={Images.dashboardGreeting.primary}
          fallback={Images.dashboardGreeting.fallback}
          alt=""
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-r from-white/95 via-white/85 to-white/40" />
      </div>

      <div className="relative flex flex-col md:flex-row items-center gap-6 p-6 md:p-8">
        <div className="relative w-24 h-24 md:w-28 md:h-28 rounded-full overflow-hidden ring-4 ring-primary-200 shadow-glow flex-shrink-0 animate-gentle-float">
          <SmartImage
            src={Images.mascot.primary}
            fallback={Images.mascot.fallback}
            alt="Health assistant"
            fill
            className="object-cover"
          />
        </div>

        <div className="flex-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2 text-primary-500 text-sm font-medium mb-1">
            <Sun className="w-4 h-4 text-sunshine-400" />
            {greeting}{name ? `、${name}さん` : ''}
          </div>
          <h1 className="font-serif text-2xl md:text-3xl font-bold text-primary-800 mb-2">
            {messages.main}
          </h1>
          <p className="text-slate-600 leading-relaxed max-w-xl">{messages.sub}</p>
          <div className="flex items-center justify-center md:justify-start gap-2 mt-3 text-mint-600 text-sm font-medium">
            <Heart className="w-4 h-4 fill-mint-300" />
            <Sparkles className="w-3 h-3" />
            {messages.cta}
          </div>
        </div>
      </div>
    </div>
  );
}
