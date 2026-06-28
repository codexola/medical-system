'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Settings, BarChart3, FileText, Server, Users, LogOut, Code2, UserRound,
} from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';

const icons = [LayoutDashboard, Settings, BarChart3, FileText, Server, UserRound, Users];

export default function DeveloperSidebar() {
  const { t } = useLanguage();
  const pathname = usePathname();

  const links = [
    { href: '/developer', label: t.developer.title, icon: 0 },
    { href: '/developer/settings', label: t.developer.settings, icon: 1 },
    { href: '/developer/usage', label: t.developer.usage, icon: 2 },
    { href: '/developer/audit', label: t.developer.audit, icon: 3 },
    { href: '/developer/system', label: t.developer.system, icon: 4 },
    { href: '/developer/users', label: t.developer.users, icon: 5 },
    { href: '/developer/staff', label: t.developer.staff, icon: 6 },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen flex flex-col">
      <div className="p-6 border-b border-slate-700">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-violet-500 rounded-lg flex items-center justify-center">
            <Code2 className="w-4 h-4 text-white" />
          </div>
          <span className="font-serif font-bold">Developer</span>
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
                active ? 'bg-violet-600 text-white' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-700">
        <button
          onClick={() => { api.clearToken(); window.location.href = '/login'; }}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 w-full"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
