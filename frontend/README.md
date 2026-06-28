# Kenko AI — Frontend

Next.js frontend for the Japanese medical consultation platform. Deploy on [Vercel](https://vercel.com); API runs on your VPS.

## Environment

Create `.env.local` (or set in Vercel Dashboard):

```bash
NEXT_PUBLIC_API_URL=https://your-vps-domain.com/api
```

## Local development

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Deploy on Vercel

1. Import this repository in Vercel
2. Framework: **Next.js** (auto-detected)
3. Set `NEXT_PUBLIC_API_URL` to your VPS API URL (include `/api`)
4. Deploy

On your VPS backend, add your Vercel URL to `CORS_ORIGINS` in `.env`.
