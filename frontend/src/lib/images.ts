/** Image library — static files in /public/images with API fallback */

import type { SlideImage } from '@/components/ImageSlider';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const mediaSlugUrl = (slug: string) => `${API_URL}/media/slug/${slug}`;

/** Serve from Next.js public folder (works without backend). */
export const staticImageUrl = (filename: string) => `/images/${filename}`;

const img = (slug: string, ext = 'jpg', fallbackSlug = 'hero-healthcare') => ({
  primary: staticImageUrl(`${slug}.${ext}`),
  fallback: mediaSlugUrl(fallbackSlug),
});

const slideSlug = (prefix: string, index: number) =>
  `slide-${prefix}-${String(index).padStart(2, '0')}`;

const slideSet = (prefix: string, count: number, alt: string): SlideImage[] =>
  Array.from({ length: count }, (_, i) => {
    const slug = slideSlug(prefix, i + 1);
    return {
      src: staticImageUrl(`${slug}.webp`),
      fallback: mediaSlugUrl(slug),
      alt,
    };
  });

export const Images = {
  hero: img('bright-hero'),
  mascot: img('bright-mascot'),
  dashboardGreeting: img('bright-dashboard-greeting'),
  doctor: img('bright-doctor'),
  patientHope: img('bright-patient-hope'),
  consultation: img('bright-consultation'),
  team: img('bright-team'),
  recovery: img('bright-recovery'),
  featureAiChat: img('bright-feature-chat'),
  featureRag: img('bright-feature-rag'),
  featureReservation: img('bright-feature-reservation'),
  featureHospital: img('bright-feature-hospital'),
  featureHealth: img('bright-feature-health'),
  usageLine: img('bright-usage-line'),
  usageBooking: img('bright-usage-booking'),
  loginBg: img('bright-login'),
  hospitalBanner: img('bright-hospital'),
  pricingHero: img('bright-pricing'),
  dashboardHero: img('bright-dashboard-greeting'),
  symptomCheck: img('bright-symptom'),
  bgPattern: img('bright-bg-pattern'),
} as const;

/** Homepage slider sets — 5 images per section (slide-*.webp in public/images). */
export const SliderImages = {
  hero: slideSet('hero', 5, 'AI healthcare reception'),
  hope: slideSet('hope', 5, 'Courageous choice to seek treatment'),
  team: slideSet('team', 5, 'Welcoming medical care team'),
  guide: slideSet('guide', 5, 'How to use Kenko AI'),
  recovery: slideSet('recovery', 5, 'Recovery and smiling again'),
  featureAi: slideSet('feature-ai', 5, 'AI medical reception'),
  featureRag: slideSet('feature-rag', 5, 'Medical knowledge RAG'),
  featureReservation: slideSet('feature-reservation', 5, 'Smart appointment booking'),
  featureHospital: slideSet('feature-hospital', 5, 'Hospital search and recommendation'),
  featureHealth: slideSet('feature-health', 5, 'Health timeline'),
  featureSubscription: slideSet('feature-subscription', 5, 'Healthcare subscription'),
} as const;

export const featureSliderSets = [
  SliderImages.featureAi,
  SliderImages.featureRag,
  SliderImages.featureReservation,
  SliderImages.featureHospital,
  SliderImages.featureHealth,
  SliderImages.featureSubscription,
];

export const featureImages = [
  Images.featureAiChat,
  Images.featureRag,
  Images.featureReservation,
  Images.featureHospital,
  Images.featureHealth,
  Images.pricingHero,
];

export const profilePhotoUrl = (assetId?: string | null) =>
  assetId ? `${API_URL}/media/${assetId}` : null;

export const absoluteMediaUrl = (url?: string | null) => {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  const origin = API_URL.replace(/\/api\/?$/, '');
  return `${origin}${url.startsWith('/') ? url : `/${url}`}`;
};
