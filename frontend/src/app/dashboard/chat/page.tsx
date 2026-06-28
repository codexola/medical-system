'use client';

import { useEffect, useState, useRef } from 'react';
import SmartImage from '@/components/SmartImage';
import HospitalCardList, { ChatHospital, ChatSpecialist } from '@/components/HospitalCardList';
import { useLanguage } from '@/context/LanguageContext';
import { api } from '@/lib/api';
import { absoluteMediaUrl, Images } from '@/lib/images';
import { Send, Trash2, User } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  hospitals?: ChatHospital[];
  pharmacies?: ChatHospital[];
  specialists?: ChatSpecialist[];
  showHospitalFinder?: boolean;
  showPharmacyFinder?: boolean;
  symptomsContext?: string;
}

export default function ChatPage() {
  const { t, locale } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [profilePhoto, setProfilePhoto] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<number, string>>({});
  const [clearing, setClearing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getProfile().then((p) => setProfilePhoto(absoluteMediaUrl(p.profile_photo_url))).catch(() => {});
  }, []);

  const welcome = locale === 'ja'
    ? 'こんにちは。今日の体調はいかがですか？気になることがあれば、遠慮なく教えてくださいね。'
    : "Hello. How are you feeling today? Please share anything that's on your mind.";

  const quickPrompts = locale === 'ja'
    ? ['38度の発熱が2日続いています', '頭痛がひどいです', '咳とのどの痛みがあります']
    : ['I have had a 38°C fever for 2 days', 'I have a severe headache', 'I have cough and sore throat'];

  useEffect(() => {
    api.getChatHistory().then((items) => {
      if (!items.length) return;
      const restored: Message[] = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.role !== 'user' && item.role !== 'assistant') continue;
        const prevUser = item.role === 'assistant'
          ? [...items].slice(0, i).reverse().find((m) => m.role === 'user')?.content
          : undefined;
        restored.push({
          role: item.role as 'user' | 'assistant',
          content: item.content,
          symptomsContext: prevUser,
          showHospitalFinder: false,
        });
      }
      setMessages(restored);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleClearHistory = async () => {
    if (clearing || !messages.length) return;
    if (!window.confirm(t.dashboard.clearChatHistoryConfirm)) return;
    setClearing(true);
    try {
      await api.clearChatHistory();
      setMessages([]);
      setActiveFilters({});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.common.error;
      window.alert(msg);
    } finally {
      setClearing(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    try {
      const res = await api.chat(userMsg);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          hospitals: res.hospitals,
          pharmacies: res.pharmacies,
          specialists: res.specialists,
          showHospitalFinder: res.show_hospital_finder,
          showPharmacyFinder: res.show_pharmacy_finder,
          symptomsContext: userMsg,
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.common.error;
      setMessages((prev) => [...prev, { role: 'assistant', content: msg }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async (msgIndex: number, sortBy: 'nearest' | 'specialty' | 'rating', excellenceOnly = false) => {
    const msg = messages[msgIndex];
    if (!msg?.symptomsContext) return;
    setFilterLoading(true);
    setActiveFilters((prev) => ({ ...prev, [msgIndex]: excellenceOnly ? 'excellence' : sortBy }));
    try {
      const hospitals = await api.filterHospitals({
        symptoms: msg.symptomsContext,
        sort_by: sortBy,
        excellence_only: excellenceOnly,
      });
      setMessages((prev) =>
        prev.map((m, i) => (i === msgIndex ? { ...m, hospitals } : m))
      );
    } catch {
      /* keep existing list */
    } finally {
      setFilterLoading(false);
    }
  };

  return (
    <main className="flex h-[100dvh] flex-col">
        <div className="relative h-36 overflow-hidden border-b border-primary-100 shrink-0">
          <SmartImage src={Images.symptomCheck.primary} fallback={Images.symptomCheck.fallback} alt="" fill className="object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-white/95 via-sky-50/90 to-transparent" />
          <div className="relative h-full flex items-center px-6 gap-4">
            <div className="relative w-16 h-16 rounded-full overflow-hidden ring-4 ring-primary-200 shadow-soft flex-shrink-0">
              <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" fill className="object-cover" />
            </div>
            <div>
              <h1 className="font-serif text-xl font-bold text-primary-800">{t.dashboard.chat}</h1>
              <p className="text-sm text-slate-500 mt-0.5">
                {locale === 'ja' ? 'やさしい医療相談アシスタント' : 'Kind medical consultation assistant'}
              </p>
            </div>
            {messages.length > 0 && (
              <button
                type="button"
                onClick={handleClearHistory}
                disabled={clearing}
                className="ml-auto flex items-center gap-2 text-sm text-slate-500 hover:text-red-600 border border-slate-200 hover:border-red-200 px-3 py-2 rounded-lg bg-white/80 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                {t.dashboard.clearChatHistory}
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden min-h-0">
          <div className="hidden xl:block w-64 p-5 border-r bg-white/50 shrink-0">
            <div className="relative rounded-2xl overflow-hidden aspect-square mb-4 shadow-soft ring-2 ring-white">
              <SmartImage src={Images.doctor.primary} fallback={Images.doctor.fallback} alt="" fill className="object-cover" />
            </div>
            <p className="text-xs text-slate-500 leading-relaxed text-center">
              適切な治療を受ければ、回復への道は必ず開けます。一人で悩まないでください。
            </p>
          </div>

          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-10 max-w-md mx-auto">
                  <div className="relative w-24 h-24 mx-auto mb-4 rounded-full overflow-hidden ring-4 ring-mint-200 shadow-soft">
                    <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" fill className="object-cover" />
                  </div>
                  <p className="text-primary-700 leading-relaxed mb-5">{welcome}</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickPrompts.map((q) => (
                      <button key={q} onClick={() => setInput(q)} className="text-xs bg-white border-2 border-primary-100 px-4 py-2 rounded-full hover:border-primary-300 hover:bg-sky-50 text-primary-600 transition-colors">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-9 h-9 rounded-full overflow-hidden flex-shrink-0 ring-2 ring-mint-200">
                      <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" width={36} height={36} className="object-cover w-full h-full" />
                    </div>
                  )}
                  <div className={msg.role === 'user' ? '' : 'max-w-lg'}>
                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-primary-400 to-primary-500 text-white rounded-br-md shadow-soft max-w-lg'
                        : 'bg-white border-2 border-mint-100 text-slate-700 rounded-bl-md shadow-sm'
                    }`}>
                      {msg.content}
                    </div>
                    {msg.role === 'assistant' && (msg.showHospitalFinder || msg.showPharmacyFinder || (msg.specialists?.length ?? 0) > 0) && (
                      <HospitalCardList
                        hospitals={msg.hospitals || []}
                        pharmacies={msg.pharmacies || []}
                        specialists={msg.specialists || []}
                        symptoms={msg.symptomsContext}
                        showFilters={msg.showHospitalFinder}
                        loading={filterLoading}
                        activeFilter={activeFilters[i] || 'nearest'}
                        onFilter={(sortBy, excellence) => handleFilter(i, sortBy, excellence)}
                      />
                    )}
                  </div>
                  {msg.role === 'user' && (
                    profilePhoto ? (
                      <div className="w-9 h-9 rounded-full overflow-hidden flex-shrink-0 ring-2 ring-peach-200">
                        <SmartImage src={profilePhoto} alt="" width={36} height={36} className="object-cover w-full h-full" />
                      </div>
                    ) : (
                      <div className="w-9 h-9 bg-peach-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-peach-500" />
                      </div>
                    )
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3">
                  <div className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-mint-200">
                    <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="" width={36} height={36} />
                  </div>
                  <div className="bg-white border-2 border-mint-100 px-4 py-3 rounded-2xl rounded-bl-md">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((j) => (
                        <span key={j} className="w-2 h-2 bg-primary-300 rounded-full animate-bounce" style={{ animationDelay: `${j * 0.1}s` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="p-4 bg-white/90 backdrop-blur border-t border-primary-100 shrink-0">
              <div className="flex gap-3 max-w-3xl mx-auto">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder={locale === 'ja' ? 'いまの体調や気になることを教えてください...' : "Tell me how you're feeling..."}
                  className="input-field flex-1"
                />
                <button onClick={sendMessage} disabled={loading} className="btn-primary px-5">
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-slate-400 text-center mt-2">
                医療診断ではありません。お体のことが心配なときは、医療機関への受診をお勧めします。
              </p>
            </div>
          </div>
        </div>
    </main>
  );
}
