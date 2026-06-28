'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { messages, Locale } from '@/lib/i18n';

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: typeof messages.ja;
}

const LanguageContext = createContext<LanguageContextType>({
  locale: 'ja',
  setLocale: () => {},
  t: messages.ja,
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('ja');

  useEffect(() => {
    const saved = localStorage.getItem('locale') as Locale;
    if (saved && messages[saved]) setLocaleState(saved);
  }, []);

  const setLocale = (l: Locale) => {
    setLocaleState(l);
    localStorage.setItem('locale', l);
  };

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t: messages[locale] }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);
