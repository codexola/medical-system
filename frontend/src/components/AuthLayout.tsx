'use client';

import Link from 'next/link';
import SmartImage from './SmartImage';
import { Images } from '@/lib/images';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2 pattern-bright">
      <div className="hidden lg:flex flex-col relative overflow-hidden">
        <SmartImage src={Images.loginBg.primary} fallback={Images.loginBg.fallback} alt="" fill className="object-cover" />
        <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-sky-50/20 to-peach-50/30" />

        <div className="relative flex-1 flex flex-col justify-between p-10">
          <Link
            href="/"
            className="flex items-center gap-3 w-fit rounded-2xl transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400"
            aria-label="ホームページへ戻る"
          >
            <div className="relative w-14 h-14 rounded-2xl overflow-hidden ring-4 ring-white shadow-soft">
              <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" fill className="object-cover" />
            </div>
            <span className="font-serif text-2xl font-bold text-primary-800">健康<span className="text-peach-400">AI</span></span>
          </Link>

          <div>
            <div className="relative w-full h-56 rounded-3xl overflow-hidden shadow-soft mb-6 ring-2 ring-white">
              <SmartImage src={Images.consultation.primary} fallback={Images.consultation.fallback} alt="" fill className="object-cover" />
            </div>
            <p className="text-primary-800 text-xl font-serif font-bold leading-relaxed mb-2">
              あなたは、必ず良くなれます。
            </p>
            <p className="text-slate-600 leading-relaxed">
              やさしい医療チームとAIが、治療への一歩を温かくサポートします。
            </p>
          </div>

          <div className="flex gap-3">
            <div className="relative w-16 h-16 rounded-full overflow-hidden ring-2 ring-mint-200">
              <SmartImage src={Images.doctor.primary} fallback={Images.doctor.fallback} alt="" fill className="object-cover" />
            </div>
            <div className="relative w-16 h-16 rounded-full overflow-hidden ring-2 ring-peach-200 -ml-4">
              <SmartImage src={Images.patientHope.primary} fallback={Images.patientHope.fallback} alt="" fill className="object-cover" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col justify-center px-6 py-12 lg:px-16">
        <div className="w-full max-w-md mx-auto animate-fade-up">
          <Link
            href="/"
            className="lg:hidden flex items-center justify-center gap-2.5 mb-6 w-fit mx-auto rounded-2xl transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400"
            aria-label="ホームページへ戻る"
          >
            <div className="relative w-10 h-10 rounded-2xl overflow-hidden ring-2 ring-primary-200 shadow-soft">
              <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" fill className="object-cover" />
            </div>
            <span className="font-serif text-xl font-bold text-primary-700">
              健康<span className="text-peach-400">AI</span>
            </span>
          </Link>
          <div className="card-bright">
            <h1 className="text-2xl font-bold text-primary-800 mb-1">{title}</h1>
            {subtitle && <p className="text-slate-500 text-sm mb-6">{subtitle}</p>}
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
