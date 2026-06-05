# SmartStock AI

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
| **Frontend** | React · TypeScript · Tailwind CSS · Recharts · React Query · Zustand |
| **Backend** | Django REST Framework · Python |
| **Database** | PostgreSQL · pgvector · Redis |
| **AI / ML** | Prophet · LangChain · GPT-4o · text-embedding-3-small · Cohere |
| **Infrastructure** | Docker · GitHub Actions · Celery |

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
smartstock-backend/       # Django REST API (Clean Architecture)
├── config/               # Project settings (dev/prod), Celery, URL routing
├── apps/                 # Feature-based Django apps (5 domains)
│   ├── authentication/   # JWT, RBAC, CustomUser model
│   ├── inventory/        # Products, SKUs, stock levels
│   ├── forecasting/      # Prophet model, reorder logic
│   ├── purchasing/       # Purchase orders, supplier management
│   └── audit/            # Audit logging (signals + middleware)
├── ai/                   # Isolated AI layer
│   ├── llm/              # LangChain chain, prompts, output parser
│   ├── rag/              # Ingestion, hybrid retrieval, citation
│   ├── agents/           # 3 agents + 8 plugin tools
│   └── multimodal/       # Vision OCR, Whisper STT
├── core/                 # Shared abstractions (BaseRepository, exceptions)
└── infrastructure/       # Redis, email, file storage wrappers

smartstock-frontend/      # React + TypeScript SPA
└── src/
    ├── features/         # Vertical slices per domain
    ├── shared/           # Reusable components/hooks
    ├── lib/              # Axios, React Query, Router config
    └── store/            # Zustand (client state only)
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (with pgvector extension)
- Redis

### Backend Setup

```bash
cd smartstock-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your environment variables
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd smartstock-frontend
npm install
cp .env.example .env.local
npm run dev
```

### Docker (alternative)

```bash
docker compose up --build
```

---

## Delivery Roadmap

| Week | Milestone |
|------|-----------|
| 1 | Core inventory CRUD, dashboard, PostgreSQL schema, JWT auth |
| 2 | Prophet forecasting engine, historical sales ingestion, recharts chart |
| 3 | GPT-4o NL query pipeline, 5 few-shot examples, RAG pipeline |
| 4 | Purchasing Agent (HITL), email integration, approval workflow |

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

## Observability

- **Langfuse** traces every LLM call, RAG retrieval, and agent tool invocation
- 3 core metrics: Retrieval Precision@5 (≥0.80), Answer Faithfulness (≥0.85), Agent Success Rate (≥0.90)
- Golden dataset of 30 annotated NL queries run in CI on every merge
- Alerting: latency p95 >3s, error rate >1%, budget cap exceeded

---

## License

Graduation Project — ITI (Information Technology Institute)
