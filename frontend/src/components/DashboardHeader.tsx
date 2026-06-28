'use client';

import SmartImage from './SmartImage';
import { Images } from '@/lib/images';

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  image?: string;
  imageFallback?: string;
}

export default function DashboardHeader({
  title,
  subtitle,
  image = Images.dashboardHero.primary,
  imageFallback = Images.dashboardHero.fallback,
}: DashboardHeaderProps) {
  return (
    <div className="dashboard-header">
      <SmartImage src={image} fallback={imageFallback} alt="" fill className="object-cover" />
      <div className="absolute inset-0 bg-gradient-to-r from-primary-900/85 to-primary-700/50" />
      <div className="absolute inset-0 flex items-center px-6 md:px-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white font-serif">{title}</h1>
          {subtitle && <p className="text-primary-100 text-sm mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}
