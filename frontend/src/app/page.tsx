'use client';

import Link from 'next/link';
import SmartImage from '@/components/SmartImage';
import { ArrowRight, Heart, Sun, Shield } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import FeatureCard from '@/components/FeatureCard';
import HowItWorks from '@/components/HowItWorks';
import SectionShell, { SectionHeader, HopeCard } from '@/components/SectionShell';
import { useLanguage } from '@/context/LanguageContext';
import { Images, SliderImages, featureSliderSets } from '@/lib/images';
import ImageSlider from '@/components/ImageSlider';

const hopeNotesJa = [
  '不安な夜も、一人じゃありません。いつでもご相談ください。',
  '正しい情報が、安心への第一歩になります。',
  '早めの受診は、回復への大切な一歩です。',
  'あなたに合った医療機関を、一緒に見つけましょう。',
  '毎日の記録が、未来の健康を守ります。',
  '継続的なケアが、笑顔を取り戻す力になります。',
];

const hopeNotesEn = [
  'Even on anxious nights, you are not alone. We are here.',
  'Clear information is the first step toward peace of mind.',
  'Seeking care early is a brave step toward recovery.',
  'Let us help you find the right hospital for you.',
  'Daily records protect your future health.',
  'Ongoing care helps bring back your smile.',
];

export default function HomePage() {
  const { t, locale } = useLanguage();
  const features = [
    t.features.ai, t.features.rag, t.features.reservation,
    t.features.hospital, t.features.health, t.features.subscription,
  ];
  const hopeNotes = locale === 'ja' ? hopeNotesJa : hopeNotesEn;

  return (
    <div className="min-h-screen pattern-bright">
      <Navbar />

      {/* Hero — bright, hopeful */}
      <section className="relative pt-16 overflow-hidden">
        <div className="absolute inset-0 pattern-dots opacity-60" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="grid lg:grid-cols-2 gap-10 items-center">
            <div className="animate-fade-up order-2 lg:order-1">
              <span className="section-label">
                <Sun className="w-3 h-3" />
                {t.hero.badge}
              </span>
              <h1 className="font-serif text-4xl md:text-5xl font-bold text-primary-800 leading-tight mb-5">
                {t.hero.title}
              </h1>
              <p className="text-lg text-slate-600 mb-8 leading-relaxed">{t.hero.subtitle}</p>
              <div className="flex flex-wrap gap-4 mb-8">
                <Link href="/register" className="btn-primary inline-flex items-center gap-2">
                  {t.hero.cta} <ArrowRight className="w-4 h-4" />
                </Link>
                <Link href="/#features" className="btn-secondary">{t.hero.ctaSecondary}</Link>
              </div>
              <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                <span className="flex items-center gap-1.5 bg-white/80 px-3 py-1.5 rounded-full shadow-sm">
                  <Heart className="w-4 h-4 text-peach-400" /> やさしいAI相談
                </span>
                <span className="flex items-center gap-1.5 bg-white/80 px-3 py-1.5 rounded-full shadow-sm">
                  <Shield className="w-4 h-4 text-mint-500" /> 安心のガイド
                </span>
              </div>
            </div>

            <div className="relative order-1 lg:order-2 animate-fade-up">
              <ImageSlider slides={SliderImages.hero} priority />
              <div className="absolute -bottom-4 -left-4 w-28 h-28 rounded-2xl overflow-hidden ring-4 ring-mint-200 shadow-soft hidden md:block animate-gentle-float z-10">
                <SmartImage src={Images.mascot.primary} fallback={Images.mascot.fallback} alt="Assistant" fill className="object-cover" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Hope message */}
      <SectionShell variant="mint" className="!py-12">
        <HopeCard
          message={locale === 'ja' ? '治療を受けることは、自分を大切にする勇気ある選択です。' : 'Choosing treatment is a courageous act of caring for yourself.'}
          submessage={locale === 'ja' ? '私たちは、あなたが必ず良くなれると信じています。焦らず、一緒に進みましょう。' : 'We believe you can recover. There is no rush—we will move forward together.'}
          slides={SliderImages.hope}
        />
      </SectionShell>

      {/* Features */}
      <SectionShell variant="white" id="features">
        <SectionHeader label="Features" title={t.features.title} subtitle={t.features.subtitle} />
        <div className="divide-y divide-primary-50">
          {features.map((feature, i) => (
            <FeatureCard
              key={i}
              index={i}
              title={feature.title}
              description={feature.desc}
              slides={featureSliderSets[i]}
              hopeNote={hopeNotes[i]}
            />
          ))}
        </div>
      </SectionShell>

      {/* Team trust */}
      <SectionShell variant="sky">
        <div className="grid lg:grid-cols-2 gap-10 items-center">
          <ImageSlider
            slides={SliderImages.team}
            aspectClass="aspect-[16/10]"
            innerClassName="rounded-3xl overflow-hidden shadow-soft ring-2 ring-white"
          />
          <div>
            <SectionHeader
              align="left"
              label="Care Team"
              title={locale === 'ja' ? '笑顔で迎える医療チーム' : 'A medical team that welcomes you with a smile'}
              subtitle={locale === 'ja' ? '明るい色のユニフォームを着た医師・スタッフが、温かくあなたをお迎えします。' : 'Doctors and staff in bright, fine uniforms welcome you with warmth.'}
            />
          </div>
        </div>
      </SectionShell>

      <HowItWorks
        title={locale === 'ja' ? 'ご利用の流れ' : 'How it works'}
        subtitle={locale === 'ja' ? '難しく考えなくて大丈夫。やさしく3ステップで始められます' : 'No need to overthink it—start gently in three steps'}
        slides={SliderImages.guide}
        steps={[
          { title: locale === 'ja' ? '無料登録' : 'Free registration', description: locale === 'ja' ? 'LINEまたはWebから、気軽に登録できます。' : 'Register easily via LINE or the web.' },
          { title: locale === 'ja' ? 'やさしいAI相談' : 'Kind AI consultation', description: locale === 'ja' ? '気になることを、そのままお話しください。' : 'Share your concerns just as they are.' },
          { title: locale === 'ja' ? '予約・フォロー' : 'Booking & follow-up', description: locale === 'ja' ? '受診後も、あなたの回復を見守ります。' : 'We support your recovery even after your visit.' },
        ]}
      />

      {/* Recovery hope */}
      <SectionShell variant="peach">
        <div className="grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <h2 className="section-title">
              {locale === 'ja' ? '必ず、笑顔の日が来ます' : 'Your day to smile will come'}
            </h2>
            <p className="text-slate-600 text-lg leading-relaxed mb-6">
              {locale === 'ja'
                ? '今つらくても、適切な治療と支えがあれば、前に進むことができます。私たちはその道のりを、明るくやさしくお手伝いします。'
                : 'Even when it is hard now, with proper treatment and support you can move forward. We will help brighten that path.'}
            </p>
            <Link href="/register" className="btn-peach inline-flex items-center gap-2">
              {t.hero.cta} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <ImageSlider slides={SliderImages.recovery} aspectClass="aspect-[4/3]" />
        </div>
      </SectionShell>

      <Footer />
    </div>
  );
}
