'use client';

import { useEffect, useState } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { Check, Crown } from 'lucide-react';

export default function SubscriptionPage() {
  const { t } = useLanguage();
  const [status, setStatus] = useState<{
    active: boolean;
    plan?: string;
    status?: string;
    trial_end?: string;
    current_period_end?: string;
    subscription_id?: string;
    is_test_account?: boolean;
    can_select_without_payment?: boolean;
    features?: string[];
  }>({ active: false });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const reload = () => {
    api.getSubscriptionStatus().then(setStatus).catch(() => {});
  };

  useEffect(() => { reload(); }, []);

  const handleSelectPlan = async (plan: 'standard' | 'premium') => {
    setLoading(true);
    setMessage('');
    try {
      if (status.can_select_without_payment) {
        const res = await api.changeSubscriptionPlan(plan);
        setMessage(
          status.is_test_account
            ? `テストアカウントのため、${plan}プランをお支払いなしで有効にしました。`
            : 'プランを変更しました。'
        );
        reload();
        return;
      }
      const res = await api.createCheckout(plan);
      if (res.checkout_url) window.location.href = res.checkout_url;
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('サブスクリプションをキャンセルしますか？')) return;
    setLoading(true);
    setMessage('');
    try {
      await api.cancelSubscription();
      setMessage('キャンセルしました');
      reload();
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : t.common.error);
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: t.pricing.trial,
      price: '¥0',
      features: [t.pricing.features.aiChat, t.pricing.features.hospitalSearch],
      current: status.plan === 'free_trial',
    },
    {
      name: t.pricing.standard,
      price: '¥980',
      features: [t.pricing.features.aiChat, t.pricing.features.hospitalSearch, t.pricing.features.reminders],
      plan: 'standard' as const,
    },
    {
      name: t.pricing.premium,
      price: '¥1,980',
      features: [
        t.pricing.features.aiChat, t.pricing.features.hospitalSearch,
        t.pricing.features.reminders, t.pricing.features.family,
        t.pricing.features.analytics, t.pricing.features.priority,
      ],
      plan: 'premium' as const,
      highlight: true,
    },
  ];

  const canCancel = status.active && status.status !== 'cancelled' && status.plan !== 'free_trial';

  return (
    <main className="p-8">
        <h1 className="text-2xl font-bold text-primary-800 mb-2">{t.dashboard.subscription}</h1>
        {status.plan && (
          <div className="text-sm text-matcha-600 mb-4 space-y-1">
            <p>現在のプラン: <strong>{status.plan}</strong> ({status.status})</p>
            {status.is_test_account && (
              <p className="text-primary-600">テストアカウント — プランはお支払いなしで切り替えできます。</p>
            )}
            {status.trial_end && <p>トライアル終了: {new Date(status.trial_end).toLocaleDateString('ja-JP')}</p>}
            {status.current_period_end && <p>次回更新: {new Date(status.current_period_end).toLocaleDateString('ja-JP')}</p>}
          </div>
        )}
        {message && <p className="text-sm text-primary-600 mb-4">{message}</p>}
        {canCancel && (
          <button
            onClick={handleCancel}
            disabled={loading}
            className="text-sm text-red-600 border border-red-200 px-4 py-2 rounded-lg mb-6 hover:bg-red-50"
          >
            サブスクリプションをキャンセル
          </button>
        )}

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div key={plan.name} className={`card relative ${plan.highlight ? 'border-primary-300 ring-2 ring-primary-100' : ''}`}>
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-700 text-white text-xs px-3 py-1 rounded-full flex items-center gap-1">
                  <Crown className="w-3 h-3" /> おすすめ
                </div>
              )}
              <h3 className="font-semibold text-lg text-primary-800 mb-1">{plan.name}</h3>
              <p className="text-3xl font-bold text-primary-700 mb-4">
                {plan.price}<span className="text-sm font-normal text-gray-500">{t.pricing.perMonth}</span>
              </p>
              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                    <Check className="w-4 h-4 text-matcha-500" />
                    {f}
                  </li>
                ))}
              </ul>
              {plan.current ? (
                <button className="w-full py-2 bg-gray-100 text-gray-500 rounded-lg text-sm" disabled>
                  現在のプラン
                </button>
              ) : plan.plan ? (
                <button
                  onClick={() => handleSelectPlan(plan.plan!)}
                  disabled={loading}
                  className="w-full btn-primary text-sm disabled:opacity-50"
                >
                  {status.can_select_without_payment ? 'このプランを選択（テスト）' : 'プランを選択'}
                </button>
              ) : null}
            </div>
          ))}
        </div>
    </main>
  );
}
