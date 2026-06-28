'use client';

import { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import SmartImage from './SmartImage';

export interface SlideImage {
  src: string;
  fallback?: string;
  alt: string;
}

interface ImageSliderProps {
  slides: SlideImage[];
  className?: string;
  innerClassName?: string;
  aspectClass?: string;
  intervalMs?: number;
  priority?: boolean;
  showControls?: boolean;
}

export default function ImageSlider({
  slides,
  className = '',
  innerClassName = 'rounded-3xl overflow-hidden shadow-glow ring-4 ring-white',
  aspectClass = 'aspect-[4/3]',
  intervalMs = 5000,
  priority = false,
  showControls = true,
}: ImageSliderProps) {
  const [index, setIndex] = useState(0);

  const next = useCallback(
    () => setIndex((i) => (i + 1) % slides.length),
    [slides.length]
  );
  const prev = useCallback(
    () => setIndex((i) => (i - 1 + slides.length) % slides.length),
    [slides.length]
  );

  useEffect(() => {
    if (slides.length <= 1) return;
    const id = setInterval(next, intervalMs);
    return () => clearInterval(id);
  }, [next, intervalMs, slides.length]);

  if (!slides.length) return null;

  return (
    <div className={`relative ${aspectClass} ${className}`}>
      <div className={`absolute inset-0 ${innerClassName}`}>
        {slides.map((slide, i) => (
          <div
            key={slide.src}
            className={`absolute inset-0 transition-opacity duration-700 ease-in-out ${
              i === index ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
            aria-hidden={i !== index}
          >
            <SmartImage
              src={slide.src}
              fallback={slide.fallback}
              alt={slide.alt}
              fill
              className="object-cover"
              priority={priority && i === 0}
            />
          </div>
        ))}
      </div>

      {showControls && slides.length > 1 && (
        <>
          <button
            type="button"
            onClick={prev}
            className="absolute left-3 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/90 shadow-md flex items-center justify-center text-primary-700 hover:bg-white transition-colors"
            aria-label="Previous slide"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={next}
            className="absolute right-3 top-1/2 -translate-y-1/2 z-10 w-9 h-9 rounded-full bg-white/90 shadow-md flex items-center justify-center text-primary-700 hover:bg-white transition-colors"
            aria-label="Next slide"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-10 flex gap-1.5">
            {slides.map((slide, i) => (
              <button
                key={slide.src}
                type="button"
                onClick={() => setIndex(i)}
                className={`h-2 rounded-full transition-all ${
                  i === index ? 'w-6 bg-white' : 'w-2 bg-white/60 hover:bg-white/80'
                }`}
                aria-label={`Go to slide ${i + 1}`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
