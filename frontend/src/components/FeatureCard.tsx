'use client';

import ImageSlider, { SlideImage } from './ImageSlider';
import SmartImage from './SmartImage';

interface FeatureCardProps {
  title: string;
  description: string;
  image?: string;
  imageFallback?: string;
  slides?: SlideImage[];
  index: number;
  hopeNote?: string;
}

export default function FeatureCard({
  title,
  description,
  image,
  imageFallback,
  slides,
  index,
  hopeNote,
}: FeatureCardProps) {
  const reversed = index % 2 === 1;

  return (
    <div
      className={`flex flex-col ${reversed ? 'lg:flex-row-reverse' : 'lg:flex-row'} gap-8 lg:gap-12 items-center py-10`}
    >
      <div className="flex-1 w-full relative">
        {slides && slides.length > 0 ? (
          <ImageSlider
            slides={slides}
            aspectClass="aspect-[16/10]"
            innerClassName="rounded-3xl overflow-hidden shadow-soft ring-2 ring-white"
          />
        ) : (
          <div className="relative rounded-3xl overflow-hidden shadow-soft ring-2 ring-white aspect-[16/10]">
            <SmartImage src={image!} fallback={imageFallback} alt={title} fill className="object-cover" />
          </div>
        )}
      </div>
      <div className="flex-1">
        <h3 className="font-serif text-2xl md:text-3xl font-bold text-primary-800 mb-3">{title}</h3>
        <p className="text-slate-600 leading-relaxed text-lg mb-4">{description}</p>
        {hopeNote && (
          <p className="text-sm text-mint-700 bg-mint-50 border border-mint-100 rounded-2xl px-4 py-3 leading-relaxed">
            {hopeNote}
          </p>
        )}
      </div>
    </div>
  );
}
