'use client';

import { useEffect, useRef, useState } from 'react';
import SmartImage from '@/components/SmartImage';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { absoluteMediaUrl } from '@/lib/images';
import { Camera, Save, User } from 'lucide-react';

export default function ProfilePage() {
  const { t, setLocale } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [profile, setProfile] = useState({
    name: '', email: '', phone: '', preferred_language: 'ja', id: '',
    address: '', job_function: '', profile_photo_url: '',
  });
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadProfile = () => {
    api.getProfile().then((p) => setProfile({
      ...p,
      phone: p.phone || '',
      address: p.address || '',
      job_function: p.job_function || '',
      profile_photo_url: p.profile_photo_url || '',
    })).catch(() => {});
  };

  useEffect(() => { loadProfile(); }, []);

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage('');
    setError('');
    try {
      const res = await api.uploadProfilePhoto(file);
      setProfile((prev) => ({ ...prev, profile_photo_url: res.url }));
      setMessage(t.auth.photoUpdated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t.common.error);
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');
    try {
      const updated = await api.updateProfile({
        name: profile.name,
        email: profile.email,
        phone: profile.phone || undefined,
        address: profile.address,
        job_function: profile.job_function,
        preferred_language: profile.preferred_language,
      });
      setProfile({
        ...updated,
        phone: updated.phone || '',
        address: updated.address || '',
        job_function: updated.job_function || '',
        profile_photo_url: updated.profile_photo_url || profile.profile_photo_url,
      });
      setLocale(updated.preferred_language === 'en' ? 'en' : 'ja');
      setMessage(t.auth.profileUpdated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t.common.error);
    } finally {
      setSaving(false);
    }
  };

  const photoSrc = absoluteMediaUrl(profile.profile_photo_url);

  return (
    <main className="p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-6 flex items-center gap-2">
          <User className="w-6 h-6" /> {t.dashboard.profile}
        </h1>

        <form onSubmit={handleSave} className="card max-w-lg">
          <div className="flex flex-col items-center mb-6 pb-6 border-b border-gray-100">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="relative w-28 h-28 rounded-full overflow-hidden ring-4 ring-primary-100 shadow-soft group"
            >
              {photoSrc ? (
                <SmartImage src={photoSrc} alt={profile.name} fill className="object-cover" />
              ) : (
                <div className="w-full h-full bg-sky-50 flex items-center justify-center">
                  <Camera className="w-10 h-10 text-primary-300" />
                </div>
              )}
              <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                <Camera className="w-6 h-6 text-white" />
              </div>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handlePhotoUpload}
            />
            <p className="text-sm text-gray-500 mt-2">{t.auth.changePhoto}</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.auth.name}</label>
              <input
                value={profile.name}
                onChange={(e) => setProfile((prev) => ({ ...prev, name: e.target.value }))}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.auth.email}</label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile((prev) => ({ ...prev, email: e.target.value }))}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.auth.phone}</label>
              <input
                type="tel"
                value={profile.phone}
                onChange={(e) => setProfile((prev) => ({ ...prev, phone: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.auth.home_address}</label>
              <input
                value={profile.address}
                onChange={(e) => setProfile((prev) => ({ ...prev, address: e.target.value }))}
                placeholder={t.auth.homeAddressPlaceholder}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none"
              />
              <p className="text-xs text-gray-400 mt-1">{t.auth.homeAddressHint}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.auth.job_function}</label>
              <input
                value={profile.job_function}
                onChange={(e) => setProfile((prev) => ({ ...prev, job_function: e.target.value }))}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mb-1 block">{t.common.language}</label>
              <select
                value={profile.preferred_language}
                onChange={(e) => setProfile((prev) => ({ ...prev, preferred_language: e.target.value }))}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-300 focus:border-primary-400 outline-none bg-white"
              >
                <option value="ja">日本語</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>

          {message && <p className="text-sm text-mint-600 mt-4">{message}</p>}
          {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

          <button
            type="submit"
            disabled={saving || uploading}
            className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-700 text-white rounded-lg hover:bg-primary-800 disabled:opacity-50 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? t.common.loading : t.common.save}
          </button>
        </form>
    </main>
  );
}
