'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Calendar, Users, Brain, BarChart3,
  HelpCircle, Clock, LogOut, Heart, CreditCard,
} from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

const icons = [LayoutDashboard, Calendar, Users, CreditCard, Brain, BarChart3, HelpCircle, Clock];

export default function AdminSidebar() {
  const { t } = useLanguage();
  const pathname = usePathname();

  const links = [
    { href: '/admin', label: t.admin.title, icon: 0 },
    { href: '/admin/reservations', label: t.admin.todayReservations, icon: 1 },
    { href: '/admin/patients', label: t.admin.patients, icon: 2 },
    { href: '/admin/subscriptions', label: 'Subscriptions', icon: 3 },
    { href: '/admin/ai-logs', label: t.admin.aiLogs, icon: 4 },
    { href: '/admin/analytics', label: t.admin.analytics, icon: 5 },
    { href: '/admin/faqs', label: t.admin.faqs, icon: 6 },
    { href: '/admin/schedules', label: t.admin.schedules, icon: 7 },
  ];

  return (
    <aside className="w-64 bg-primary-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-primary-700">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-sakura-400 rounded-lg flex items-center justify-center">
            <Heart className="w-4 h-4 text-white" />
          </div>
          <span className="font-serif font-bold">Admin</span>
        </Link>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => {
          const Icon = icons[link.icon];
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active ? 'bg-primary-700 text-white' : 'text-primary-200 hover:bg-primary-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-primary-700">
        <button
          onClick={() => { api.clearToken(); window.location.href = '/login'; }}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-primary-300 hover:bg-primary-800 w-full"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
