# SmartStock AI — Spec vs. Implementation Comparison Report

| | |
|---|---|
| **Spec Document** | `SmartStock_AI_Report.pdf` (31 pages, June 2025) |
| **Project** | SmartStock AI monorepo |
| **Audit Date** | 29 June 2026 |
| **Auditor** | Agent investigation via code-review-graph + full source exploration |

---

## 1. Executive Summary

The project delivers **~85-90% of the spec requirements** and adds **~15 significant features** not mentioned in the spec. The one structural gap is the **multi-agent pipeline**: the spec describes a chained Forecasting → Decision → Purchasing workflow, but the Decision Agent is **dead code** (class exists, zero production callers) and the three agents operate independently with no orchestrator.

---

## 2. Spec Items — Implementation Status

### 2.1 Section A: Use Case & Product Definition

| Requirement | Status | Evidence |
|------------|--------|----------|
| Problem statement (overstocking/stockouts) | ✅ | `readme.md` — exact match |
| Solution: proactive demand planning | ✅ | README + architecture |
| Target users: warehouse managers, procurement | ✅ | RBAC roles Viewer/Manager/Admin |
| KPIs: stockout -30%, PO automation 60%, cost -15% | ⚠️ No tracking dashboards | Metrics code exists but no UI for these specific KPIs |

### 2.2 Section A.6: 4-Week MVP Roadmap

| Week | Requirement | Status | Details |
|------|-------------|--------|---------|
| W1 | Inventory CRUD, dashboard, low-stock alerts, PostgreSQL, auth | ✅ | Complete in `apps/inventory/`, `apps/authentication/` |
| W2 | Prophet forecast, sales ingestion, reorder thresholds, charts | ✅ | `apps/forecasting/` + Recharts |
| W3 | GPT-4o NL analytics, function calling, few-shot, .env keys | ✅ | `ai/llm/chain.py` with `bind_tools(tool_choice="required")` |
| W4 | Purchasing agent, PO drafting, email, approval, error handling | ✅ | `ai/agents/purchasing_agent.py` + tasks |

### 2.3 Section B: LLM & Prompt Engineering

| Requirement | Status | Details |
|------------|--------|---------|
| B.1 System prompt template | ✅ | `ai/llm/prompts.py` — warehouse analytics assistant |
| B.2 Structured output via function calling | ✅ | `NLQueryToolSchema` + `tool_choice="required"` |
| B.3 NL → structured examples | ✅ | 3 spec examples + more in prompts.py |
| B.4 Few-shot prompting strategy | ✅ | 15 examples covering all 9 action types |

### 2.4 Section C: RAG Foundation

| Requirement | Status | Details |
|------------|--------|---------|
| C.1 pgvector + PostgreSQL | ✅ | `docker-entrypoint-initdb.d/01-init-vector.sql` |
| C.2 512-token chunks, 50 overlap, metadata | ✅ | `ai/rag/ingestion.py` |
| C.3 Hybrid search + Cohere reranking | ✅ | `ai/rag/retrieval.py` |
| C.4 Source citation, hallucination prevention | ✅ | `ai/rag/citation.py` |

### 2.5 Section D: Multi-Agent Pipeline

| Requirement | Status | Details |
|------------|--------|---------|
| Agent 1 — Forecasting Agent | ⚠️ Partial | LangChain ReAct class exists but **production Celery task bypasses it** (calls `ProphetEngine.predict()` directly) |
| Agent 2 — Decision Agent | ❌ **Dead code** | Class exists at `ai/agents/decision_agent.py` but **zero production callers** — no Celery task, view, or schedule invokes it |
| Agent 3 — Purchasing Agent | ✅ Full | HITL approval gate, email via Celery, supplier confirmation polling with exponential backoff |
| Agent chaining (F → D → P) | ❌ **Missing** | No orchestrator, supervisor, or pipeline connects agents |
| Error handling: email retry | ✅ | `PurchasingAgent`: 3 retries (30s/2min/10min) |
| Error handling: supplier timeout | ✅ | 48-hour timeout → "Pending — Unresponsive" |
| Error handling: Prophet fallback | ⚠️ Partial | Moving average fallback exists but not wired to Celery task |
| HITL checkpoint | ✅ | Approval card with SKU, quantity, cost, reasoning trace |

### 2.6 Section E: Multimodal

| Requirement | Status | Details |
|------------|--------|---------|
| E.1 Vision/OCR invoice scanning | ✅ | `ai/multimodal/vision.py` + confirmation card |
| E.2 Speech-to-Text Whisper | ✅ | `TranscribeView` + `VoiceButton` frontend component |

### 2.7 Section F: Safety & Security

| Requirement | Status | Details |
|------------|--------|---------|
| F.1 HITL safety | ✅ | Purchasing Agent approval gate |
| F.2 API key management via .env | ✅ | `python-decouple` + `.env.example` |
| F.3 JWT authentication | ✅ | 15min access / 3d refresh, HttpOnly cookie |
| F.4 RBAC (Viewer/Manager/Admin) | ✅ | `HasRole` permission + frontend role guards |
| F.5 Prompt injection defense | ✅ | Multi-layer: normalization, base64 detection, 8 pattern categories, risk scoring |
| F.6 Input validation | ✅ | DRF serializers + `core/validators.py` |
| F.7 Rate limiting | ✅ | 100 req/min/user, AI-specific throttles |
| F.8 PII protection (DB encryption) | ❌ **Missing** | Spec mentions DB encryption — only audit logging exists |
| F.9 Audit logging | ✅ | `apps/audit/`: 12 event types, signals + middleware |

### 2.8 Section G: Observability & Evaluation

| Requirement | Status | Details |
|------------|--------|---------|
| G.1 Langfuse observability | ✅ | `ai/observability/langfuse.py` — callback handler |
| G.2 Evaluation metrics | ✅ | Precision@5, faithfulness, agent success rate in `ai/evaluation/metrics.py` |
| G.3 Golden dataset (30 NL queries) | ✅ | `tests/golden_dataset/nl_queries.jsonl` — 30 entries, 5 categories |
| G.4 Runtime monitoring & alerting | ✅ | P95 >3s, error >1%, token budget cap, success rate <80% |

### 2.9 Section H: Engineering & Delivery

| Requirement | Status | Details |
|------------|--------|---------|
| H.1-H.2 Tech stack | ✅ | React 19, Django 5, DRF, PostgreSQL 16, Redis, Prophet, LangChain |
| H.3 Backend layer | ✅ | DRF with service/repository pattern |
| H.4 Database layer | ✅ | PostgreSQL + Redis |
| H.5 AI layer | ✅ | Prophet + LangChain + GPT-4o |
| H.6 Containerization | ✅ | Docker Compose with 9 services |
| H.7 Deployment | ✅ | Railway (backend) + Vercel (frontend) |
| H.8 CI/CD | ✅ | GitHub Actions: 5 job groups, 80% coverage gate |
| H.9 Testing strategy | ⚠️ No E2E | Unit + integration + golden dataset tests exist; **no end-to-end tests** per spec |
| H.10 Documentation | ⚠️ Partial | README + OpenAPI/Swagger exist; **no architecture diagrams** per spec |
| H.11 Risk mitigation | ✅ | Redis caching, health monitoring, token monitoring, data validation |

---

## 3. Features Added Beyond the Spec

| Feature | Location | What It Does |
|---------|----------|-------------|
| **Multi-LLM Provider Support** | `ai/llm/provider_config.py` | 4 providers (OpenAI, Groq, Gemini, xAI) with embedding fallback chain |
| **Full Monitoring Stack** | `monitoring/` + `apps/monitoring/` | Prometheus (30-day TSDB), Grafana (9-panel dashboard), Alertmanager (email routing) |
| **Notification System** | `apps/notifications/` | In-app notifications: mark_read, dismiss, mark_all_read, unread count, polling |
| **Health Check Endpoints** | `apps/health/views.py` | `live/` (always 200), `ready/` (DB + Redis), `full/` (all subsystems) |
| **Comprehensive Seed Data** | `core/management/commands/seed_data.py` | ~16K rows at scale=1, seasonal sales model, FK validation, production guard |
| **Storybook Visual Testing** | `smartstock-frontend/.storybook/` | 24 stories, Playwright visual regression, a11y addon |
| **Database Fingerprinting** | `core/management/commands/db_fingerprint.py` | SHA-256 hash of all table row counts for CI |
| **Celery Beat Scheduler** | `config/base.py:387-438` | 8 scheduled tasks (daily forecasts, supplier checks, audit purge, evaluations) |
| **Supplier Management** | `apps/purchasing/` + frontend | Full CRUD with repository pattern |
| **RAG Document Management** | `apps/ingestion/` + frontend | Upload PDFs, view chunks, query via hybrid search |
| **Invoice Scan Lifecycle** | `apps/ingestion/` + frontend | Upload → Vision OCR → confirmation card → accept/reject → audit log |
| **Monitoring Django App** | `apps/monitoring/` | AlertRule, AlertEvent, DashboardBanner, TokenUsageLog, AgentRunLog models |
| **Graceful Degradation** | Multiple | Forecast → moving average fallback, Chat → keyword fallback, LLM → upstream fallback |

---

## 4. Gaps Summary

### Critical (blocks spec promise)

| # | Gap | Spec Reference | Current State |
|---|-----|---------------|---------------|
| 1 | **No multi-agent pipeline** | Section D | Agents are independent. No Forecast → Decide → Purchase chaining. Decision Agent is dead code. |
| 2 | **Decision Agent not in production** | Section D.2 | Class exists but never called. No Celery task, view, or schedule. |

### Moderate (reduces spec fidelity)

| # | Gap | Spec Reference | Current State |
|---|-----|---------------|---------------|
| 3 | **Forecasting Agent not using LangChain in production** | Section D.1 | Celery task calls `ProphetEngine` directly, bypasses the ReAct agent |
| 4 | **No KPI tracking dashboards** | Section A.4 | Stockout rate, PO automation rate, cost reduction targets have no UI |
| 5 | **No E2E tests** | Section H.9 | 4-step business workflow untested at system level |
| 6 | **No architecture diagrams** | Section H.10 | No system/DB/workflow diagrams |

### Minor

| # | Gap | Spec Reference |
|---|-----|---------------|
| 7 | DB-level encryption for PII not implemented | F.8 |
| 8 | Golden dataset not explicitly gated in CI | G.3 |

---

## 5. Architecture Deviations

| Spec Expectation | Reality |
|-----------------|---------|
| All 3 agents are LangChain ReAct | Only Forecasting & Decision are ReAct; Purchasing is procedural Python |
| Clean Architecture: Views → Services → Repositories → DB | Cross-app import: `ingestion/views.py` imports `inventory/views.py` (NL query handlers in wrong layer) |
| `ForecastingService` uses `ForecastingAgent` | Celery task bypasses agent, calls `ProphetEngine` directly |

---

## 6. Project Stats

| Metric | Value |
|--------|-------|
| Django apps | 9 (`authentication`, `inventory`, `forecasting`, `purchasing`, `ingestion`, `audit`, `notifications`, `monitoring`, `health`) |
| Domain models | 23 across 7 apps |
| API endpoints | 35+ across 12 URL prefixes |
| Repository classes | 14 |
| Service classes | 12 |
| Celery tasks | 10+ (8 on schedule) |
| AI providers | 4 (OpenAI, Groq, Gemini, xAI) |
| Frontend features | 12 vertical slices |
| Storybook stories | 24 |
| Test files | 51 |
| Golden dataset entries | 30 |
| Seed data rows | ~16,435 (scale=1), ~164K (scale=10) |
| Docker services | 9 (6 core + 3 monitoring) |
| CI job groups | 5 (backend-check, lint, test — frontend-lint, build) |

---

## 7. Recommended Next Steps

1. **Wire Decision Agent into production** — add Celery task `run_decision_agent` and schedule it after forecasts
2. **Create agent orchestrator** — simple supervisor task calling Forecast → Decide → Purchase sequentially
3. **Add KPI dashboard widgets** — track stockout reduction, PO automation rate, carrying cost via `apps/monitoring/`
4. **Add architecture diagrams** — system context, container, and component diagrams in `docs/`
5. **Wire Prophet fallback** — connect moving-average fallback to Celery forecasting task
6. **Gate golden dataset in CI** — explicit step to run `tests/golden_dataset/` in CI workflow
7. **Add E2E test** — one Playwright or pytest test for the full forecast→decide→purchase flow
