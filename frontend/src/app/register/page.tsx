'use client';

import { useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Camera } from 'lucide-react';
import { api } from '@/lib/api';
import { useLanguage } from '@/context/LanguageContext';
import AuthLayout from '@/components/AuthLayout';

export default function RegisterPage() {
  const { t } = useLanguage();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    home_address: '',
    job_function: '',
  });
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError(t.auth.photoInvalid);
      return;
    }
    setPhoto(file);
    setPhotoPreview(URL.createObjectURL(file));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!photo) {
      setError(t.auth.photoRequired);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('email', form.email);
      formData.append('password', form.password);
      formData.append('name', form.name);
      formData.append('home_address', form.home_address);
      formData.append('job_function', form.job_function);
      if (form.phone) formData.append('phone', form.phone);
      formData.append('profile_photo', photo);

      const res = await api.register(formData);
      api.setToken(res.access_token);
      api.setRole(res.role);
      router.push('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { key: 'name' as const, type: 'text', required: true },
    { key: 'email' as const, type: 'email', required: true },
    { key: 'home_address' as const, type: 'text', required: true },
    { key: 'job_function' as const, type: 'text', required: true },
    { key: 'phone' as const, type: 'text', required: false },
    { key: 'password' as const, type: 'password', required: true },
  ];

  return (
    <AuthLayout title={t.auth.register} subtitle={t.auth.registerSubtitle}>
      {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-xl mb-4 border border-red-100">{error}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex flex-col items-center mb-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="relative w-24 h-24 rounded-full overflow-hidden bg-sky-50 border-2 border-dashed border-primary-200 hover:border-primary-400 transition-colors flex items-center justify-center group"
          >
            {photoPreview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={photoPreview} alt="" className="w-full h-full object-cover" />
            ) : (
              <Camera className="w-8 h-8 text-primary-300 group-hover:text-primary-500" />
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handlePhotoChange}
          />
          <p className="text-sm font-medium text-gray-700 mt-2">{t.auth.profilePhoto}</p>
          <p className="text-xs text-gray-400">{t.auth.profilePhotoHint}</p>
        </div>

        {fields.map(({ key, type, required }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t.auth[key]}</label>
            {key === 'home_address' && (
              <p className="text-xs text-gray-400 mb-1">{t.auth.homeAddressHint}</p>
            )}
            <input
              type={type}
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              className="input-field"
              required={required}
              placeholder={key === 'home_address' ? t.auth.homeAddressPlaceholder : undefined}
            />
          </div>
        ))}
        <button type="submit" disabled={loading} className="w-full btn-primary disabled:opacity-50">
          {loading ? t.common.loading : t.auth.register}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-6">
        {t.auth.hasAccount}{' '}
        <Link href="/login" className="text-primary-700 font-medium hover:underline">{t.auth.login}</Link>
      </p>
    </AuthLayout>
  );
}
