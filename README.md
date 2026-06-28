# Kenko AI Healthcare Platform (健康AI)

AI-powered healthcare platform for Japanese clinics, combining medical reception, reservations, RAG knowledge base, hospital search, subscription management, and admin dashboard.

## Architecture

```
Patient → LINE / Web → FastAPI Backend
                         ├── AI Agents (GPT-4o / Claude)
                         ├── RAG (pgvector)
                         ├── Reservation Engine
                         ├── Hospital Recommendation
                         ├── Subscription (Stripe)
                         └── PostgreSQL + Redis + Celery
Frontend (Next.js) → XSERVER / Vercel
Backend (Docker)   → VPS (Ubuntu + Nginx)
```

## Features

- **AI Medical Receptionist** — 24/7 symptom consultation via LINE and Web
- **RAG Knowledge Base** — Clinic FAQs, insurance, treatment info, medical guidelines
- **Smart Reservations** — Google Calendar integration, availability checking
- **Hospital Search & Recommendation** — National hospital database with geo-based matching
- **Health Timeline** — Daily check-ins, mood tracking, medication reminders
- **Subscription Platform** — 7-day free trial, Standard/Premium/Enterprise plans
- **Admin Dashboard** — Reservations, patients, AI logs, analytics, FAQ management
- **Multi-language** — Japanese (default) and English

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+
- Python 3.12+

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (OpenAI, LINE, Stripe)
```

### 2. Start Backend Services

```bash
docker compose up -d postgres redis
docker compose up -d backend celery celery-beat
```

### 3. Seed Database

```bash
cd backend
pip install -r requirements.txt
python scripts/seed_data.py
```

Default admin credentials: `admin@kenko-ai.jp` / `admin123`

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

### 5. Generate Images (Optional)

```bash
OPENAI_API_KEY=your-key python scripts/generate_images.py
```

## API Endpoints

| Route | Description |
|-------|-------------|
| `POST /api/auth/register` | Patient registration |
| `POST /api/auth/login` | Patient login |
| `POST /api/chat/` | AI chat |
| `POST /api/chat/assess` | Symptom assessment |
| `POST /api/reservation/` | Create reservation |
| `POST /api/hospital/recommend` | Hospital recommendation |
| `POST /api/line/webhook` | LINE Messaging API webhook |
| `GET /api/admin/dashboard` | Admin dashboard stats |
| `POST /api/rag/query` | RAG knowledge query |
| `GET /api/subscription/status` | Subscription status |

Full API docs at http://localhost:8000/docs

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── ai/           # AI providers, agents, prompts
│   │   ├── rag/          # RAG service
│   │   ├── line/         # LINE Messaging API client
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API routes
│   │   ├── services/     # Business logic
│   │   └── main.py
│   └── scripts/seed_data.py
├── frontend/
│   └── src/
│       ├── app/          # Next.js pages
│       ├── components/   # React components
│       └── lib/          # API client, i18n
├── nginx/
├── docker-compose.yml
└── scripts/
```

## Deployment

### Frontend (Vercel) + Backend (VPS)

**Architecture:** Next.js on [Vercel](https://vercel.com) → FastAPI on your VPS.

#### 1. Push to GitHub

Repository: [github.com/codexola/-](https://github.com/codexola/-)

```bash
git remote add origin https://github.com/codexola/-.git
git push -u origin main
```

#### 2. Deploy frontend on Vercel

1. Import the GitHub repo in Vercel
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-vps-domain.com/api`
4. Deploy

`frontend/vercel.json` is included. Production build: `npm run build` (verified).

#### 3. Configure VPS backend

On the VPS `.env`:

```bash
# Allow your Vercel URL (comma-separated if multiple)
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
FRONTEND_URL=https://your-app.vercel.app
```

Start backend from `backend/` (not project root):

```bash
./scripts/start-backend.sh
# or: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Expose port 8000 via Nginx + HTTPS (e.g. `api.your-domain.com`).

#### 4. Verify

- Vercel site loads and login works
- Browser devtools → Network: API calls go to your VPS URL
- Backend `/health` returns OK

### Backend (VPS) — Docker alternative

```bash
docker compose up -d
# Configure Nginx SSL with Certbot
```

### Frontend (XSERVER) — alternative

```bash
cd frontend && npm run build
# Upload build output to XSERVER
```

## LINE Integration

1. Create LINE Official Account at [developers.line.biz](https://developers.line.biz)
2. Enable Messaging API channel
3. Set webhook URL: `https://api.clinic.example.jp/api/line/webhook`
4. Add Channel Secret and Access Token to `.env`

## Disclaimer

This platform provides AI-assisted symptom assessment and healthcare information. It does **not** provide medical diagnoses. Users should consult licensed healthcare professionals for medical decisions.

## License

Proprietary — Kenko AI Healthcare Platform
