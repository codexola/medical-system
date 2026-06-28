'use client';

import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import PageHero from '@/components/PageHero';
import SectionShell from '@/components/SectionShell';
import { Images } from '@/lib/images';
import { Mail, MapPin, Phone } from 'lucide-react';

export default function ContactPage() {
  return (
    <div className="min-h-screen pattern-bright">
      <Navbar />
      <PageHero title="お問い合わせ" subtitle="どんな小さなことでも、やさしくお答えします" image={Images.consultation.primary} imageFallback={Images.consultation.fallback} compact />

      <SectionShell variant="sky">
        <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
          <div className="card-bright space-y-5">
            {[
              { icon: Mail, label: 'Email', value: 'contact@kenko-ai.jp' },
              { icon: Phone, label: 'Phone', value: '03-1234-5678' },
              { icon: MapPin, label: 'Address', value: '東京都千代田区丸の内1-1-1' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-4">
                <div className="w-12 h-12 bg-sky-100 rounded-2xl flex items-center justify-center">
                  <item.icon className="w-5 h-5 text-primary-500" />
                </div>
                <div>
                  <p className="text-sm text-slate-400">{item.label}</p>
                  <p className="font-medium text-primary-800">{item.value}</p>
                </div>
              </div>
            ))}
          </div>
          <form className="card-bright space-y-4" onSubmit={(e) => e.preventDefault()}>
            <input placeholder="お名前" className="input-field" />
            <input type="email" placeholder="メールアドレス" className="input-field" />
            <textarea placeholder="ご質問・ご不安なことなど、お気軽にどうぞ" rows={5} className="input-field resize-none" />
            <button type="submit" className="btn-primary w-full">やさしく送信</button>
          </form>
        </div>
      </SectionShell>
      <Footer />
    </div>
  );
}
