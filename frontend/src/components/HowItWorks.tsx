'use client';

import ImageSlider, { SlideImage } from './ImageSlider';
import SmartImage from './SmartImage';

interface HowItWorksProps {
  title: string;
  subtitle?: string;
  image?: string;
  imageFallback?: string;
  slides?: SlideImage[];
  steps: { title: string; description: string }[];
}

export default function HowItWorks({ title, subtitle, image, imageFallback, slides, steps }: HowItWorksProps) {
  return (
    <section className="py-20 bg-gradient-to-b from-white to-sky-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <span className="section-label">Guide</span>
          <h2 className="section-title">{title}</h2>
          {subtitle && <p className="text-slate-600 max-w-2xl mx-auto text-lg">{subtitle}</p>}
        </div>

        <div className="grid lg:grid-cols-2 gap-10 items-center">
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
          <div className="space-y-5">
            {steps.map((step, i) => (
              <div key={i} className="card-bright flex gap-4 items-start !p-5">
                <div className="flex-shrink-0 w-11 h-11 rounded-2xl bg-gradient-to-br from-primary-300 to-mint-400 text-white flex items-center justify-center font-bold shadow-soft">
                  {i + 1}
                </div>
                <div>
                  <h4 className="font-semibold text-primary-800 mb-1">{step.title}</h4>
                  <p className="text-slate-500 text-sm leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
