'use client';

import SmartImage from './SmartImage';

interface PageHeroProps {
  title: string;
  subtitle?: string;
  image: string;
  imageFallback?: string;
  children?: React.ReactNode;
  compact?: boolean;
  bright?: boolean;
}

export default function PageHero({
  title,
  subtitle,
  image,
  imageFallback,
  children,
  compact,
  bright = true,
}: PageHeroProps) {
  const overlay = bright
    ? 'bg-gradient-to-r from-white/92 via-sky-50/88 to-primary-100/40'
    : 'bg-gradient-to-r from-primary-900/90 via-primary-800/80 to-primary-700/60';

  const titleClass = bright ? 'text-primary-800' : 'text-white';
  const subtitleClass = bright ? 'text-slate-600' : 'text-primary-100';

  return (
    <section className={`relative overflow-hidden ${compact ? 'h-52 md:h-60' : 'h-64 md:h-80'}`}>
      <SmartImage src={image} fallback={imageFallback} alt="" fill className="object-cover" priority />
      <div className={`absolute inset-0 ${overlay}`} />
      <div className="relative h-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col justify-center">
        <h1 className={`font-serif text-3xl md:text-4xl font-bold mb-2 ${titleClass}`}>{title}</h1>
        {subtitle && <p className={`text-lg max-w-2xl leading-relaxed ${subtitleClass}`}>{subtitle}</p>}
        {children}
      </div>
    </section>
  );
}
