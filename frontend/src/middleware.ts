import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ROLE_COOKIE, TOKEN_COOKIE } from '@/lib/auth-cookies';

function roleHome(role: string): string {
  if (role === 'admin') return '/admin';
  if (role === 'developer') return '/developer';
  if (role === 'patient') return '/dashboard';
  return '/login';
}

function redirect(request: NextRequest, pathname: string) {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  if (pathname === '/login' && request.nextUrl.pathname !== '/login') {
    url.searchParams.set('next', request.nextUrl.pathname);
  }
  return NextResponse.redirect(url);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(TOKEN_COOKIE)?.value;
  const role = request.cookies.get(ROLE_COOKIE)?.value;

  // Auth cookies are set on login; client RequireAuth also checks localStorage and syncs cookies.
  if (!token) {
    return NextResponse.next();
  }

  if (pathname.startsWith('/dashboard')) {
    if (role === 'admin') return redirect(request, '/admin');
    if (role === 'developer') return redirect(request, '/developer');
    if (role && role !== 'patient') return redirect(request, '/login');
  }

  if (pathname.startsWith('/admin') && role !== 'admin') {
    return redirect(request, role ? roleHome(role) : '/login');
  }

  if (pathname.startsWith('/developer') && role !== 'developer') {
    return redirect(request, role ? roleHome(role) : '/login');
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/admin/:path*', '/developer/:path*'],
};
