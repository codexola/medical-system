'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useLanguage } from '@/context/LanguageContext';
import AuthLayout from '@/components/AuthLayout';

function LoginForm() {
  const { t } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.syncAuthCookies();
    const token = api.getToken();
    const role = api.getRole();
    if (!token) return;
    if (role === 'developer') router.replace('/developer');
    else if (role === 'admin') router.replace('/admin');
    else router.replace('/dashboard');
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.login(email, password);
      api.setToken(res.access_token);
      api.setRole(res.role);
      const defaultHome =
        res.role === 'developer' ? '/developer' : res.role === 'admin' ? '/admin' : '/dashboard';
      const next = searchParams.get('next');
      if (next && next.startsWith('/') && !next.startsWith('/login')) {
        const allowed =
          (res.role === 'patient' && next.startsWith('/dashboard')) ||
          (res.role === 'admin' && next.startsWith('/admin')) ||
          (res.role === 'developer' && next.startsWith('/developer'));
        router.push(allowed ? next : defaultHome);
        return;
      }
      router.push(defaultHome);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title={t.auth.login} subtitle="おかえりなさい。今日もあなたの健康を、やさしくサポートします。">
      {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-xl mb-4 border border-red-100">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t.auth.email}</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t.auth.password}</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" required />
        </div>
        <button type="submit" disabled={loading} className="w-full btn-primary disabled:opacity-50">
          {loading ? t.common.loading : t.auth.submit}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-6">
        {t.auth.noAccount}{' '}
        <Link href="/register" className="text-primary-700 font-medium hover:underline">{t.auth.register}</Link>
      </p>
    </AuthLayout>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
