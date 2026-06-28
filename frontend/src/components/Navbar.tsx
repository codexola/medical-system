'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { Menu, X, Globe } from 'lucide-react';
import SmartImage from './SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { Images } from '@/lib/images';

export default function Navbar() {
  const { t, locale, setLocale } = useLanguage();
  const [open, setOpen] = useState(false);

  const links = [
    { href: '/#features', label: t.nav.features },
    { href: '/hospitals', label: t.nav.hospitals },
    { href: '/pricing', label: t.nav.pricing },
  ];

  return (
    <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-lg shadow-sm border-b border-primary-100/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="relative w-10 h-10 rounded-2xl overflow-hidden ring-2 ring-primary-200 shadow-soft">
              <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="Kenko AI" fill className="object-cover" />
            </div>
            <span className="font-serif text-xl font-bold text-primary-700">
              健康<span className="text-peach-400">AI</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {links.map((link) => (
              <Link key={link.href} href={link.href} className="text-sm font-medium text-slate-600 hover:text-primary-500 transition-colors">
                {link.label}
              </Link>
            ))}
            <button onClick={() => setLocale(locale === 'ja' ? 'en' : 'ja')} className="flex items-center gap-1 text-sm text-slate-500 hover:text-primary-500">
              <Globe className="w-4 h-4" />
              {locale === 'ja' ? 'EN' : 'JP'}
            </button>
            <Link href="/login" className="text-sm font-medium text-primary-600">{t.nav.login}</Link>
            <Link href="/register" className="btn-primary text-sm py-2 px-5">{t.nav.register}</Link>
          </div>

          <button className="md:hidden text-slate-700" onClick={() => setOpen(!open)}>
            {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden bg-white border-t px-4 py-4 space-y-3 shadow-lg">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="block text-slate-600 py-2" onClick={() => setOpen(false)}>{link.label}</Link>
          ))}
          <Link href="/login" className="block py-2 text-primary-600">{t.nav.login}</Link>
          <Link href="/register" className="block btn-primary text-center">{t.nav.register}</Link>
        </div>
      )}
    </nav>
  );
}
