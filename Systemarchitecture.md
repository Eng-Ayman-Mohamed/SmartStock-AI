# SystemArchitecture.md

# SmartStock AI — System Architecture Reference

> **Project:** SmartStock AI — AI-powered Inventory Management Platform
> **Team:** React-ive ITIIANS
> **Stack:** React + TypeScript + Tailwind · Django REST + Python · PostgreSQL + Redis + pgvector · Docker + GitHub Actions
> **Last Updated:** June 2025

---

## Table of Contents

1. [Architectural Philosophy](#1-architectural-philosophy)
2. [Clean Architecture Layers](#2-clean-architecture-layers)
3. [SOLID Principles Applied](#3-solid-principles-applied)
4. [System Communication Flow](#4-system-communication-flow)
5. [Backend Folder Structure](#5-backend-folder-structure)
6. [Frontend Folder Structure](#6-frontend-folder-structure)
7. [Design Patterns](#7-design-patterns)
8. [Key Architectural Decisions](#8-key-architectural-decisions)
9. [Security Model](#9-security-model)
10. [The Golden Rule](#10-the-golden-rule)

---

## 1. Architectural Philosophy

SmartStock AI follows **Clean Architecture** (also called Layered Architecture), meaning the codebase is divided into concentric layers where **outer layers depend on inner layers — never the other way around**.

The goal is to produce a system that is:

- **Testable** — business logic can be unit-tested without a database or HTTP server.
- **Maintainable** — changing one feature does not break another.
- **Scalable** — new features are added by extending, not modifying, existing code.
- **Swappable** — the database, LLM provider, or email service can be replaced by changing one file.

The architecture is **feature-based**, not layer-based. This means all code related to `forecasting` lives in one folder, not scattered across a `models/` folder, a `views/` folder, and a `services/` folder. A new developer can own a feature without understanding the entire codebase.

---

## 2. Clean Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                     │
│   React UI · Django REST Views · Serializers        │
│   Responsibility: Accept input, return output only  │
├─────────────────────────────────────────────────────┤
│              APPLICATION LAYER                      │
│   Services · Use Cases · LangChain Orchestration    │
│   Responsibility: Coordinate business operations    │
├─────────────────────────────────────────────────────┤
│               DOMAIN LAYER                         │
│   Business Logic · Entities · Rules · Repositories  │
│   Responsibility: Core business rules, pure Python  │
├─────────────────────────────────────────────────────┤
│            INFRASTRUCTURE LAYER                     │
│   PostgreSQL · pgvector · Redis · Email · S3        │
│   Responsibility: All I/O — DB, cache, external APIs│
└─────────────────────────────────────────────────────┘
```

### Layer Rules (NEVER violate these)

| Rule                       | Description                                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------------- |
| Views call Services        | Views validate input via serializers, then call a service. They never query the DB directly.            |
| Services call Repositories | Services contain business logic and call repositories for data access.                                  |
| Repositories call the DB   | Repositories are the only layer that touches Django ORM or raw SQL.                                     |
| Domain has no imports      | The domain layer imports nothing from infrastructure or presentation.                                   |
| AI layer is isolated       | LLM, RAG, and Agents are siblings in the `ai/` directory. They do not live inside business app folders. |

---

## 3. SOLID Principles Applied

### S — Single Responsibility

Each Django app owns **one domain only**. The `inventory` app manages products and stock levels. The `forecasting` app manages Prophet models and predictions. No app imports another app's models directly — communication happens via service interfaces.

### O — Open/Closed

New agent tools are added via the `BaseTool` plugin interface. Adding a tool requires **zero changes** to the agent orchestration code — only a new file in `ai/agents/tools/`. The system is open for extension, closed for modification.

### L — Liskov Substitution

All repositories extend `BaseRepository`. The service layer depends on `BaseRepository`, not on `InventoryRepository` specifically. This means the concrete ORM implementation can be swapped (e.g., from PostgreSQL to another DB) without breaking any service.

### I — Interface Segregation

RAG, LLM, and Agent interfaces are **separate**. The RAG pipeline does not depend on the Agent interface. A component that only needs retrieval is not forced to know about agent tools.

### D — Dependency Inversion

Services depend on **abstract repository interfaces**, not concrete ORM models. The dependency flows inward — infrastructure depends on domain interfaces, not the reverse.

---

## 4. System Communication Flow

### Standard Request Flow

```
React UI
  └─► Axios (Bearer token) ──► Django REST View
                                    └─► Serializer (validate input)
                                          └─► Service (business logic)
                                                └─► Repository
                                                      └─► PostgreSQL / Redis
                                                ◄─── Response JSON
```

### AI / NL Query Flow

```
React Chat UI
  └─► POST /api/nlquery/
        └─► Django View ──► LangChain Chain
                                └─► System Prompt + Few-shot examples
                                      └─► GPT-4o (function calling)
                                            └─► Structured JSON action
                                                  └─► DB Query via Repository
                                                        └─► Response to frontend
```

### RAG Pipeline Flow

```
User NL Query
  └─► Embed query (text-embedding-3-small)
        └─► Hybrid search (pgvector dense + PostgreSQL FTS sparse)
              └─► Cohere cross-encoder reranking
                    └─► Top-3 context chunks injected into prompt
                          └─► GPT-4o generates response with [Source: X, Page: Y] citations
```

### Agent Pipeline Flow

```
Scheduled Daily Trigger
  └─► Forecasting Agent
        ├─ db_read_tool       → reads historical sales from PostgreSQL
        ├─ prophet_run_tool   → executes Prophet model per SKU
        └─ db_write_tool      → persists predictions to forecasts table
              └─► Decision Agent
                    ├─ db_read_tool         → reads current stock levels
                    ├─ forecast_read_tool   → reads predictions
                    └─ po_status_check_tool → checks for open duplicate POs
                          └─► [ReAct loop: Plan → Execute → Verify]
                                └─► Purchasing Agent (on stockout flag)
                                      ├─ po_draft_tool            → generates PO
                                      ├─ [HITL APPROVAL GATE]     → manager approves
                                      ├─ email_send_tool          → dispatches to supplier
                                      ├─ confirmation_listener_tool → polls for reply
                                      └─ db_update_tool           → updates inventory status
```

### Multimodal Flows

```
# Vision / OCR
Image Upload (React)
  └─► Base64 encode ──► POST /api/invoice-scan/
                              └─► GPT-4o Vision API
                                    └─► Structured JSON (product, SKU, qty, price)
                                          └─► Confirmation Card presented to user
                                                └─► [User confirms / rejects]
                                                      └─► DB update + Audit log entry

# Speech-to-Text
Microphone input (browser)
  └─► OpenAI Whisper API
        └─► Transcribed text
              └─► NL Query Pipeline (same as above)
```

---

## 5. Backend Folder Structure

```
smartstock-backend/
├── config/                          # Django project configuration
│   ├── settings/
│   │   ├── base.py                  # Shared settings (installed apps, middleware)
│   │   ├── development.py           # Debug=True, local DB
│   │   └── production.py           # Debug=False, env vars, HTTPS
│   ├── urls.py                      # Root URL dispatcher
│   └── wsgi.py
│
├── apps/                            # Feature-based Django applications
│   ├── authentication/              # JWT, RBAC, user management
│   │   ├── models.py                # CustomUser model with role field
│   │   ├── views.py                 # login, register, refresh endpoints
│   │   ├── serializers.py
│   │   ├── permissions.py           # IsViewer, IsManager, IsAdmin classes
│   │   └── urls.py
│   │
│   ├── inventory/                   # Products, SKUs, stock levels, sales records
│   │   ├── models.py                # Product, SKU, StockLevel, SalesRecord models
│   │   ├── views.py                 # Thin views — calls services only
│   │   ├── serializers.py
│   │   ├── services.py              # Business logic (get_low_stock, update_stock)
│   │   ├── repositories.py          # DB abstraction (extends BaseRepository)
│   │   └── urls.py
│   │
│   ├── forecasting/                 # Prophet model, reorder logic
│   │   ├── models.py                # ForecastResult model
│   │   ├── views.py
│   │   ├── services.py              # Orchestrates prophet_engine + reorder logic
│   │   ├── repositories.py
│   │   ├── prophet_engine.py        # Isolated Prophet ML logic (no Django imports)
│   │   └── urls.py
│   │
│   ├── purchasing/                  # Purchase orders, supplier management
│   │   ├── models.py                # PurchaseOrder, Supplier models
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services.py              # approve_po(), draft_po(), send_po()
│   │   ├── repositories.py
│   │   └── urls.py
│   │
│   └── audit/                       # Audit log — all critical events
│       ├── models.py                # AuditLog model (event, user, timestamp, data)
│       ├── middleware.py            # Auto-log on every mutating request
│       └── serializers.py
│
├── ai/                              # Isolated AI layer — no business logic here
│   ├── llm/
│   │   ├── chain.py                 # LangChain chain: prompt | model | parser
│   │   ├── prompts.py               # System prompt templates (inventory scope)
│   │   ├── output_parser.py         # StructuredOutputParser for JSON actions
│   │   └── few_shots.py             # All 5 few-shot NL→query examples
│   │
│   ├── rag/
│   │   ├── ingestion.py             # Chunking (512t/50 overlap) + embedding
│   │   ├── retrieval.py             # Hybrid search (dense + FTS) + Cohere rerank
│   │   └── citation.py             # Source metadata injection into prompt
│   │
│   ├── agents/
│   │   ├── base_agent.py            # Abstract BaseTool interface (plugin pattern)
│   │   ├── forecasting_agent.py     # Scheduled daily forecasting agent
│   │   ├── decision_agent.py        # ReAct loop: reorder threshold + duplicate check
│   │   ├── purchasing_agent.py      # HITL PO drafting + email dispatch
│   │   └── tools/                   # One file per tool (plugin pattern)
│   │       ├── db_read.py
│   │       ├── db_write.py
│   │       ├── forecast_read.py
│   │       ├── po_draft.py
│   │       ├── email_send.py
│   │       ├── confirmation_listener.py
│   │       ├── po_status_check.py
│   │       └── db_update.py
│   │
│   └── multimodal/
│       ├── vision.py                # GPT-4o Vision invoice extraction
│       └── whisper.py               # OpenAI Whisper speech-to-text
│
├── core/                            # Shared abstractions (no app dependencies)
│   ├── base_repository.py           # Abstract BaseRepository (ABC)
│   ├── exceptions.py                # StockNotFoundException, DuplicatePOError, etc.
│   ├── pagination.py                # Shared DRF pagination class
│   └── validators.py                # Shared input validators
│
├── infrastructure/                  # External service wrappers
│   ├── cache.py                     # Redis abstraction (get, set, delete, TTL)
│   ├── email.py                     # Email service wrapper (SMTP / SendGrid)
│   └── storage.py                   # File/image storage (local dev / S3 prod)
│
├── tests/
│   ├── unit/                        # Pure business logic tests (no DB)
│   ├── integration/                 # API endpoint + DB tests
│   └── golden_dataset/              # 30 annotated NL queries for CI eval
│
├── .env.example                     # All required env var names (no values)
├── .gitignore                       # Blocks: .env, __pycache__, *.pyc, db.sqlite3
├── Dockerfile
├── requirements.txt
└── manage.py
```

### Backend Directory Roles

| Directory               | Role                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| `config/`               | Django project settings split by environment. Never put business logic here.                     |
| `apps/`                 | All feature domains. Each app is self-contained — models, views, services, repositories.         |
| `ai/`                   | Entire AI layer isolated. Swapping GPT-4o for Claude touches only `ai/llm/chain.py`.             |
| `core/`                 | Shared abstractions. Nothing in `core/` imports from `apps/` or `ai/`.                           |
| `infrastructure/`       | External service wrappers. The rest of the app never calls Redis directly — only via `cache.py`. |
| `tests/golden_dataset/` | 30 NL query test cases. Executed in CI on every merge to main.                                   |

---

## 6. Frontend Folder Structure

```
smartstock-frontend/
├── src/
│   ├── features/                    # One folder per feature — vertical slices
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useAuth.ts       # JWT token management, login, logout
│   │   │   ├── api.ts               # Auth API calls (login, refresh)
│   │   │   ├── store.ts             # Zustand auth slice (token in memory)
│   │   │   └── types.ts
│   │   │
│   │   ├── inventory/
│   │   │   ├── components/
│   │   │   │   ├── StockTable.tsx
│   │   │   │   ├── LowStockAlert.tsx
│   │   │   │   └── StockBadge.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useInventory.ts  # React Query: fetch, cache, refetch
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   │
│   │   ├── forecasting/
│   │   │   ├── components/
│   │   │   │   ├── ForecastChart.tsx   # Recharts AreaChart
│   │   │   │   └── ReorderAlert.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useForecasting.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── purchasing/
│   │   │   ├── components/
│   │   │   │   ├── POApprovalCard.tsx  # SKU, date, qty, cost, reasoning trace
│   │   │   │   └── POQueue.tsx
│   │   │   ├── hooks/
│   │   │   │   └── usePurchasing.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── ai-assistant/
│   │   │   ├── components/
│   │   │   │   ├── ChatPanel.tsx
│   │   │   │   ├── VoiceButton.tsx     # Whisper mic integration
│   │   │   │   └── CitationTag.tsx     # [Source: file, Page: X] display
│   │   │   ├── hooks/
│   │   │   │   └── useNLQuery.ts
│   │   │   └── api.ts
│   │   │
│   │   └── invoice-scan/
│   │       ├── components/
│   │       │   ├── InvoiceUpload.tsx
│   │       │   └── ConfirmationCard.tsx  # Editable fields + Confirm/Reject
│   │       └── api.ts
│   │
│   ├── shared/                      # Components/hooks used by 2+ features
│   │   ├── components/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Table.tsx
│   │   │   └── Skeleton.tsx
│   │   ├── hooks/
│   │   │   ├── useDebounce.ts
│   │   │   └── usePagination.ts
│   │   └── utils/
│   │       ├── formatters.ts        # Currency, date, SKU formatters
│   │       └── validators.ts
│   │
│   ├── lib/                         # Infrastructure wrappers (configured once)
│   │   ├── axios.ts                 # Axios instance with base URL + interceptors
│   │   ├── queryClient.ts           # React Query client config (stale time, retry)
│   │   └── router.tsx               # React Router with protected route wrapper
│   │
│   ├── store/                       # Zustand — global CLIENT state only
│   │   └── authStore.ts             # { user, token, setToken, clearToken }
│   │
│   ├── types/                       # Global TypeScript type definitions
│   │   └── api.d.ts                 # API response shapes, shared enums
│   │
│   └── main.tsx                     # App entry point
│
├── .env.example
├── .gitignore                       # Blocks: node_modules, .env, dist
├── Dockerfile
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

### Frontend Directory Roles

| Directory   | Role                                                                                                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `features/` | Each folder is a vertical slice (components + hooks + API + types). Changing forecasting UI touches only `features/forecasting/`.  |
| `shared/`   | Promoted only when a component is used by 2+ features. If only one feature uses it, it stays in that feature.                      |
| `lib/`      | All infrastructure config in one place. Changing the API base URL happens in `axios.ts` only — not in 20 different `api.ts` files. |
| `store/`    | Zustand only for global client state (auth token, current user). Server state lives in React Query — never duplicated in Zustand.  |

---

## 7. Design Patterns

### Pattern 1 — Repository Pattern (Backend)

**Layer:** Domain / Infrastructure
**Purpose:** Services never query the DB directly. All data access goes through a repository interface.

```python
# core/base_repository.py
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int): ...
    @abstractmethod
    def get_all(self): ...
    @abstractmethod
    def create(self, data: dict): ...
    @abstractmethod
    def update(self, id: int, data: dict): ...
    @abstractmethod
    def delete(self, id: int): ...

# apps/inventory/repositories.py
from core.base_repository import BaseRepository
from .models import Product

class InventoryRepository(BaseRepository):
    def get_by_id(self, id: int):
        return Product.objects.get(pk=id)

    def get_all(self):
        return Product.objects.all()

    def create(self, data: dict):
        return Product.objects.create(**data)
```

**Why it prevents technical debt:** If you later need to add caching, change the DB, or mock data in tests, you change only the repository — not 30 different view files.

---

### Pattern 2 — Service Layer Pattern (Backend)

**Layer:** Application
**Purpose:** Views are thin. All business logic lives in `services.py`. Views call services; services call repositories.

```python
# apps/inventory/views.py  ← THIN
class LowStockView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        result = InventoryService().get_low_stock_items()
        return Response(result, status=200)

# apps/inventory/services.py  ← FAT (business logic lives here)
class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()

    def get_low_stock_items(self):
        all_items = self.repo.get_all()
        return [
            item for item in all_items
            if item.quantity < item.reorder_point
        ]
```

---

### Pattern 3 — Plugin Pattern for Agent Tools (AI Layer)

**Layer:** AI / Agents
**Purpose:** Adding a new agent tool requires zero changes to orchestration code. Register a new class, it becomes available.

```python
# ai/agents/base_agent.py
from abc import ABC, abstractmethod

class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, input: dict) -> dict: ...

# ai/agents/tools/po_draft.py
from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService

class PODraftTool(BaseTool):
    name = "po_draft_tool"
    description = "Generates a formal Purchase Order for a given SKU and quantity."

    def run(self, input: dict) -> dict:
        return PurchasingService().draft_po(
            sku_id=input["sku_id"],
            quantity=input["quantity"]
        )
```

---

### Pattern 4 — Custom Hook Pattern (Frontend)

**Layer:** Frontend Application
**Purpose:** Components are pure presentational. All data fetching, caching, and error states live in custom hooks.

```typescript
// features/inventory/hooks/useInventory.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryApi } from '../api';

export function useInventory() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['inventory'],
    queryFn: inventoryApi.getAll,
    staleTime: 60_000,          // 1-min cache
    retry: 2,
  });
  return { inventory: data ?? [], isLoading, error };
}

// features/inventory/components/StockTable.tsx  ← no API logic
export function StockTable() {
  const { inventory, isLoading } = useInventory();
  if (isLoading) return <Skeleton />;
  return <Table data={inventory} />;
}
```

---

### Pattern 5 — Strategy Pattern for Error Handling (Backend)

**Layer:** Infrastructure / Presentation
**Purpose:** Business logic throws typed domain exceptions. A global handler maps them to HTTP status codes. Consistent error shape across all 30+ endpoints.

```python
# core/exceptions.py
class StockNotFoundException(Exception): pass
class InsufficientStockError(Exception): pass
class DuplicatePOError(Exception): pass
class ForecastingModelError(Exception): pass
class SupplierNotFoundException(Exception): pass

# config/exception_handler.py
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    STATUS_MAP = {
        StockNotFoundException:    404,
        InsufficientStockError:    409,
        DuplicatePOError:          409,
        ForecastingModelError:     500,
        SupplierNotFoundException: 404,
    }
    status_code = STATUS_MAP.get(type(exc), 500)
    return Response(
        {"error": str(exc), "type": type(exc).__name__},
        status=status_code
    )
```

---

### Pattern 6 — Observer Pattern for Audit Logging (Backend)

**Layer:** Infrastructure
**Purpose:** Critical events are logged automatically via Django signals. Service code emits a signal; the audit app listens. Zero audit code in business logic.

```python
# apps/purchasing/services.py
from django.dispatch import Signal

po_approved = Signal()

class PurchasingService:
    def approve_po(self, po_id: int, user):
        po = self.repo.approve(po_id)
        po_approved.send(sender=self, po=po, user=user)  # fire and forget
        return po

# apps/audit/signals.py
from django.dispatch import receiver
from apps.purchasing.services import po_approved
from .models import AuditLog

@receiver(po_approved)
def log_po_approval(sender, po, user, **kwargs):
    AuditLog.objects.create(
        event="PO_APPROVED",
        user=user,
        entity_id=po.id,
        data={"supplier": po.supplier.name, "amount": str(po.total_cost)}
    )
```

---

## 8. Key Architectural Decisions

| Decision Area         | Chosen                                      | Rejected                          | Rationale                                                                                                                                                                              |
| --------------------- | ------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API Style**         | REST (Django REST Framework)                | GraphQL, gRPC                     | REST maps cleanly to CRUD inventory ops. GraphQL adds resolver complexity unjustified by data graph. gRPC requires a separate gateway for browser clients.                             |
| **Client State**      | React Query (server) + Zustand (client)     | Redux Toolkit, Context API        | React Query owns all async server data with caching and stale-while-revalidate. Zustand handles only UI state (auth token, modal open). Redux adds 3× boilerplate for the same result. |
| **Database ORM**      | Django ORM behind Repository abstraction    | Raw SQL, SQLAlchemy               | Repository pattern makes ORM swappable without touching services. Raw SQL bypasses the abstraction. SQLAlchemy adds a second ORM to a Django project.                                  |
| **Vector Store**      | pgvector on existing PostgreSQL             | Pinecone, Chroma, Qdrant          | Eliminates a separate service. Hybrid search (vector + FTS) in one query. Clear migration path if scale later demands a dedicated vector DB.                                           |
| **LLM Orchestration** | LangChain (function calling + RAG + Agents) | Direct OpenAI SDK, LlamaIndex     | LangChain unifies LLM, RAG, and Agents under one interface. Direct SDK calls don't scale to multi-agent pipelines. LlamaIndex is optimised for document-heavy RAG — overkill here.     |
| **Background Tasks**  | Celery + Redis (beat scheduler)             | Django cron commands, APScheduler | Celery Beat enables retries, monitoring, and horizontal scaling. Cron has no retry logic. APScheduler is process-bound and breaks in multi-instance deployments.                       |
| **Authentication**    | JWT (access + refresh tokens) + RBAC        | Session auth, API keys only       | JWT is stateless — works across mobile, web, and future microservices. Session auth requires shared session store in multi-instance deployment.                                        |
| **AI Observability**  | Langfuse + Django logging                   | LangSmith, W&B                    | Langfuse is open-source, free to self-host, integrates with LangChain in 3 lines. LangSmith requires paid plan. W&B is optimised for model training, not LLM call tracing.             |

---

## 9. Security Model

### 9.1 Authentication Flow

```
1. POST /api/auth/login/  { email, password }
      └─► DRF validates against hashed password (bcrypt)
            └─► Issues: Access Token (15-min TTL) + Refresh Token (7-day TTL)
                  ├─ Access Token → returned in response body
                  └─ Refresh Token → stored as HttpOnly cookie (JS cannot read it)

2. React stores access token in Zustand memory (NOT localStorage)
      └─► Axios interceptor attaches as: Authorization: Bearer <token>

3. Every protected endpoint runs:
      └─► JWT decode → verify signature → check expiry
            └─► RBAC permission class checks user.role
                  ├─ Viewer:  GET only
                  ├─ Manager: GET + approve POs + access forecasts
                  └─ Admin:   Full access + user management

4. On access token expiry:
      └─► Axios interceptor silently calls POST /api/auth/refresh/
            └─► Uses HttpOnly refresh cookie (automatic, no JS involvement)
                  └─► New access token issued — user never sees re-login prompt
```

### 9.2 AI-Specific Security

| Threat                      | Mitigation                                                                                                                        |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Prompt injection            | System prompt in server-side role boundary. User input cannot override instructions. Input sanitized before LangChain invocation. |
| Hallucination corrupting DB | LLM output validated against JSON schema before any DB write. Vision malformed JSON → reject + prompt re-upload.                  |
| Autonomous spending         | HITL approval gate on all POs. No fully autonomous procurement — manager must confirm every order.                                |
| Tool misuse                 | Agent tools check RBAC before execution. Non-manager users cannot trigger po_draft_tool.                                          |

### 9.3 Infrastructure Security

| Area          | Implementation                                                                                                          |
| ------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Secrets       | All API keys in `.env`. Never hardcoded. `.gitignore` blocks `.env`. `.env.example` lists all key names without values. |
| HTTPS         | Enforced in production via Render TLS. HTTP requests redirected to HTTPS.                                               |
| CORS          | `django-cors-headers` restricts to known frontend origin only.                                                          |
| Rate Limiting | DRF throttle: 100 req/min/user. IP-based limits. Daily LLM token quotas.                                                |
| Containers    | Docker containers run as non-root user. No secrets in Dockerfile.                                                       |
| Database      | PostgreSQL connection via SSL in production. Parameterised queries only — no raw string formatting.                     |

### 9.4 Data Security

| Area           | Implementation                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------- |
| PII fields     | Supplier contacts, emails, and financial data access-controlled by role.                                |
| Audit logging  | Every PO approval, AI action, login attempt, and config change logged with timestamp and user identity. |
| Data retention | PII data retention policy: 90 days. Automated cleanup job via Celery Beat.                              |
| Backups        | Automated daily PostgreSQL backups. Point-in-time recovery enabled on production Render instance.       |

---

## 10. The Golden Rule

> **Views call Services. Services call Repositories. Repositories call the DB. Nothing skips a layer.**

If a view is directly calling `Product.objects.filter()`, that is an architecture violation.
If a repository contains business logic (e.g., reorder threshold calculations), that is an architecture violation.
If the `ai/` directory imports from `apps/inventory/models.py` directly instead of going through a service, that is an architecture violation.

Every violation creates technical debt that compounds. A 5-minute shortcut today becomes a 5-hour debugging session in week 3.

When in doubt: **add a service method**.

---

_This document is a living reference. Update it when architectural decisions change. Do not let the code diverge from this document — they should always match._
