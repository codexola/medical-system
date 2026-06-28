/** @type {import('next').NextConfig} */

function apiRemotePattern() {
  const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  try {
    const url = new URL(raw);
    return {
      protocol: url.protocol.replace(':', ''),
      hostname: url.hostname,
      ...(url.port ? { port: url.port } : {}),
      pathname: '/api/media/**',
    };
  } catch {
    return { protocol: 'http', hostname: 'localhost', port: '8000', pathname: '/api/media/**' };
  }
}

const nextConfig = {
  images: {
    remotePatterns: [
      apiRemotePattern(),
      { protocol: 'https', hostname: '**' },
      { protocol: 'http', hostname: 'localhost', port: '8000', pathname: '/api/media/**' },
    ],
    unoptimized: true,
  },
  // Allow VPS API hostname in production when set via env
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
