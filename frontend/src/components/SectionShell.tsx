'use client';

import ImageSlider, { SlideImage } from './ImageSlider';
import SmartImage from './SmartImage';

type SectionVariant = 'white' | 'sky' | 'peach' | 'mint' | 'pattern' | 'gradient';

interface SectionShellProps {
  children: React.ReactNode;
  variant?: SectionVariant;
  className?: string;
  id?: string;
}

const variants: Record<SectionVariant, string> = {
  white: 'bg-white',
  sky: 'bg-gradient-to-b from-sky-50 to-white',
  peach: 'bg-gradient-to-b from-peach-50/80 to-white',
  mint: 'bg-gradient-to-b from-mint-50/80 to-white',
  pattern: 'pattern-bright pattern-dots',
  gradient: 'bg-gradient-to-br from-sky-50 via-white to-peach-50',
};

export default function SectionShell({ children, variant = 'white', className = '', id }: SectionShellProps) {
  return (
    <section id={id} className={`py-20 md:py-24 ${variants[variant]} ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">{children}</div>
    </section>
  );
}

interface SectionHeaderProps {
  label?: string;
  title: string;
  subtitle?: string;
  align?: 'left' | 'center';
}

export function SectionHeader({ label, title, subtitle, align = 'center' }: SectionHeaderProps) {
  return (
    <div className={`mb-14 ${align === 'center' ? 'text-center' : ''}`}>
      {label && <span className="section-label">{label}</span>}
      <h2 className="section-title">{title}</h2>
      {subtitle && <p className="text-slate-600 max-w-2xl text-lg leading-relaxed mx-auto">{subtitle}</p>}
    </div>
  );
}

interface HopeCardProps {
  message: string;
  submessage?: string;
  image?: string;
  imageFallback?: string;
  slides?: SlideImage[];
}

export function HopeCard({ message, submessage, image, imageFallback, slides }: HopeCardProps) {
  return (
    <div className="card-hope flex flex-col md:flex-row gap-6 items-center">
      {slides && slides.length > 0 ? (
        <div className="w-full md:w-72 flex-shrink-0">
          <ImageSlider
            slides={slides}
            aspectClass="aspect-[4/3]"
            innerClassName="rounded-2xl overflow-hidden shadow-soft"
          />
        </div>
      ) : image ? (
        <div className="relative w-full md:w-48 h-36 rounded-2xl overflow-hidden flex-shrink-0 shadow-soft">
          <SmartImage src={image} fallback={imageFallback} alt="" fill className="object-cover" />
        </div>
      ) : null}
      <div>
        <p className="text-lg font-medium text-primary-800 leading-relaxed">{message}</p>
        {submessage && <p className="text-slate-500 text-sm mt-2 leading-relaxed">{submessage}</p>}
      </div>
    </div>
  );
}
