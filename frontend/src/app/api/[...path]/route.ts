import { NextRequest, NextResponse } from 'next/server';

const BACKEND = (process.env.BACKEND_URL || 'http://210.131.217.208:8000').replace(/\/$/, '');

export const dynamic = 'force-dynamic';

async function proxy(request: NextRequest, path: string[]) {
  const target = `${BACKEND}/api/${path.join('/')}${request.nextUrl.search}`;

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);
  const authorization = request.headers.get('authorization');
  if (authorization) headers.set('authorization', authorization);
  const accept = request.headers.get('accept');
  if (accept) headers.set('accept', accept);

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: 'no-store',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete('content-encoding');
  responseHeaders.delete('transfer-encoding');

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

type RouteContext = { params: { path: string[] } };

export async function GET(request: NextRequest, { params }: RouteContext) {
  return proxy(request, params.path);
}

export async function POST(request: NextRequest, { params }: RouteContext) {
  return proxy(request, params.path);
}

export async function PUT(request: NextRequest, { params }: RouteContext) {
  return proxy(request, params.path);
}

export async function PATCH(request: NextRequest, { params }: RouteContext) {
  return proxy(request, params.path);
}

export async function DELETE(request: NextRequest, { params }: RouteContext) {
  return proxy(request, params.path);
}
