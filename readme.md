# SmartStock AI

[![CI](https://github.com/Eng-Ayman-Mohamed/SmartStock-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Eng-Ayman-Mohamed/SmartStock-AI/actions/workflows/ci.yml)
[![Docker Build](https://github.com/Eng-Ayman-Mohamed/SmartStock-AI/actions/workflows/docker-build.yml/badge.svg)](https://github.com/Eng-Ayman-Mohamed/SmartStock-AI/actions/workflows/docker-build.yml)

> AI-powered Inventory Management Platform — proactive demand planning, LLM-powered analytics, and autonomous purchasing agents.

**Team:** Horizonte Infinito — Ayman Mohamed · Omar Wael · Mostafa Abdel Aziz · Mostafa Abdel Qawy · Mawada Alexander

**Target Industry:** Logistics, E-commerce, and Retail Supply Chain

---

## Problem

E-commerce and logistics enterprises lose revenue to two inventory failure modes: **overstocking** (immobilised working capital) and **stockouts** (lost sales). Incumbent systems are reactive — relying on manual audits that miss seasonal demand curves, macroeconomic signals, and supplier lead-time variability.

## Solution

SmartStock AI couples **real-time inventory tracking** with **AI-driven demand forecasting** to shift decision-making from reactive correction to anticipatory action. The system notifies managers of impending shortfalls before they materialise, auto-drafts purchase orders, and provides a natural-language interface for ad-hoc analytics.

---

## Key Features

- **Inventory Management** — CRUD for products, SKUs, stock levels with low-stock alerts
- **Demand Forecasting** — Prophet time-series model per SKU with Recharts visualisation
- **NL Analytics** — Natural-language queries against inventory data via GPT-4o + LangChain
- **RAG Pipeline** — Hybrid search (pgvector dense + PostgreSQL FTS) with Cohere reranking and source citations
- **Multi-Agent Pipeline** — Forecasting Agent → Decision Agent → Purchasing Agent (HITL)
- **Multimodal Input** — GPT-4o Vision invoice scanning + Whisper speech-to-text
- **RBAC** — Viewer / Manager / Admin roles with JWT authentication
- **Observability** — Langfuse tracing for LLM calls, RAG retrieval, and agent actions

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 · TypeScript · Vite 8 · Tailwind CSS 4 · Recharts · React Query · Zustand |
| **Backend** | Django 5 · DRF · Python 3.12 · Celery |
| **Database** | PostgreSQL 16 · pgvector · Redis 7 |
| **AI / ML** | Prophet · LangChain · GPT-4o · text-embedding-3-small · Cohere |
| **Infrastructure** | Docker · GitHub Actions · Railway (deploy) |
| **Monitoring** | Prometheus · Grafana · Alertmanager · Langfuse |

---

## Architecture

The project follows **Clean Architecture** with feature-based Django apps. Outer layers depend on inner layers — never the other way around.

```
Presentation  ──►  Application  ──►  Domain  ──►  Infrastructure
(DRF Views)      (Services)        (Entities)     (DB / Cache / Email)
```

Each Django app (`authentication`, `inventory`, `forecasting`, `purchasing`, `audit`) is a vertical slice containing its own models, views, services, and repositories.

The AI layer (`ai/`) is fully isolated — swapping GPT-4o for another model only touches `ai/llm/chain.py`.

See [`Systemarchitecture.md`](Systemarchitecture.md) for the full architectural reference.

---

## Project Structure

```
smartstock-backend/           # Django REST API (Clean Architecture)
├── config/                   # Project settings (dev/prod), Celery, URL routing
├── apps/                     # Feature-based Django apps
│   ├── authentication/       # JWT, RBAC, CustomUser model
│   ├── inventory/            # Products, SKUs, stock levels
│   ├── forecasting/          # Prophet model, reorder logic
│   ├── purchasing/           # Purchase orders, supplier management
│   ├── ingestion/            # Document upload, RAG query
│   ├── audit/                # Audit logging (signals + middleware)
│   ├── monitoring/           # Prometheus metrics, alerting
│   ├── notifications/        # Email + dashboard notifications
│   └── health/               # Readiness / liveness probes
├── ai/                       # Isolated AI layer
│   ├── llm/                  # LangChain chain, prompts, output parser
│   ├── rag/                  # Ingestion, hybrid retrieval, citation
│   ├── agents/               # 3 agents + 8 plugin tools
│   ├── multimodal/           # Vision OCR, Whisper STT
│   ├── evaluation/           # AI evaluation metrics
│   └── observability/        # Langfuse tracing integration
├── core/                     # Shared abstractions (BaseRepository, exceptions)
├── infrastructure/           # Redis, email, file storage wrappers
├── tests/                    # Unit, integration, golden dataset
├── Dockerfile
├── entrypoint.sh
├── railway.toml              # Railway web service config
├── railway.worker.toml       # Railway Celery worker config
└── DEPLOY.md                 # Detailed deployment guide

smartstock-frontend/          # React + TypeScript SPA
├── src/
│   ├── features/             # Vertical slices per domain
│   │   ├── ai-assistant/     # AI chat & voice assistant
│   │   ├── auth/             # Login, register, session management
│   │   ├── dashboard/        # Dashboard widgets & metrics
│   │   ├── forecasting/      # Demand forecasting charts & alerts
│   │   ├── inventory/        # Product & stock management
│   │   ├── invoice-scan/     # AI-powered invoice scanning
│   │   ├── purchasing/       # Purchase orders & suppliers
│   │   └── users/            # User management (admin)
│   ├── lib/                  # Axios, React Query, Router config
│   ├── shared/               # Reusable components/hooks
│   └── store/                # Zustand (client state only)
├── Dockerfile                # Multi-stage build (Node → Nginx)
├── nginx.conf                # Production reverse proxy
└── docker-entrypoint.sh      # Runtime env injection for Docker

monitoring/                   # Observability stack
├── prometheus/               # Prometheus config + alert rules
├── grafana/                  # Pre-built dashboards + datasources
└── alertmanager/             # Alert routing config
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 22+
- PostgreSQL 16+ (with pgvector extension)
- Redis 7+
- OpenAI API key
- Cohere API key (for RAG reranking)

### Backend Setup

```bash
cd smartstock-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your environment variables
python manage.py migrate
python manage.py runserver
```

The API is available at `http://localhost:8000/api/`. Swagger docs at `http://localhost:8000/api/schema/swagger-ui/`.

### Frontend Setup

```bash
cd smartstock-frontend
cp .env.example .env.local
npm install
npm run dev
```

Dev server starts on `http://localhost:5173`. API requests to `/api` are proxied to `http://localhost:8000`.

### Docker (Full Stack)

```bash
docker compose up --build
```

This starts all services:

| Service | Container | URL |
|---------|-----------|-----|
| **Frontend** | `smartstock_frontend` | http://localhost:3000 |
| **Backend API** | `smartstock_backend` | http://localhost:8000/api/ |
| **Celery Worker** | `smartstock_celery` | — |
| **Celery Beat** | `smartstock_celery_beat` | — |
| **PostgreSQL** | `smartstock_db` | localhost:5433 |
| **Redis** | `smartstock_redis` | localhost:6379 |
| **Prometheus** | `smartstock_prometheus` | http://localhost:9090 |
| **Alertmanager** | `smartstock_alertmanager` | http://localhost:9093 |
| **Grafana** | `smartstock_grafana` | http://localhost:3001 |

> **Note:** The root `.env` file is shared by all Docker services. Copy `.env.example` at the repo root if one doesn't exist.

### Environment Variables

| Service | Required Vars | See |
|---------|---------------|-----|
| Backend | `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`, `COHERE_API_KEY` | [`smartstock-backend/.env.example`](smartstock-backend/.env.example) |
| Frontend | `VITE_API_URL` (has default) | [`smartstock-frontend/.env.example`](smartstock-frontend/.env.example) |

Each service's `.env.example` is annotated with purpose, defaults, and required/optional markers.

---

## Available Commands

### Backend

```bash
ruff check .                   # Lint
ruff format .                  # Format
pytest                         # Run tests (SQLite in-memory)
pytest --cov=. --cov-report=html  # With coverage
python manage.py migrate       # Run migrations
python manage.py createsuperuser
python manage.py seed_data     # Populate test data
```

### Frontend

```bash
npm run dev                    # Vite dev server (port 5173, HMR)
npm run build                  # tsc -b + vite build
npm run preview                # Preview production build
npm run lint                   # ESLint
```

### Docker

```bash
docker compose up --build      # Build + start all services
docker compose down            # Stop all services
docker compose logs -f backend # Tail backend logs
docker compose exec backend python manage.py shell  # Django shell
```

---

## Testing

### Backend

```bash
cd smartstock-backend
pytest                                    # Unit + integration (SQLite)
DATABASE_URL=postgres://... pytest        # Against real Postgres
pytest tests/unit/                        # Unit tests only
pytest tests/integration/                 # Integration tests only
```

- Tests use `config.settings.test` (Redis disabled, Celery eager, Cloudinary disabled)
- CI enforces ≥80% coverage (`--cov-fail-under=80`)
- Golden dataset: 30 annotated NL queries run in CI on merge to main
- OpenAPI schema validation runs in CI

### Frontend

```bash
cd smartstock-frontend
npm run lint                  # ESLint
npx tsc --noEmit              # Type checking
```

No test framework is currently configured. CI runs lint + build on every push/PR.

---

## CI/CD

GitHub Actions workflows on push to `main`/`develop` and PRs to `main`:

| Job | What it does |
|-----|-------------|
| `backend-lint` | `ruff check` + `ruff format --check` |
| `backend-test` | `pytest` with Postgres service container, ≥80% coverage gate, OpenAPI schema validation |
| `backend-check` | `python manage.py check` (system check) |
| `frontend-lint` | `npm run lint` + `tsc --noEmit` |
| `frontend-build` | `npm run build` |

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and [`.github/workflows/docker-build.yml`](.github/workflows/docker-build.yml).

---

## Deployment

### Backend — Railway

Deploys via two Railway services from the same Docker image:

| Service | Config | Start Command |
|---|---|---|
| `smartstock-api` | `railway.toml` | `migrate` + `gunicorn` |
| `smartstock-worker` | `railway.worker.toml` | `celery worker` |

See [`smartstock-backend/DEPLOY.md`](smartstock-backend/DEPLOY.md) for the full deployment checklist.

### Frontend — Vercel / Docker

- **Vercel:** Deploy `dist/` to Vercel. Set `VITE_API_BASE_URL` to your backend URL.
- **Docker:** `docker compose up --build` runs the full stack with Nginx serving the SPA and proxying API calls.

---

## Monitoring

The Docker Compose stack includes a full observability suite:

- **Prometheus** — scrapes backend metrics, 30-day retention
- **Grafana** — pre-built dashboards at http://localhost:3001 (admin/smartstock)
- **Alertmanager** — routes alerts for latency p95 >3s, error rate >1%, budget caps
- **Langfuse** — traces every LLM call, RAG retrieval, and agent tool invocation (requires `LANGFUSE_*` env vars)

---

## Security

- **JWT** authentication (15-min access + 7-day refresh as HttpOnly cookie)
- **RBAC** — Viewer (read-only), Manager (approve POs), Admin (full access)
- **HITL** — No PO dispatched without manager approval
- **Prompt injection** defence via isolated system prompts + output validation
- **Rate limiting** — 100 req/min/user, daily LLM token quotas
- All secrets managed via `.env`, never hardcoded

See [`Systemarchitecture.md`](Systemarchitecture.md) §9 for the full security model.

---

## Further Reading

| Document | Description |
|----------|-------------|
| [`Systemarchitecture.md`](Systemarchitecture.md) | Full architectural reference (688 lines) |
| [`DESIGN.md`](DESIGN.md) | Design system and UI guidelines |
| [`design-system-prompt.md`](design-system-prompt.md) | Tailwind token reference (brand colors) |
| [`Project-blueprint.md`](Project-blueprint.md) | Project blueprint and planning |
| [`Future-Work.md`](Future-Work.md) | Planned features and improvements |
| [`reports/security-audit-report.md`](reports/security-audit-report.md) | Security audit findings |
| [`reports/performance-report.md`](reports/performance-report.md) | Performance analysis |
| [`smartstock-backend/DEPLOY.md`](smartstock-backend/DEPLOY.md) | Railway deployment guide |

---

## License

Graduation Project — ITI (Information Technology Institute)
