'use client';

import Image from 'next/image';
import { useState } from 'react';

interface SmartImageProps {
  src: string;
  fallback?: string;
  alt: string;
  width?: number;
  height?: number;
  fill?: boolean;
  className?: string;
  priority?: boolean;
}

export default function SmartImage({
  src,
  fallback,
  alt,
  width,
  height,
  fill,
  className = '',
  priority,
}: SmartImageProps) {
  const [current, setCurrent] = useState(src);

  const props = fill
    ? { fill: true as const, sizes: '(max-width: 768px) 100vw, 50vw' }
    : { width: width || 800, height: height || 500 };

  return (
    <Image
      {...props}
      src={current}
      alt={alt}
      className={className}
      priority={priority}
      onError={() => {
        if (fallback && current !== fallback) {
          setCurrent(fallback);
        }
      }}
    />
  );
}
