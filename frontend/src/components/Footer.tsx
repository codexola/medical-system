'use client';

import Link from 'next/link';
import SmartImage from './SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { Images } from '@/lib/images';
import { Heart } from 'lucide-react';

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="bg-gradient-to-b from-sky-50 to-primary-50 border-t border-primary-100">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="card-hope mb-12 flex flex-col md:flex-row gap-6 items-center text-center md:text-left">
          <div className="relative w-20 h-20 rounded-full overflow-hidden ring-4 ring-mint-200 flex-shrink-0">
            <SmartImage src={Images.doctor.primary} fallback={Images.doctor.fallback} alt="" fill className="object-cover" />
          </div>
          <div>
            <p className="text-primary-800 font-medium text-lg leading-relaxed">
              {t.footer.hopeMessage || 'どんなときも、あなたの回復を心から信じています。一緒に歩みましょう。'}
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Heart className="w-5 h-5 text-peach-400 fill-peach-200" />
              <span className="font-serif font-bold text-primary-800">{t.footer.company}</span>
            </div>
            <p className="text-slate-500 text-sm mb-3">{t.footer.tagline}</p>
            <p className="text-slate-400 text-xs leading-relaxed">{t.footer.disclaimer}</p>
          </div>
          <div>
            <h4 className="font-semibold text-primary-700 mb-3 text-sm">Links</h4>
            <ul className="space-y-2 text-sm text-slate-500">
              <li><Link href="/privacy" className="hover:text-primary-500">{t.footer.privacy}</Link></li>
              <li><Link href="/terms" className="hover:text-primary-500">{t.footer.terms}</Link></li>
              <li><Link href="/contact" className="hover:text-primary-500">{t.footer.contact}</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-primary-700 mb-3 text-sm">Services</h4>
            <ul className="space-y-2 text-sm text-slate-500">
              <li><Link href="/dashboard" className="hover:text-primary-500">{t.nav.dashboard}</Link></li>
              <li><Link href="/hospitals" className="hover:text-primary-500">{t.nav.hospitals}</Link></li>
              <li><Link href="/pricing" className="hover:text-primary-500">{t.nav.pricing}</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-primary-100 mt-10 pt-8 text-center text-slate-400 text-xs">
          &copy; {new Date().getFullYear()} Kenko AI Healthcare Platform
        </div>
      </div>
    </footer>
  );
}
