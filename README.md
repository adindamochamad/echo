<div align="center">

# ⚡ ECHO

### Institutional Memory for Engineering Teams

**Stop letting your team repeat the same mistakes.**

ECHO connects today's incident to the post-mortem your team wrote — and forgot — months ago.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Claude](https://img.shields.io/badge/Claude-API-CC785C?style=flat)](https://anthropic.com)

[**Live Demo →**](https://echo-memory.vercel.app) &nbsp;|&nbsp; [API Docs →](https://echo-api.railway.app/docs)

</div>

---

## The Problem

Your team just spent 3 hours debugging a checkout outage. You write a thorough post-mortem. You assign action items. You close the ticket.

**Eight months later — checkout goes down again. Same root cause.**

This is not a rare failure. It is the default. Post-mortems get written, filed in Notion, and forgotten. Action items expire. Engineers who held the context leave. New engineers hit the same walls.

> **ECHO is the institutional memory your on-call rotation never had.**

---

## What ECHO Does

When a new incident comes in, ECHO:

1. **Extracts structure** — feeds raw incident notes to Claude and gets back root causes, action items, severity, and affected systems
2. **Generates a semantic embedding** — turns the incident fingerprint into a 1024-dimensional vector via Voyage AI
3. **Searches your history** — runs pgvector cosine similarity against every prior post-mortem in your workspace
4. **Surfaces the recurrence** — if a match is found, shows the original incident, the unimplemented action items, and exactly how many days have passed since you could have fixed this

The signal is not keyword matching. It is semantic — ECHO catches "DB connection pool exhaustion" matching "max_connections never reviewed since initial deploy" even when the wording is completely different.

---

## Live Demo

The demo tells a real story:

> *March 15, 2025 — Payment service outage. Root cause: DB connection pool set to 20, never reviewed. Action item: increase max_connections. Status: NEVER STARTED.*
>
> *November 8, 2025 — Checkout down 2h 51m during Black Friday. Same root cause.*
>
> *ECHO matches the two incidents with **62% semantic similarity**, surfaces 3 unimplemented action items from 238 days earlier, and renders its verdict: **this recurrence was preventable.***

The demo is live at the backend — hit `/api/v1/demo/climax` to see it in action without signing up.

---

## Features

### Core Intelligence
- **Claude-powered extraction** — paste raw Slack threads, doc exports, or messy notes; get structured post-mortems back
- **Voyage AI embeddings** — 1024-dim semantic vectors, model `voyage-3-large`, with hash-based fallback for offline mode
- **pgvector similarity search** — IVFFlat index, cosine distance, sub-10ms queries on 10k+ incidents
- **Recurrence detection** — threshold-based matching with discrimination gap validation (recurrence pair: 0.62, unrelated incident: 0.02)

### Product
- **Auth layer** — JWT-based registration and login, bcrypt passwords, org-namespaced workspaces
- **Persistent workspaces** — authenticated users get a private incident history with real pgvector search against their own data
- **Demo mode** — full feature demo without sign-up, rate-limited, stateless
- **Pattern Score** — dynamically computed 0–100 metric from recurrence rate × action item completion rate
- **Post-mortem detail pages** — per-incident view with all matches, action items, and the ECHO verdict

### Engineering
- **Async throughout** — `asyncio`, `asyncpg`, `AsyncSession`, async Voyage AI client
- **Rate limiting** — `slowapi` per-IP on demo endpoints
- **4-phase verification agents** — autonomous test agents that validate each build phase end-to-end (see below)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ECHO Frontend                       │
│              Next.js 14 · TypeScript · Tailwind         │
│                                                         │
│  / (landing)  /submit  /dashboard  /postmortems/[id]   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST / JSON
┌──────────────────────▼──────────────────────────────────┐
│                    ECHO Backend                         │
│                  FastAPI · Python 3.12                  │
│                                                         │
│  /api/v1/auth         JWT register · login · /me        │
│  /api/v1/postmortems  submit · list · get               │
│  /api/v1/demo         climax · incidents · analyze      │
└──────────┬─────────────┬──────────────┬─────────────────┘
           │             │              │
    ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │ Claude  │ │  Voyage AI  │
    │  pgvector   │ │   API   │ │  Embeddings │
    │ AsyncPG     │ │Extract  │ │ voyage-3-lg │
    └─────────────┘ └─────────┘ └─────────────┘
```

### Data Flow: Submit Post-Mortem

```
raw_content (messy notes)
       │
       ▼
  Claude API ──► { summary, root_causes, action_items, severity, systems_affected }
       │
       ▼
  build_embedding_text()  ──►  Voyage AI  ──►  float[1024]
       │
       ▼
  INSERT postmortems (embedding stored as pgvector)
       │
       ▼
  SELECT ... ORDER BY embedding <=> CAST(:vec AS vector)  ──►  top-5 matches
       │
       ▼
  PostmortemOut { ..., recurrence_matches: [...] }
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **API** | FastAPI + uvicorn | Async-first, automatic OpenAPI docs |
| **Database** | PostgreSQL + pgvector | Native vector search, no extra infra |
| **ORM** | SQLAlchemy 2.0 async | Type-safe, async sessions |
| **AI Extraction** | Anthropic Claude | Best-in-class unstructured text understanding |
| **Embeddings** | Voyage AI `voyage-3-large` | 1024-dim, optimized for technical documents |
| **Auth** | JWT (python-jose) + bcrypt | Stateless, secure, no session storage |
| **Frontend** | Next.js 14 App Router | Server components, fast navigation |
| **Styling** | Tailwind CSS | Design system tokens, dark/light themes |
| **Rate limiting** | slowapi | Per-IP limits on public endpoints |

---

## Quick Start

### Prerequisites

- Docker (for PostgreSQL)
- Python 3.12+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com)

### 1. Start the database

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Edit .env — add your ANTHROPIC_API_KEY
# Optional: add VOYAGE_API_KEY for real semantic embeddings
#           (falls back to deterministic hash embeddings without it)

uvicorn app.main:app --reload --port 8000
```

API is live at `http://localhost:8000`. Interactive docs at `/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 4. Verify the build

Each phase has an autonomous verification agent:

```bash
cd backend
make phase1   # Database schema + pgvector (no server needed)
make phase2   # Auth endpoints (requires: make dev)
make phase3   # Embeddings + similarity search
make phase4   # Demo data integrity + score computation
```

All agents exit `0` = all checks passed, `1` = warnings, `2` = critical failures.

---

## Environment Variables

```bash
# .env (backend + frontend share this file)

# Required
DATABASE_URL=postgresql+asyncpg://echo:echo@localhost:5432/echo
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enables real semantic embeddings (fallback: deterministic hash)
VOYAGE_API_KEY=pa-...

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Project Structure

```
echo/
├── backend/
│   ├── agents/                 # Autonomous verification agents
│   │   ├── base_agent.py       # AgentReport (ok/fail/warn + exit codes)
│   │   ├── phase1_database.py  # 36 checks: schema, indexes, pgvector
│   │   ├── phase2_auth.py      # 16 checks: register, login, JWT, concurrent
│   │   ├── phase3_embeddings.py # 15 checks: embed, store, search, recurrence
│   │   └── phase4_demo.py      # 27 checks: no hardcoded scores, diversity
│   ├── app/
│   │   ├── models.py           # SQLAlchemy ORM (User, Postmortem)
│   │   ├── routers/            # FastAPI routers (auth, postmortems, demo)
│   │   ├── services/           # Business logic (embedding, matching, demo data)
│   │   └── schemas/            # Pydantic request/response models
│   └── Makefile                # phase1–phase5 targets
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing — live demo narrative
│   │   ├── dashboard/          # Workspace dashboard (5 tabs)
│   │   ├── submit/             # Submit post-mortem (paste or file upload)
│   │   ├── postmortems/[id]/   # Post-mortem detail view
│   │   ├── login/ register/    # Auth pages
│   ├── components/
│   │   ├── RecurrenceAlert.tsx # The core ECHO verdict card
│   │   ├── SideBySide.tsx      # Incident comparison view
│   │   ├── PatternScoreGauge.tsx
│   │   └── IncidentTimeline.tsx
│   └── lib/
│       ├── api.ts              # Typed API client
│       └── auth.ts             # JWT localStorage helpers
├── .env.example
└── docker-compose.yml
```

---

## The Verification Agents

ECHO ships with 4 autonomous agents that verify every layer of the stack after each build phase. Each agent makes real HTTP calls, queries the database directly, and validates computed values — not mocks.

```
Phase 1 — Database Foundation    36 passed  0 failed
Phase 2 — Auth Layer             16 passed  0 failed
Phase 3 — Embeddings & Search    15 passed  2 warnings (expected — no Voyage key in CI)
Phase 4 — Demo Data Integrity    27 passed  0 failed
                                 ─────────────────────
                                 94 checks  0 critical failures
```

The agents check things tests can't easily verify: that hardcoded scores have been removed, that similarity discrimination between related and unrelated incidents exceeds a threshold, that auth tokens contain the right payload shape, that concurrent registrations don't race.

---

## API Reference

### Demo (no auth)

```
GET  /api/v1/demo/climax         → ClimaxResponse (the full narrative)
GET  /api/v1/demo/incidents      → IncidentSummary[]
GET  /api/v1/demo/pattern-score  → PatternScoreResponse
POST /api/v1/demo/analyze        → AnalyzeResponse (rate-limited)
```

### Auth

```
POST /api/v1/auth/register  → TokenResponse
POST /api/v1/auth/login     → TokenResponse
GET  /api/v1/auth/me        → UserOut (JWT required)
```

### Postmortems (JWT required)

```
POST /api/v1/postmortems        → PostmortemOut (extract + embed + search)
GET  /api/v1/postmortems        → PostmortemOut[] (your history)
GET  /api/v1/postmortems/{id}   → PostmortemOut
```

---

## Why ECHO

Most incident management tools help you document failures. ECHO helps you **not repeat them**.

The key insight is that recurrence is a memory problem, not a process problem. Teams already write post-mortems. They already create action items. The breakdown happens in retrieval — when a new incident arrives, nobody searches the archive, and nobody remembers the action items that expired 6 months ago.

ECHO makes retrieval automatic. The moment a post-mortem is submitted, ECHO runs similarity search across your entire history. If the pattern exists, you see it before you spend 3 hours debugging something that was already root-caused.

The demo shows this with real data: 62% semantic similarity, 238 days apart, 3 unimplemented action items. That's not a made-up number — it's the computed score from the actual matching algorithm running against the actual incident data.

---

<div align="center">

**[Try the live demo →](https://echo-memory.vercel.app)**

</div>
