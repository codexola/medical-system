'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  LayoutDashboard, Calendar, MessageCircle, MapPin, Activity,
  CreditCard, User, Settings, LogOut,
} from 'lucide-react';
import SmartImage from './SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { absoluteMediaUrl, Images } from '@/lib/images';

const icons = [LayoutDashboard, Calendar, MessageCircle, MapPin, Activity, CreditCard, User, Settings];

export default function DashboardSidebar() {
  const { t } = useLanguage();
  const pathname = usePathname();
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [userName, setUserName] = useState('');

  useEffect(() => {
    api.getProfile().then((p) => {
      setProfilePhoto(absoluteMediaUrl(p.profile_photo_url));
      setUserName(p.name || '');
    }).catch(() => {});
  }, [pathname]);

  const links = [
    { href: '/dashboard', label: t.dashboard.title, icon: 0 },
    { href: '/dashboard/reservations', label: t.dashboard.reservations, icon: 1 },
    { href: '/dashboard/chat', label: t.dashboard.chat, icon: 2 },
    { href: '/dashboard/hospitals', label: t.dashboard.hospitals, icon: 3 },
    { href: '/dashboard/health', label: t.dashboard.healthTimeline, icon: 4 },
    { href: '/dashboard/subscription', label: t.dashboard.subscription, icon: 5 },
    { href: '/dashboard/profile', label: t.dashboard.profile, icon: 6 },
    { href: '/dashboard/settings', label: t.dashboard.settings, icon: 7 },
  ];

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-primary-100 bg-white/95 shadow-soft backdrop-blur-xl overflow-y-auto">
      <div className="p-5 border-b border-primary-50">
        <Link href="/" className="flex items-center gap-3">
          <div className="relative w-11 h-11 rounded-2xl overflow-hidden ring-2 ring-primary-200 shadow-soft">
            <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" fill className="object-cover" />
          </div>
          <span className="font-serif font-bold text-primary-700">健康<span className="text-peach-400">AI</span></span>
        </Link>
      </div>

      <div className="px-4 py-3">
        <p className="text-xs text-mint-600 bg-mint-50 rounded-xl px-3 py-2 leading-relaxed">
          不安なときは、いつでもご相談を
        </p>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        {links.map((link) => {
          const Icon = icons[link.icon];
          const active = pathname === link.href;
          return (
            <Link key={link.href} href={link.href} className={`sidebar-link ${active ? 'sidebar-link-active' : 'sidebar-link-inactive'}`}>
              <Icon className="w-4 h-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-primary-50">
        {userName && (
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-primary-100 flex-shrink-0">
              {profilePhoto ? (
                <SmartImage src={profilePhoto} alt={userName} width={36} height={36} className="object-cover w-full h-full" />
              ) : (
                <div className="w-full h-full bg-primary-50 flex items-center justify-center">
                  <User className="w-4 h-4 text-primary-400" />
                </div>
              )}
            </div>
            <span className="text-sm font-medium text-primary-800 truncate">{userName}</span>
          </div>
        )}
        <button
          onClick={() => { api.clearToken(); window.location.href = '/login'; }}
          className="sidebar-link sidebar-link-inactive w-full text-slate-400 hover:text-red-500 hover:bg-red-50"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
