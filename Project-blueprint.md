# PROJECT_BLUEPRINT.md

# SmartStock AI — Comprehensive Implementation Blueprint

> **Single Source of Truth** — This document synthesizes every architectural, technical, and design decision made during the project planning phase.
> If the code diverges from this document, this document wins.
>
> **Team:** React-ive ITIIANS
> **Members:** Ayman Mohamed · Omar Wael · Mostafa Abdel Aziz · Mostafa Abdel Qawy · Mawada Alexander
> **Target Industry:** Logistics, E-commerce, and Retail Supply Chain
> **Version:** 1.1 — June 2026

---

## Table of Contents

1. [Project Vision & Scope](#1-project-vision--scope)
2. [Technical Stack](#2-technical-stack)
3. [System Architecture](#3-system-architecture)
4. [Data Modeling (ERD)](#4-data-modeling-erd)
5. [Frontend Component Architecture](#5-frontend-component-architecture)
6. [API / Service Layer](#6-api--service-layer)
7. [AI Layer Specification](#7-ai-layer-specification)
8. [Implementation Roadmap & Tasks](#8-implementation-roadmap--tasks)

---

## 1. Project Vision & Scope

### 1.1 What Is SmartStock AI?

SmartStock AI is an integrated, web-based warehouse management platform that couples real-time operational data capture with AI-driven demand forecasting. It serves medium-to-large e-commerce and logistics businesses that suffer financial losses from two antithetical inventory failure modes:

- **Overstocking** — ties up working capital in idle goods, increasing holding costs by 15–25% annually.
- **Stockouts** — generate lost sales (4–8% revenue loss per year) and erode customer satisfaction.

Incumbent systems are reactive — they rely on manual, periodic audits that fail to incorporate seasonal demand curves, macroeconomic signals, or supplier lead-time variability. SmartStock AI makes inventory management **proactive and autonomous**.

### 1.2 Core Value Proposition

> _"Tell the user exactly what they need before they run out."_

**Proactive Demand Planning** — the system predicts future stockouts and autonomously initiates the procurement workflow, with a human-in-the-loop approval gate before any order is dispatched.

### 1.3 Target Users

| User                     | Role      | Key Actions                                                |
| ------------------------ | --------- | ---------------------------------------------------------- |
| **Warehouse Manager**    | Primary   | View dashboard, approve POs, run NL queries, scan invoices |
| **Procurement Team**     | Primary   | Monitor reorder alerts, manage suppliers, review forecasts |
| **Business Owner**       | Secondary | Review analytics, monitor costs, access reports            |
| **System Administrator** | Internal  | Manage users, configure roles, access audit logs           |

### 1.4 Success KPIs

| KPI                               | Target                                  | Measurement                                                     |
| --------------------------------- | --------------------------------------- | --------------------------------------------------------------- |
| Stockout Reduction Rate           | −30% within 3 months                    | `(before_stockouts − after_stockouts) / before_stockouts × 100` |
| PO Automation Rate                | ≥60% auto-approved without manual edits | `approved_without_edit / total_po_drafts × 100`                 |
| Inventory Carrying Cost Reduction | −15% within 6 months                    | Comparison of holding costs before/after deployment             |

### 1.5 The AI Trinity Strategy

| Component              | Technology                 | Role                                                                                            |
| ---------------------- | -------------------------- | ----------------------------------------------------------------------------------------------- |
| **LLM (Intelligence)** | GPT-4o via LangChain       | Natural Language Data Analyst — translates NL commands into structured DB queries               |
| **RAG (Knowledge)**    | pgvector + Cohere reranker | Grounds AI responses in internal business data — product catalogues, supplier records, policies |
| **Agents (Action)**    | LangChain Agents (ReAct)   | Purchasing Agent — autonomously drafts and dispatches POs on predicted stockouts                |

### 1.6 Scope Boundaries

**In Scope (MVP):**

- Inventory CRUD (products, SKUs, suppliers, stock levels)
- Prophet-based demand forecasting per SKU
- NL query interface with GPT-4o function calling
- RAG pipeline over internal business documents
- Three-agent purchasing workflow with HITL approval
- Invoice OCR via GPT-4o Vision
- Voice commands via OpenAI Whisper
- JWT auth + RBAC (Viewer / Manager / Admin)
- Langfuse observability + golden evaluation dataset

**Out of Scope (Post-MVP):**

- Mobile native app
- Multi-warehouse / multi-tenant support
- ERP/WMS integration APIs
- Barcode/RFID scanning hardware integration

---

## 2. Technical Stack

### 2.1 Definitive Technology Stack

| Layer                  | Technology                                   | Version | Purpose                                      |
| ---------------------- | -------------------------------------------- | ------- | -------------------------------------------- |
| **Frontend Framework** | React                                        | 19.x    | Component-based SPA                          |
| **Frontend Language**  | TypeScript                                   | 5.x     | Type safety across all components            |
| **Styling**            | Tailwind CSS                                 | 4.x     | Utility-first responsive design              |
| **Build Tool**         | Vite                                         | 5.x     | Fast dev server + production build           |
| **Data Visualisation** | Recharts                                     | 2.x     | Inventory + forecast charts                  |
| **Server State**       | TanStack React Query                         | 5.x     | API caching, refetch, stale-while-revalidate |
| **Client State**       | Zustand                                      | 5.x     | Auth token, global UI state                  |
| **HTTP Client**        | Axios                                        | 1.x     | API calls with interceptors for JWT          |
| **Routing**            | React Router                                 | 6.x     | SPA navigation + protected routes            |
| **Backend Framework**  | Django                                       | 5.x     | Feature-based REST API                       |
| **API Layer**          | Django REST Framework                        | 3.15.x  | Serializers, ViewSets, permissions           |
| **Authentication**     | djangorestframework-simplejwt                | 5.x     | JWT access + refresh tokens                  |
| **API Docs**           | drf-spectacular                              | 0.27.x  | OpenAPI 3.0 / Swagger UI                     |
| **Task Queue**         | Celery                                       | 5.x     | Background tasks + scheduled jobs            |
| **Primary Database**   | PostgreSQL                                   | 16.x    | All structured operational data              |
| **Vector Extension**   | pgvector                                     | 0.7.x   | Embedding storage + similarity search        |
| **Cache / Queue**      | Redis                                        | 7.x     | Caching, Celery broker, session store        |
| **LLM**                | GPT-4o (OpenAI)                              | latest  | NL queries + Vision + orchestration          |
| **Embeddings**         | text-embedding-3-small                       | latest  | 1536-dim vectors for RAG                     |
| **Speech-to-Text**     | OpenAI Whisper                               | v2      | Voice command transcription                  |
| **LLM Orchestration**  | LangChain                                    | 0.2.x   | Chains, agents, RAG, output parsing          |
| **Reranking**          | Cohere Rerank                                | v3      | Cross-encoder RAG result refinement          |
| **Forecasting**        | Prophet (Meta)                               | 1.1.x   | Time-series demand forecasting               |
| **ML Utilities**       | Scikit-learn                                 | 1.5.x   | Preprocessing, MAE/MAPE evaluation           |
| **Data Processing**    | Pandas                                       | 2.x     | Sales data ingestion + cleaning              |
| **Observability**      | Langfuse                                     | 2.x     | LLM trace, token cost, agent monitoring      |
| **Containerisation**   | Docker + Docker Compose                      | 25.x    | Environment consistency                      |
| **CI/CD**              | GitHub Actions                               | —       | Lint + test + deploy on push                 |
| **Backend Hosting**    | Railway                                      | —       | Django + Celery deployment                   |
| **Frontend Hosting**   | Vercel                                       | —       | React SPA deployment                         |
| **Secret Management**  | python-dotenv (dev) / Railway Env Vars (prod) | —       | Credential isolation                         |

### 2.2 Architecture Pattern

- **Backend:** Feature-based Django apps following Clean Architecture (Presentation → Application → Domain → Infrastructure)
- **Frontend:** Feature-based vertical slices (`features/inventory/`, `features/forecasting/`, etc.)
- **Monorepo structure:** `smartstock-backend/` and `smartstock-frontend/` as sibling directories in one Git repository

---

## 3. System Architecture

### 3.1 Clean Architecture Layers

```
┌────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                          │
│  React UI · DRF Views · Serializers · API Endpoints           │
│  Rule: Accept input, validate, delegate to service. No logic. │
├────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                           │
│  Django Services · LangChain Orchestration · Use Cases        │
│  Rule: Coordinate operations. Call repositories + AI layer.   │
├────────────────────────────────────────────────────────────────┤
│                      DOMAIN LAYER                              │
│  Business Logic · Entities · Reorder Rules · Validation       │
│  Rule: Pure Python. Zero infrastructure imports.              │
├────────────────────────────────────────────────────────────────┤
│                  INFRASTRUCTURE LAYER                          │
│  PostgreSQL · pgvector · Redis · Email · S3 · OpenAI APIs     │
│  Rule: All I/O lives here. Wrapped behind abstractions.       │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Full System Communication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER (React)                           │
│  Zustand (auth) · React Query (server state) · Axios (HTTP)     │
└────────────────────┬─────────────────────────────────────────────┘
                     │  HTTPS · Bearer JWT
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                   DJANGO REST API (Railway)                       │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │
│  │    auth/    │  │ inventory/  │  │     forecasting/        │  │
│  │ purchasing/ │  │   audit/    │  │        ai/              │  │
│  └─────────────┘  └─────────────┘  └────────────────────────┘  │
│                                                                  │
│  Views → Services → Repositories → PostgreSQL                   │
│                    ↓                                             │
│            ┌───────────────┐                                     │
│            │  AI LAYER     │                                     │
│            │  LangChain    │──► GPT-4o · Whisper · Vision       │
│            │  RAG Pipeline │──► pgvector · Cohere Rerank        │
│            │  3 Agents     │──► Celery Beat (scheduler)         │
│            └───────────────┘                                     │
│                    ↓              ↓                              │
│             PostgreSQL         Redis                             │
│             + pgvector         (cache + Celery broker)          │
└──────────────────────────────────────────────────────────────────┘
                     │
                     ▼  Email (SMTP)
              Supplier Inbox
```

### 3.3 Request Lifecycle (Standard)

```
1. React component calls custom hook (e.g., useInventory())
2. Hook triggers React Query → Axios GET /api/inventory/
3. Axios interceptor attaches Authorization: Bearer <access_token>
4. Django View receives request → validates JWT → checks RBAC permission
5. View calls InventoryService.get_all()
6. Service calls InventoryRepository.get_all()
7. Repository executes Django ORM query → PostgreSQL
8. Response flows back: Repository → Service → View → Serializer → JSON
9. React Query caches response (staleTime: 60s)
10. Component re-renders with data
```

### 3.4 Request Lifecycle (NL Query)

```
1. User types "Show slow-moving items from last month" (or uses voice)
2. If voice: browser mic → Whisper API → transcribed text
3. React POST /api/nlquery/ { "query": "..." }
4. Django View → NLQueryService.process(query)
5. Service → LangChain chain:
   a. System prompt (scope boundary + few-shot examples)
   b. GPT-4o with function calling → structured JSON action
   c. OutputParser validates JSON against schema
6. JSON action dispatched to correct repository method
7. DB result returned → GPT-4o formats human-readable response
8. Response + action returned to frontend
```

### 3.5 Agent Pipeline Lifecycle

```
[DAILY CELERY BEAT TRIGGER]
│
├─► Forecasting Agent
│     ├─ db_read_tool          → SELECT sales WHERE date > NOW()-30d
│     ├─ prophet_run_tool      → fit Prophet per SKU, generate 30d forecast
│     └─ db_write_tool         → INSERT INTO forecasts (sku_id, date, predicted_qty)
│
├─► Decision Agent (reads forecast results)
│     ├─ db_read_tool          → SELECT current stock_level per SKU
│     ├─ forecast_read_tool    → SELECT predicted demand for next lead_time days
│     ├─ [REORDER CHECK]       → reorder_point = (avg_daily_demand × lead_time) + safety_stock
│     ├─ po_status_check_tool  → check for existing open PO for this SKU (prevent duplicate)
│     └─ [FLAG for Purchasing Agent if stock < reorder_point AND no open PO]
│
└─► Purchasing Agent (on reorder flag)
      ├─ po_draft_tool              → generate PO document (SKU, qty, supplier, estimated cost)
      ├─ [HITL GATE]                → present approval card to manager in dashboard
      │     Card shows: SKU · predicted stockout date · qty · supplier · cost · reasoning trace
      │     Manager: Approve / Reject / Edit quantity
      ├─ [ON APPROVE] email_send_tool      → SMTP email to pre-approved supplier
      ├─ confirmation_listener_tool        → poll for supplier reply (48hr timeout)
      │     On no reply: flag as "Pending — Supplier Unresponsive" + notify manager
      └─ db_update_tool                    → UPDATE purchase_orders SET status='confirmed'
```

---

## 4. Data Modeling (ERD)

### 4.1 Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        enum role "viewer|manager|admin"
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CATEGORY {
        int id PK
        string name UK
        string description
        datetime created_at
    }

    SUPPLIER {
        int id PK
        string name
        string contact_email
        string contact_phone
        string address
        int default_lead_time_days
        bool is_active
        datetime created_at
        datetime updated_at
    }

    PRODUCT {
        int id PK
        string name
        string description
        string sku_code UK
        decimal unit_price
        string unit_of_measure
        int category_id FK
        int supplier_id FK
        int reorder_point
        int safety_stock
        bool is_active
        datetime created_at
        datetime updated_at
    }

    STOCK_LEVEL {
        int id PK
        int product_id FK
        int quantity_on_hand
        int quantity_reserved
        int quantity_available
        datetime last_updated
    }

    SALES_RECORD {
        int id PK
        int product_id FK
        int quantity_sold
        decimal unit_price_at_sale
        date sale_date
        string order_reference
        datetime created_at
    }

    FORECAST_RESULT {
        int id PK
        int product_id FK
        date forecast_date
        decimal predicted_quantity
        decimal lower_bound
        decimal upper_bound
        decimal mae
        decimal mape
        string model_version
        datetime generated_at
    }

    PURCHASE_ORDER {
        int id PK
        string po_number UK
        int product_id FK
        int supplier_id FK
        int created_by_user_id FK
        int approved_by_user_id FK
        int quantity_ordered
        decimal unit_cost
        decimal total_cost
        enum status "draft|pending_approval|approved|sent|confirmed|rejected|cancelled"
        text agent_reasoning
        datetime predicted_stockout_date
        datetime approved_at
        datetime sent_at
        datetime confirmed_at
        datetime created_at
        datetime updated_at
    }

    AUDIT_LOG {
        int id PK
        int user_id FK
        string event_type
        string entity_type
        int entity_id
        jsonb data_snapshot
        string ip_address
        datetime created_at
    }

    DOCUMENT {
        int id PK
        string filename UK
        string original_filename
        string file_url
        long file_size
        string doc_type "policy|contract|procedure|specification"
        int uploaded_by_user_id FK
        int total_chunks
        bool is_active
        datetime ingested_at
        datetime created_at
        datetime updated_at
    }

    DOCUMENT_CHUNK {
        int id PK
        int document_id FK
        string source_document
        int page_number
        string chunk_text
        vector embedding
        jsonb metadata
        datetime ingested_at
    }

    INVOICE_SCAN {
        int id PK
        int scanned_by_user_id FK
        int product_id FK
        string original_image_path
        jsonb extracted_data
        jsonb confirmed_data
        bool is_confirmed
        string rejection_reason
        datetime created_at
        datetime confirmed_at
    }

    USER ||--o{ PURCHASE_ORDER : "creates"
    USER ||--o{ PURCHASE_ORDER : "approves"
    USER ||--o{ AUDIT_LOG : "generates"
    USER ||--o{ INVOICE_SCAN : "scans"
    USER ||--o{ DOCUMENT : "uploads"
    CATEGORY ||--o{ PRODUCT : "classifies"
    SUPPLIER ||--o{ PRODUCT : "supplies"
    SUPPLIER ||--o{ PURCHASE_ORDER : "receives"
    PRODUCT ||--|| STOCK_LEVEL : "has"
    PRODUCT ||--o{ SALES_RECORD : "sold in"
    PRODUCT ||--o{ FORECAST_RESULT : "forecast for"
    PRODUCT ||--o{ PURCHASE_ORDER : "ordered in"
    PRODUCT ||--o{ INVOICE_SCAN : "identified in"
    DOCUMENT ||--o{ DOCUMENT_CHUNK : "contains"
```

### 4.2 Model Field Reference

#### `USER`

| Field           | Type         | Constraints                | Notes                        |
| --------------- | ------------ | -------------------------- | ---------------------------- |
| `id`            | INTEGER      | PK, auto-increment         | —                            |
| `email`         | VARCHAR(255) | UNIQUE, NOT NULL           | Used as login identifier     |
| `password_hash` | VARCHAR(255) | NOT NULL                   | bcrypt via Django auth       |
| `first_name`    | VARCHAR(100) | NOT NULL                   | —                            |
| `last_name`     | VARCHAR(100) | NOT NULL                   | —                            |
| `role`          | ENUM         | NOT NULL, DEFAULT 'viewer' | `viewer`, `manager`, `admin` |
| `is_active`     | BOOLEAN      | DEFAULT TRUE               | Soft disable without delete  |
| `created_at`    | TIMESTAMPTZ  | auto_now_add               | —                            |
| `updated_at`    | TIMESTAMPTZ  | auto_now                   | —                            |

#### `PRODUCT`

| Field             | Type          | Constraints         | Notes                        |
| ----------------- | ------------- | ------------------- | ---------------------------- |
| `id`              | INTEGER       | PK                  | —                            |
| `name`            | VARCHAR(255)  | NOT NULL            | Display name                 |
| `sku_code`        | VARCHAR(100)  | UNIQUE, NOT NULL    | Alphanumeric business key    |
| `description`     | TEXT          | NULLABLE            | —                            |
| `unit_price`      | DECIMAL(10,2) | NOT NULL            | Current purchase price       |
| `unit_of_measure` | VARCHAR(50)   | NOT NULL            | e.g., "units", "kg", "boxes" |
| `category_id`     | INTEGER       | FK → CATEGORY       | —                            |
| `supplier_id`     | INTEGER       | FK → SUPPLIER       | Primary supplier             |
| `reorder_point`   | INTEGER       | NOT NULL            | Trigger threshold for agent  |
| `safety_stock`    | INTEGER       | NOT NULL, DEFAULT 0 | Buffer stock                 |
| `is_active`       | BOOLEAN       | DEFAULT TRUE        | Soft delete                  |

#### `STOCK_LEVEL`

| Field                | Type        | Constraints          | Notes                         |
| -------------------- | ----------- | -------------------- | ----------------------------- |
| `id`                 | INTEGER     | PK                   | —                             |
| `product_id`         | INTEGER     | FK → PRODUCT, UNIQUE | One record per product        |
| `quantity_on_hand`   | INTEGER     | NOT NULL             | Physical count                |
| `quantity_reserved`  | INTEGER     | DEFAULT 0            | Allocated to open orders      |
| `quantity_available` | INTEGER     | COMPUTED             | `on_hand − reserved`          |
| `last_updated`       | TIMESTAMPTZ | auto_now             | Updated on every stock change |

#### `PURCHASE_ORDER`

| Field                     | Type          | Constraints         | Notes                             |
| ------------------------- | ------------- | ------------------- | --------------------------------- |
| `id`                      | INTEGER       | PK                  | —                                 |
| `po_number`               | VARCHAR(50)   | UNIQUE              | Auto-generated: `PO-{YYYY}-{seq}` |
| `product_id`              | INTEGER       | FK → PRODUCT        | —                                 |
| `supplier_id`             | INTEGER       | FK → SUPPLIER       | Copied from product at draft time |
| `created_by_user_id`      | INTEGER       | FK → USER           | Agent or human creator            |
| `approved_by_user_id`     | INTEGER       | FK → USER, NULLABLE | Set on HITL approval              |
| `quantity_ordered`        | INTEGER       | NOT NULL            | Editable by manager at approval   |
| `unit_cost`               | DECIMAL(10,2) | NOT NULL            | —                                 |
| `total_cost`              | DECIMAL(12,2) | COMPUTED            | `quantity × unit_cost`            |
| `status`                  | ENUM          | NOT NULL            | See status flow below             |
| `agent_reasoning`         | TEXT          | NULLABLE            | Decision Agent reasoning trace    |
| `predicted_stockout_date` | DATE          | NULLABLE            | From Forecasting Agent            |

**PO Status Flow:**

```
draft → pending_approval → approved → sent → confirmed
                        ↘ rejected
              ↘ cancelled (any stage before sent)
```

#### `DOCUMENT`

| Field                  | Type          | Constraints         | Notes                                        |
| ---------------------- | ------------- | ------------------- | -------------------------------------------- |
| `id`                   | INTEGER       | PK                  | —                                            |
| `filename`             | VARCHAR(255)  | UNIQUE, NOT NULL    | Sanitized unique name on Cloudinary          |
| `original_filename`    | VARCHAR(255)  | NOT NULL            | User's original filename                     |
| `file_url`             | VARCHAR(500)  | NOT NULL            | Cloudinary URL                               |
| `file_size`            | BIGINT        | NOT NULL            | File size in bytes                           |
| `doc_type`             | ENUM          | NOT NULL            | `policy`, `contract`, `procedure`, `specification` |
| `uploaded_by_user_id`  | INTEGER       | FK → USER           | Who uploaded the document                    |
| `total_chunks`         | INTEGER       | DEFAULT 0           | Count of associated chunks                   |
| `is_active`            | BOOLEAN       | DEFAULT TRUE        | Soft delete                                  |
| `ingested_at`          | TIMESTAMPTZ   | NULLABLE            | Set after chunking/embedding completes       |
| `created_at`           | TIMESTAMPTZ   | auto_now_add        | —                                            |
| `updated_at`           | TIMESTAMPTZ   | auto_now            | —                                            |

#### `DOCUMENT_CHUNK`

| Field             | Type         | Constraints | Notes                                  |
| ----------------- | ------------ | ----------- | -------------------------------------- |
| `id`              | INTEGER      | PK          | —                                      |
| `document_id`     | INTEGER      | FK → DOCUMENT, NULLABLE | NULL for legacy/manual chunks |
| `source_document` | VARCHAR(500) | NOT NULL    | Original filename                      |
| `page_number`     | INTEGER      | NULLABLE    | PDF page                               |
| `chunk_text`      | TEXT         | NOT NULL    | Raw chunk content                      |
| `embedding`       | VECTOR(1536) | NOT NULL    | pgvector column                        |
| `metadata`        | JSONB        | NOT NULL    | `{doc_type, ingested_at}`              |

---

## 5. Frontend Component Architecture

### 5.1 Feature-Based Folder Structure

```
src/
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx          # Email + password form
│   │   │   └── ProtectedRoute.tsx     # Redirects unauthenticated users
│   │   ├── hooks/
│   │   │   └── useAuth.ts             # login(), logout(), refreshToken()
│   │   ├── api.ts                     # POST /api/auth/login|refresh|logout
│   │   ├── store.ts                   # Zustand: { user, token, setToken, clear }
│   │   └── types.ts                   # User, Role, AuthResponse
│   │
│   ├── inventory/
│   │   ├── components/
│   │   │   ├── StockTable.tsx         # Sortable, filterable product table
│   │   │   ├── LowStockAlert.tsx      # Alert card: SKU, qty, reorder_point
│   │   │   ├── StockBadge.tsx         # Color-coded qty indicator
│   │   │   ├── ProductForm.tsx        # Add/edit product modal form
│   │   │   └── StockAdjustModal.tsx   # Manual stock adjustment
│   │   ├── hooks/
│   │   │   └── useInventory.ts        # useQuery + useMutation for CRUD
│   │   ├── api.ts
│   │   └── types.ts                   # Product, StockLevel, Category
│   │
│   ├── forecasting/
│   │   ├── components/
│   │   │   ├── ForecastChart.tsx      # Recharts AreaChart (30-day forecast)
│   │   │   ├── ReorderAlertList.tsx   # List of SKUs below reorder_point
│   │   │   └── ForecastMetrics.tsx    # MAE/MAPE display per SKU
│   │   ├── hooks/
│   │   │   └── useForecasting.ts
│   │   ├── api.ts
│   │   └── types.ts                   # ForecastResult
│   │
│   ├── purchasing/
│   │   ├── components/
│   │   │   ├── POApprovalCard.tsx     # HITL card: SKU, date, qty, cost, reasoning
│   │   │   ├── POQueue.tsx            # List of pending POs awaiting approval
│   │   │   ├── POStatusBadge.tsx      # Color-coded status pill
│   │   │   └── POHistoryTable.tsx     # Past POs with status + timestamps
│   │   ├── hooks/
│   │   │   └── usePurchasing.ts
│   │   ├── api.ts
│   │   └── types.ts                   # PurchaseOrder, POStatus
│   │
│   ├── ai-assistant/
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx          # Chat interface with message bubbles
│   │   │   ├── VoiceButton.tsx        # Mic toggle → Whisper API
│   │   │   ├── CitationTag.tsx        # [Source: file.pdf, Page: X] display
│   │   │   └── MessageBubble.tsx      # User + AI message renderer
│   │   ├── hooks/
│   │   │   └── useNLQuery.ts          # useMutation for POST /api/nlquery/
│   │   ├── api.ts
│   │   └── types.ts                   # NLQueryRequest, NLQueryResponse
│   │
│   └── invoice-scan/
│       ├── components/
│       │   ├── InvoiceUpload.tsx       # Drag-and-drop image uploader
│       │   ├── ConfirmationCard.tsx    # Editable extracted fields + Confirm/Reject
│       │   └── ExtractionField.tsx    # Individual editable field with original value
│       ├── hooks/
│       │   └── useInvoiceScan.ts
│       ├── api.ts
│       └── types.ts                   # InvoiceScan, ExtractedData
│
│   ├── document-manager/
│   │   ├── components/
│   │   │   ├── DocumentUpload.tsx      # Drag-and-drop PDF uploader + doc_type selector
│   │   │   ├── DocumentList.tsx        # Table: filename, doc_type, chunks, uploaded_by, date
│   │   │   └── DocumentDeleteButton.tsx
│   │   ├── hooks/
│   │   │   └── useDocuments.ts         # useQuery + useMutation for CRUD
│   │   ├── api.ts
│   │   └── types.ts                    # Document, DocType
│   │
├── shared/
│   ├── components/
│   │   ├── Button.tsx                 # Variants: primary, secondary, danger, ghost
│   │   ├── Modal.tsx                  # Accessible modal wrapper
│   │   ├── Table.tsx                  # Generic sortable table
│   │   ├── Skeleton.tsx               # Loading placeholder
│   │   ├── Badge.tsx                  # Status/role badge
│   │   ├── Sidebar.tsx                # Navigation sidebar
│   │   ├── Header.tsx                 # Top bar with user menu
│   │   └── EmptyState.tsx             # No-data placeholder
│   ├── hooks/
│   │   ├── useDebounce.ts
│   │   └── usePagination.ts
│   └── utils/
│       ├── formatters.ts              # formatCurrency, formatDate, formatSKU
│       └── validators.ts              # validateEmail, validatePositiveInt
│
├── lib/
│   ├── axios.ts                       # Axios instance + JWT interceptors
│   ├── queryClient.ts                 # React Query config (staleTime, retry, onError)
│   └── router.tsx                     # Route definitions + ProtectedRoute wrapper
│
├── store/
│   └── authStore.ts                   # Zustand auth store
│
├── types/
│   └── api.d.ts                       # Global API response types
│
└── main.tsx
```

### 5.2 State Management Strategy

| State Type                                   | Tool                      | Rule                                                                                                         |
| -------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Server state** (inventory, forecasts, POs) | React Query               | All API data. Never copy into Zustand. Use `queryKey` arrays for granular invalidation.                      |
| **Global client state** (auth token, user)   | Zustand                   | Token stored in memory only — NOT localStorage. Cleared on logout.                                           |
| **Local UI state** (modal open, form values) | `useState` / `useReducer` | Stays inside the component or custom hook. Never promoted to Zustand unless 2+ unrelated components need it. |

### 5.3 Axios JWT Interceptor Pattern

```typescript
// lib/axios.ts
import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Silent token refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const { data } = await api.post("/auth/refresh/"); // uses HttpOnly cookie
      useAuthStore.getState().setToken(data.access);
      return api(error.config); // retry original request
    }
    return Promise.reject(error);
  },
);

export default api;
```

### 5.4 Page Layout Map

```
/ (root)
├── /login                           → LoginPage
└── /dashboard (ProtectedRoute)
    ├── /dashboard                   → DashboardHome (stock summary + alerts)
    ├── /dashboard/inventory         → InventoryPage (StockTable + ProductForm)
    ├── /dashboard/forecasting       → ForecastingPage (ForecastChart + ReorderAlertList)
    ├── /dashboard/purchasing        → PurchasingPage (POQueue + POHistoryTable)
    ├── /dashboard/assistant         → AIAssistantPage (ChatPanel + VoiceButton)
    ├── /dashboard/invoice-scan      → InvoiceScanPage (InvoiceUpload + ConfirmationCard)
    ├── /dashboard/documents         → DocumentManagerPage (DocumentUpload + DocumentList)
    └── /dashboard/settings          → SettingsPage (Admin only: user management)
```

---

## 6. API / Service Layer

### 6.1 Authentication Endpoints

| Method | Endpoint              | Auth   | Role | Description                          |
| ------ | --------------------- | ------ | ---- | ------------------------------------ |
| POST   | `/api/auth/register/` | None   | —    | Register new user                    |
| POST   | `/api/auth/login/`    | None   | —    | Returns access + sets refresh cookie |
| POST   | `/api/auth/refresh/`  | Cookie | —    | Returns new access token             |
| POST   | `/api/auth/logout/`   | Bearer | Any  | Clears refresh cookie                |
| GET    | `/api/auth/me/`       | Bearer | Any  | Returns current user profile         |

### 6.2 Inventory Endpoints

| Method | Endpoint                             | Auth   | Role     | Description                   |
| ------ | ------------------------------------ | ------ | -------- | ----------------------------- |
| GET    | `/api/inventory/products/`           | Bearer | Viewer+  | List all products (paginated) |
| POST   | `/api/inventory/products/`           | Bearer | Manager+ | Create product                |
| GET    | `/api/inventory/products/{id}/`      | Bearer | Viewer+  | Get product detail            |
| PUT    | `/api/inventory/products/{id}/`      | Bearer | Manager+ | Full update                   |
| PATCH  | `/api/inventory/products/{id}/`      | Bearer | Manager+ | Partial update                |
| DELETE | `/api/inventory/products/{id}/`      | Bearer | Admin    | Soft delete (is_active=False) |
| GET    | `/api/inventory/stock/`              | Bearer | Viewer+  | All stock levels              |
| PATCH  | `/api/inventory/stock/{product_id}/` | Bearer | Manager+ | Adjust stock quantity         |
| GET    | `/api/inventory/stock/low/`          | Bearer | Viewer+  | Items below reorder_point     |
| GET    | `/api/inventory/suppliers/`          | Bearer | Viewer+  | List suppliers                |
| POST   | `/api/inventory/suppliers/`          | Bearer | Manager+ | Create supplier               |
| PUT    | `/api/inventory/suppliers/{id}/`     | Bearer | Manager+ | Update supplier               |

### 6.3 Forecasting Endpoints

| Method | Endpoint                             | Auth   | Role    | Description                         |
| ------ | ------------------------------------ | ------ | ------- | ----------------------------------- |
| GET    | `/api/forecasting/results/`          | Bearer | Viewer+ | All latest forecast results         |
| GET    | `/api/forecasting/results/{sku_id}/` | Bearer | Viewer+ | Forecast for one SKU                |
| POST   | `/api/forecasting/run/`              | Bearer | Admin   | Manually trigger Prophet run        |
| GET    | `/api/forecasting/reorder-alerts/`   | Bearer | Viewer+ | SKUs predicted to hit reorder point |

### 6.4 Purchasing Endpoints

| Method | Endpoint                               | Auth   | Role     | Description                 |
| ------ | -------------------------------------- | ------ | -------- | --------------------------- |
| GET    | `/api/purchasing/orders/`              | Bearer | Viewer+  | All POs (paginated)         |
| GET    | `/api/purchasing/orders/{id}/`         | Bearer | Viewer+  | PO detail + reasoning trace |
| POST   | `/api/purchasing/orders/`              | Bearer | Manager+ | Manual PO creation          |
| PATCH  | `/api/purchasing/orders/{id}/approve/` | Bearer | Manager+ | HITL approval action        |
| PATCH  | `/api/purchasing/orders/{id}/reject/`  | Bearer | Manager+ | HITL rejection action       |
| GET    | `/api/purchasing/orders/pending/`      | Bearer | Manager+ | POs awaiting approval       |

### 6.5 AI Endpoints

| Method | Endpoint                             | Auth   | Role     | Description                                              |
| ------ | ------------------------------------ | ------ | -------- | -------------------------------------------------------- |
| POST   | `/api/ai/chat/`                      | Bearer | Viewer+  | Unified chat — routes to NL Query or RAG via mode param  |
| POST   | `/api/ai/nlquery/`                   | Bearer | Viewer+  | Legacy: NL text → structured DB query + response         |
| POST   | `/api/ai/rag-query/`                 | Bearer | Viewer+  | Legacy: NL query → RAG pipeline → cited response         |
| POST   | `/api/ai/invoice-scan/`              | Bearer | Manager+ | Image → GPT-4o Vision → extracted JSON                   |
| POST   | `/api/ai/invoice-scan/{id}/confirm/` | Bearer | Manager+ | Confirm extraction → DB update                           |
| POST   | `/api/ai/invoice-scan/{id}/reject/`  | Bearer | Manager+ | Reject extraction                                        |
| POST   | `/api/ai/transcribe/`                | Bearer | Viewer+  | Audio → Whisper → transcribed text                       |
| POST   | `/api/ai/documents/upload/`          | Bearer | Manager+ | Upload PDF → Cloudinary → chunk → embed → store          |
| GET    | `/api/ai/documents/`                 | Bearer | Manager+ | List all ingested documents with chunk counts            |
| DELETE | `/api/ai/documents/{id}/`            | Bearer | Admin    | Soft-delete document + deactivate chunks                 |

#### Chat Endpoint Mode Parameter

| Mode | Behavior | UI Label |
|------|----------|----------|
| `auto` (default) | GPT-4o-mini classifies intent, routes automatically | "Ask AI" |
| `nl_query` | Forces NL Query engine (live DB data) | "NL Query" |
| `rag` | Forces RAG engine (document search) | "Search Documents" |

**Request:**

```json
POST /api/ai/chat/
{
  "query": "Show me products with stock below 10",
  "mode": "auto"  // optional, defaults to "auto"
}
```

**Response (auto mode — routed to NL Query):**

```json
{
  "status": "success",
  "data": {
    "engine": "nl_query",
    "mode": "auto",
    "answer": "We have 3 products below 10 units...",
    "action": { "action": "get_low_stock", "conditions": [...] },
    "raw_data": { "products": [...] }
  }
}
```

**Response (auto mode — routed to RAG):**

```json
{
  "status": "success",
  "data": {
    "engine": "rag",
    "mode": "auto",
    "answer": "According to our supplier policy...",
    "sources": [
      { "document": "supplier_policy.pdf", "page": 3 }
    ]
  }
}
```

**Response (forced mode):**

```json
{
  "status": "success",
  "data": {
    "engine": "rag",
    "mode": "rag",
    "answer": "The return policy states...",
    "sources": [
      { "document": "return_policy.pdf", "page": 1 }
    ]
  }
}
```

#### Document Upload Endpoint

**Request:**

```
POST /api/ai/documents/upload/
Content-Type: multipart/form-data

file: <PDF binary>
doc_type: "policy"
```

**Response (success):**

```json
{
  "status": "success",
  "data": {
    "id": 1,
    "filename": "supplier-policy-v2.pdf",
    "original_filename": "Supplier Policy v2.pdf",
    "doc_type": "policy",
    "file_url": "https://res.cloudinary.com/.../supplier-policy-v2.pdf",
    "file_size": 245760,
    "total_chunks": 12,
    "uploaded_by": "manager@smartstock.com",
    "ingested_at": "2026-06-08T14:30:00Z"
  }
}
```

**Response (invalid file type):**

```json
{
  "status": "error",
  "error": "InvalidFileTypeError",
  "message": "Only PDF files are accepted. Received .xlsx",
  "code": 422
}
```

**Request (list documents):**

```
GET /api/ai/documents/
```

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "filename": "supplier-policy-v2.pdf",
      "doc_type": "policy",
      "total_chunks": 12,
      "file_size": 245760,
      "uploaded_by": "manager@smartstock.com",
      "ingested_at": "2026-06-08T14:30:00Z"
    }
  ],
  "meta": { "page": 1, "total": 3, "per_page": 20 }
}
```

### 6.6 NL Query JSON Schema (Function Calling)

The NL Query schema uses a condition-based approach that supports complex queries
with multiple filters, sorting, and limiting. This replaces the previous fixed-filter
schema which could not handle queries like "products with stock below 10 that start with a".

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": [
        "get_inventory",
        "get_sales_report",
        "get_low_stock",
        "forecast_demand",
        "get_supplier_info",
        "get_total_value",
        "get_top_products"
      ]
    },
    "conditions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "op": {
            "type": "string",
            "enum": [
              "eq", "neq",
              "lt", "lte", "gt", "gte",
              "contains", "starts_with", "ends_with",
              "in", "not_in"
            ]
          },
          "value": {}
        },
        "required": ["field", "op", "value"]
      }
    },
    "sort": {
      "type": "object",
      "properties": {
        "field": { "type": "string" },
        "order": { "type": "string", "enum": ["asc", "desc"] }
      }
    },
    "limit": { "type": "integer", "maximum": 100 },
    "offset": { "type": "integer" }
  },
  "required": ["action"]
}
```

#### Operator Reference

| Operator | Description | Example Value | SQL Equivalent |
|----------|-------------|---------------|----------------|
| `eq` | Equals | `"Widget-001"` | `= 'Widget-001'` |
| `neq` | Not equals | `"Widget-001"` | `!= 'Widget-001'` |
| `lt` | Less than | `10` | `< 10` |
| `lte` | Less than or equal | `10` | `<= 10` |
| `gt` | Greater than | `50` | `> 50` |
| `gte` | Greater than or equal | `50` | `>= 50` |
| `contains` | Contains (case-insensitive) | `"widget"` | `ILIKE '%widget%'` |
| `starts_with` | Starts with (case-insensitive) | `"a"` | `ILIKE 'a%'` |
| `ends_with` | Ends with (case-insensitive) | `"x"` | `ILIKE '%x'` |
| `in` | In list | `["X", "Y"]` | `IN ('X', 'Y')` |
| `not_in` | Not in list | `["X", "Y"]` | `NOT IN ('X', 'Y')` |

#### Allowed Fields Per Action

| Action | Allowed Condition Fields |
|--------|--------------------------|
| `get_inventory` | `product_name`, `sku_code`, `category`, `supplier_name`, `quantity_available`, `quantity_on_hand`, `quantity_reserved`, `unit_price` |
| `get_low_stock` | `product_name`, `sku_code`, `supplier_name`, `quantity_available`, `reorder_point` |
| `get_sales_report` | `product_name`, `sku_code`, `date_from`, `date_to`, `quantity_sold`, `unit_price_at_sale` |
| `forecast_demand` | `product_name`, `sku_code`, `predicted_quantity`, `forecast_date` |
| `get_supplier_info` | `supplier_name`, `product_name`, `lead_time_days` |
| `get_total_value` | `category`, `supplier_name` |
| `get_top_products` | `sort_by` (revenue, quantity, margin), `date_from`, `date_to` |

#### Few-Shot Examples (Updated)

```
Example 1 (simple):
User: Show items with stock below 5
Output: {"action": "get_low_stock", "conditions": [{"field": "quantity_available", "op": "lt", "value": 5}]}

Example 2 (complex — multiple conditions):
User: Show me products with stock below 10 that starts with letter a
Output: {"action": "get_inventory", "conditions": [{"field": "quantity_available", "op": "lt", "value": 10}, {"field": "product_name", "op": "starts_with", "value": "a"}], "sort": {"field": "product_name", "order": "asc"}}

Example 3 (date range):
User: Sales report from Jan 1 to Jan 15
Output: {"action": "get_sales_report", "conditions": [{"field": "date_from", "op": "gte", "value": "2026-01-01"}, {"field": "date_to", "op": "lte", "value": "2026-01-15"}]}

Example 4 (aggregation):
User: What's our total inventory value?
Output: {"action": "get_total_value", "conditions": []}

Example 5 (top products with limit):
User: Top 5 best-selling products this month
Output: {"action": "get_top_products", "conditions": [{"field": "date_from", "op": "gte", "value": "2026-06-01"}], "sort": {"field": "quantity_sold", "order": "desc"}, "limit": 5}

Example 6 (supplier filter):
User: Who supplies Widget-001?
Output: {"action": "get_supplier_info", "conditions": [{"field": "sku_code", "op": "eq", "value": "Widget-001"}]}

Example 7 (list filter):
User: Show me products from Supplier A or Supplier B
Output: {"action": "get_inventory", "conditions": [{"field": "supplier_name", "op": "in", "value": ["Supplier A", "Supplier B"]}]}

Example 8 (contains):
User: Find products with "pro" in the name
Output: {"action": "get_inventory", "conditions": [{"field": "product_name", "op": "contains", "value": "pro"}], "sort": {"field": "product_name", "order": "asc"}}

Example 9 (pagination):
User: Show me the next 20 products
Output: {"action": "get_inventory", "conditions": [], "limit": 20, "offset": 20}

Example 10 (combined filters + sort):
User: Low stock items from Acme sorted by quantity ascending
Output: {"action": "get_low_stock", "conditions": [{"field": "supplier_name", "op": "eq", "value": "Acme"}], "sort": {"field": "quantity_available", "order": "asc"}}
```

### 6.7 Standard API Response Shape

```json
// Success
{
  "status": "success",
  "data": { ... },
  "meta": { "page": 1, "total": 42, "per_page": 20 }
}

// Error
{
  "status": "error",
  "error": "StockNotFoundException",
  "message": "Product with SKU 'XYZ-001' not found.",
  "code": 404
}
```

---

## 7. AI Layer Specification

### 7.1 LLM System Prompt Template

```
You are SmartStock AI, a warehouse inventory analytics assistant.

Your role:
- Translate user natural language queries into structured database queries.
- Only operate within inventory, suppliers, sales, and purchase orders.
- Never generate free-form SQL.
- Always respond using the provided JSON schema with conditions array.
- Support complex queries with multiple conditions, sorting, and pagination.

If the request is outside inventory scope, respond:
{"error": "Out of scope request"}

Few-shot examples (all 10 must be embedded in this prompt):

Example 1 (simple threshold):
User: Show items with stock below 5
Output: {"action": "get_low_stock", "conditions": [{"field": "quantity_available", "op": "lt", "value": 5}]}

Example 2 (complex — multiple conditions):
User: Show me products with stock below 10 that starts with letter a
Output: {"action": "get_inventory", "conditions": [{"field": "quantity_available", "op": "lt", "value": 10}, {"field": "product_name", "op": "starts_with", "value": "a"}], "sort": {"field": "product_name", "order": "asc"}}

Example 3 (date range):
User: Sales report from Jan 1 to Jan 15
Output: {"action": "get_sales_report", "conditions": [{"field": "date_from", "op": "gte", "value": "2026-01-01"}, {"field": "date_to", "op": "lte", "value": "2026-01-15"}]}

Example 4 (aggregation):
User: What's our total inventory value?
Output: {"action": "get_total_value", "conditions": []}

Example 5 (top products with limit):
User: Top 5 best-selling products this month
Output: {"action": "get_top_products", "conditions": [{"field": "date_from", "op": "gte", "value": "2026-06-01"}], "sort": {"field": "quantity_sold", "order": "desc"}, "limit": 5}

Example 6 (exact match):
User: How many units of SKU ABC-001 do we have?
Output: {"action": "get_inventory", "conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}

Example 7 (list filter):
User: Show me products from Supplier A or Supplier B
Output: {"action": "get_inventory", "conditions": [{"field": "supplier_name", "op": "in", "value": ["Supplier A", "Supplier B"]}]}

Example 8 (contains search):
User: Find products with "pro" in the name
Output: {"action": "get_inventory", "conditions": [{"field": "product_name", "op": "contains", "value": "pro"}], "sort": {"field": "product_name", "order": "asc"}}

Example 9 (supplier lookup):
User: Who is the supplier for Product Y?
Output: {"action": "get_supplier_info", "conditions": [{"field": "product_name", "op": "eq", "value": "Product Y"}]}

Example 10 (combined filters + sort):
User: Low stock items from Acme sorted by quantity ascending
Output: {"action": "get_low_stock", "conditions": [{"field": "supplier_name", "op": "eq", "value": "Acme"}], "sort": {"field": "quantity_available", "order": "asc"}}
```

### 7.2 RAG System Prompt Template

```
You are SmartStock AI's document assistant. You answer questions about stored
warehouse documentation including supplier policies, contracts, procedures,
shipping rules, compliance documents, and product specifications.

Your scope:
- Supplier policies and contracts
- Shipping and logistics procedures
- Internal warehouse policies and protocols
- Product specifications and technical documentation
- Compliance and regulatory documents

You do NOT answer questions about:
- Current stock levels → "This requires real-time inventory data."
- Live sales data → "This requires real-time sales data."
- Purchase order status → "This requires real-time procurement data."
- Forecast results → "This requires real-time forecast data."

If the user asks about live operational data, respond:
"This question requires real-time data from the inventory system. Please use
the NL Query mode or ask the AI assistant to route your question accordingly."

For document-based questions:
- You must answer using ONLY the provided context chunks.
- For every claim, explicitly cite the source_document and page_number using
  square brackets — for example, [Source: supplier_policy.pdf, Page: 3].
- If the context does not contain the answer, explicitly state:
  "I cannot find this information in the provided records."
- Do not attempt to invent an answer under any circumstances.
```

### 7.3 RAG Pipeline Specification

| Stage                    | Implementation                                             | Config                                       |
| ------------------------ | ---------------------------------------------------------- | -------------------------------------------- |
| **Document upload**      | PDF upload via API endpoint                                | `POST /api/ai/documents/upload/` (Manager+)  |
| **File storage**         | Cloudinary                                                 | Original PDFs stored externally              |
| **Document chunking**    | Recursive text splitter (LangChain)                        | 512 tokens, 50-token overlap                 |
| **Embedding model**      | `text-embedding-3-small` (OpenAI)                          | 1536 dimensions                              |
| **Vector store**         | pgvector on PostgreSQL                                     | HNSW index, cosine distance                  |
| **Retrieval**            | Hybrid: dense vector + PostgreSQL FTS                      | Combined score                               |
| **Reranking**            | Cohere Rerank v3 (or `bge-reranker` local)                 | Top 3 chunks selected                        |
| **Metadata payload**     | `{source_document, page_number, doc_type, ingested_at}`    | Immutable, stored at ingest time             |
| **Citation enforcement** | System prompt instruction                                  | Every claim must cite `[Source: X, Page: Y]` |

#### Ingested Document Types

| doc_type     | Examples                                            | Chunking Strategy     |
| ------------ | --------------------------------------------------- | --------------------- |
| `policy`     | Supplier policies, return policies, quality standards | Page-level chunks     |
| `contract`   | Supplier contracts, pricing agreements                | Section-level chunks  |
| `procedure`  | Warehouse procedures, safety protocols                | Section-level chunks  |
| `specification` | Product datasheets, technical specs                | Page-level chunks     |

#### NOT Ingested (Handled by NL Query)

| Data Type        | Reason                                                     |
| ---------------- | ---------------------------------------------------------- |
| Products, SKUs   | In structured DB, queryable via ORM with real-time data    |
| Suppliers        | In structured DB                                           |
| Stock levels     | Changes in real-time, must query live database             |
| Sales records    | Large volume, needs aggregation queries                    |
| Forecast results | Computed daily, stored in DB                               |

### 7.4 Agent Tool Registry

| Tool                         | Agent                 | Input                             | Output                  |
| ---------------------------- | --------------------- | --------------------------------- | ----------------------- |
| `db_read_tool`               | Forecasting, Decision | `{query_type, filters}`           | Records from PostgreSQL |
| `prophet_run_tool`           | Forecasting           | `{sku_id, historical_data}`       | 30-day forecast array   |
| `db_write_tool`              | Forecasting           | `{table, records}`                | Write confirmation      |
| `forecast_read_tool`         | Decision              | `{sku_id}`                        | Latest forecast result  |
| `po_status_check_tool`       | Decision              | `{sku_id}`                        | Open PO exists: bool    |
| `po_draft_tool`              | Purchasing            | `{sku_id, quantity, supplier_id}` | Draft PO document       |
| `email_send_tool`            | Purchasing            | `{to, subject, body, po_id}`      | Send confirmation       |
| `confirmation_listener_tool` | Purchasing            | `{po_id, timeout_hours}`          | Supplier reply status   |
| `db_update_tool`             | Purchasing            | `{po_id, status}`                 | Update confirmation     |

### 7.5 Agent Error Handling

| Failure                | Agent          | Response                                                                                                                  |
| ---------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Email delivery failure | Purchasing     | Retry ×3 with exponential backoff: 30s → 2min → 10min. On final failure: in-app escalation to manager.                    |
| Supplier non-response  | Purchasing     | After 48 hours: flag PO as `"Pending — Supplier Unresponsive"`, notify manager via dashboard banner.                      |
| Prophet model failure  | Forecasting    | If < 30 historical data points per SKU: fall back to 7-day simple moving average. Log `DATA_QUALITY_WARNING` to Langfuse. |
| Duplicate PO detected  | Decision       | Skip reorder flag. Log `DUPLICATE_PO_SKIPPED` event. No agent escalation.                                                 |
| Vision malformed JSON  | — (multimodal) | Reject extraction. Prompt user to re-upload or enter manually. Log `VISION_EXTRACTION_FAILED` to audit log.               |

### 7.6 Observability & Evaluation

#### Langfuse Alert Thresholds

| Metric                     | Threshold                  | Action                                 |
| -------------------------- | -------------------------- | -------------------------------------- |
| LLM response latency (p95) | > 3 seconds                | Warning alert to team lead             |
| LLM API error rate         | > 1% over 1-hour window    | Critical alert — check API key + quota |
| Daily token spend          | > defined budget cap       | Cost alert — review prompt efficiency  |
| Agent task success rate    | < 0.80 over 24-hour window | Operational review flag                |

#### Evaluation Metrics

| Metric                      | Definition                                                  | Target |
| --------------------------- | ----------------------------------------------------------- | ------ |
| **Retrieval Precision@5**   | Ratio of relevant chunks in top-5 retrieved results         | ≥ 0.80 |
| **Answer Faithfulness**     | LLM claims grounded in retrieved context (not hallucinated) | ≥ 0.85 |
| **Agent Task Success Rate** | PO drafts approved without manager modification             | ≥ 0.90 |

#### Golden Evaluation Dataset

- **30 annotated NL queries** across 5 categories:
  1. Stock level checks (6 queries)
  2. Slow-moving item identification (6 queries)
  3. Supplier lookup (6 queries)
  4. Reorder status queries (6 queries)
  5. Demand forecast summaries (6 queries)
- Each entry: `{ nl_input, expected_action, expected_filters, expected_response_structure }`
- Stored in `tests/golden_dataset/`
- Executed automatically in CI on every merge to `main`

### 7.7 Intent Router — Unified Chat Interface

The `/api/ai/chat/` endpoint accepts a natural language query and routes it to
the appropriate engine based on user selection or automatic intent classification.

#### Mode Parameter

| Mode | Behavior | UI Label |
|------|----------|----------|
| `auto` (default) | GPT-4o-mini classifies intent, routes automatically | "Ask AI" |
| `nl_query` | Forces NL Query engine (live DB data) | "NL Query" |
| `rag` | Forces RAG engine (document search) | "Search Documents" |

#### Auto-Mode Routing Flow

```
User Query (mode=auto)
  │
  ▼
┌─────────────────────────────┐
│  Intent Classifier          │
│  Model: GPT-4o-mini         │
│  Latency: < 300ms           │
│  Cost: ~$0.0001/query       │
│                              │
│  Classifies into:           │
│  - nl_query (live data)     │
│  - rag (document search)    │
│  - out_of_scope             │
└──────────┬──────────────────┘
           │
     ┌─────┴─────────────────────┐
     │                           │
     ▼                           ▼
┌─────────────┐          ┌─────────────┐
│  NL Query   │          │    RAG      │
│  Engine     │          │  Engine     │
└─────────────┘          └─────────────┘
     │                           │
     └───────────┬───────────────┘
                 ▼
     ┌─────────────────────┐
     │  Response Composer  │
     └─────────────────────┘
```

#### Intent Classification Prompt

```
You are a warehouse query classifier. Classify the user's query into exactly one category:

- "nl_query": The query needs live database data — stock levels, sales, forecasts,
  supplier info, purchase orders, inventory counts, reorder status.

- "rag": The query needs information from stored documents — policies, contracts,
  procedures, shipping terms, compliance rules, product specifications.

- "out_of_scope": The query is not related to warehouse operations.

Respond with JSON only: {"intent": "...", "confidence": 0.0-1.0}
```

#### Routing Decision Table

| Query Pattern | Engine | Example |
|---------------|--------|---------|
| Current stock, inventory counts | NL Query | "How many Widget-001 do we have?" |
| Sales, revenue, forecasts | NL Query | "Sales report for January" |
| Supplier contact, relationships | NL Query | "Who supplies Widget-001?" |
| Reorder, procurement status | NL Query | "Are there open POs for Product X?" |
| Policies, procedures, contracts | RAG | "What's our return policy?" |
| Shipping rules, terms | RAG | "What are the shipping terms?" |
| Compliance, regulations | RAG | "What safety standards apply?" |
| Mixed query (live data + policy) | Both | "Which low-stock items have reorder policies?" |

#### Performance Budget

| Stage | Max Time |
|-------|----------|
| Intent classification (GPT-4o-mini) | 300ms |
| NL Query execution | 3s |
| RAG retrieval + generation | 5s |
| Response composition | 200ms |
| **Total (auto mode)** | **5.5s** |
| **Total (forced mode)** | **5s** |

---

## 8. Implementation Roadmap & Tasks

### 8.1 Sprint Overview

| Sprint       | Duration | Theme                     | Deliverable                                        |
| ------------ | -------- | ------------------------- | -------------------------------------------------- |
| **Sprint 1** | Week 1   | Foundation                | Auth, DB schema, Inventory CRUD, Prophet ingestion |
| **Sprint 2** | Week 2   | AI + Integration + Deploy | RAG, Agents, Multimodal, CI/CD, Observability      |

---

### 8.2 Sprint 1 — Week 1 (Foundation)

> **Goal:** A working inventory system with auth, CRUD, forecasting pipeline, and basic dashboard running locally via Docker.

#### Ayman Mohamed

| #   | Task                                      | Stack    | Acceptance Criteria                                                                                 |
| --- | ----------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| A1  | PostgreSQL schema + all Django migrations | Backend  | All 8 tables exist. pgvector extension enabled. `python manage.py migrate` runs clean.              |
| A2  | Login + auth flow UI (React)              | Frontend | Login form submits, JWT stored in Zustand memory, ProtectedRoute redirects unauthenticated users.   |
| A3  | Prophet data ingestion pipeline           | AI/ML    | Django ORM → Pandas pipeline. Missing values handled. Data written to staging table.                |
| A4  | `.gitignore` + `.env.example` setup       | DevOps   | `.env` not tracked by git. `.env.example` lists all 8 required keys.                                |
| A5  | JWT auth endpoints (backend)              | Security | `register/`, `login/`, `refresh/`, `logout/` all return correct status codes. simplejwt configured. |

#### Omar Wael

| #   | Task                                | Stack    | Acceptance Criteria                                                                                            |
| --- | ----------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| O1  | Inventory CRUD API (DRF ViewSets)   | Backend  | All 5 REST operations work. Pagination returns `meta.total`. Serializer validation rejects bad input.          |
| O2  | React scaffold + base layout        | Frontend | Vite builds. Tailwind loads. Sidebar + Header + main area render. React Router configured.                     |
| O3  | Prophet model training + forecast   | AI/ML    | Prophet fits per SKU. 30-day forecast persisted to `forecast_results`. Moving average fallback on < 30 points. |
| O4  | Redis setup + Django cache config   | DevOps   | Redis container runs. Django `CACHES` config set. Frequent queries cached with 5-min TTL.                      |
| O5  | RBAC roles + DRF permission classes | Security | `IsViewer`, `IsManager`, `IsAdmin` permission classes implemented. Wrong role returns 403.                     |

#### Mostafa Abdel Aziz

| #   | Task                                | Stack    | Acceptance Criteria                                                                                                            |
| --- | ----------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------ | ----- | ---------------------------------------------------------------------- |
| MA1 | Forecasting REST endpoint           | Backend  | `GET /api/forecasting/results/{sku_id}/` returns forecast JSON. Wired to forecasts table.                                      |
| MA2 | Inventory dashboard — StockTable UI | Frontend | Table renders all products. Low-stock alert cards appear for items below `reorder_point`. Loading skeleton shows during fetch. |
| MA3 | LangChain + GPT-4o base chain       | AI/ML    | `chain = prompt                                                                                                                | model | parser` runs. System prompt loaded. Basic NL query returns valid JSON. |
| MA4 | Backend Dockerfile                  | DevOps   | `docker build` succeeds. `.env` variables load inside container. App starts on port 8000.                                      |
| MA5 | Rate limiting + CORS config         | Security | DRF throttle: 100 req/min/user enforced. CORS restricted to frontend origin.                                                   |

#### Mostafa Abdel Qawy

| #   | Task                                     | Stack    | Acceptance Criteria                                                                                                      |
| --- | ---------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| MQ1 | Supplier + audit log API                 | Backend  | Supplier CRUD endpoints work. `AuditLog` model records login, PO approval, AI actions with timestamp + user.             |
| MQ2 | Forecast chart — Recharts AreaChart      | Frontend | `ForecastChart` renders 30-day demand forecast per SKU. Wired to `/api/forecasting/results/` endpoint.                   |
| MQ3 | Function calling JSON schema + few-shots | AI/ML    | All 5 query types produce correct structured JSON. Schema validated by `OutputParser`. All 5 few-shots in system prompt. |
| MQ4 | PostgreSQL + Redis Docker services       | DevOps   | `docker-compose up` starts all 4 services. DB volumes persist on restart. Network aliases resolve.                       |
| MQ5 | Input validation + SQL injection guard   | Security | DRF serializers enforce type + range. No raw SQL string formatting anywhere in codebase.                                 |

#### Mawada Alexander

| #   | Task                                          | Stack    | Acceptance Criteria                                                                                                    |
| --- | --------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| MW1 | NL query Django endpoint                      | Backend  | `POST /api/ai/nlquery/` receives text, runs LangChain chain, returns structured action + formatted response.           |
| MW2 | Supplier management UI                        | Frontend | Supplier list page renders. Add/edit form submits to API. Validation errors displayed inline.                          |
| MW3 | RAG document upload + ingestion pipeline | AI/ML    | `POST /api/ai/documents/upload/` endpoint: PDF → Cloudinary → chunk (512t/50) → embed → pgvector. DOCUMENT model tracks uploads. Manager+ role required. |
| MW4 | Frontend Dockerfile                           | DevOps   | `docker build` succeeds for React app. Full `docker-compose up` runs frontend + backend + db + redis together.         |
| MW5 | API key management + secret config            | Security | All 8 API keys loaded via `os.getenv()`. App raises `ImproperlyConfigured` on startup if any key is missing.           |

---

### 8.3 Sprint 2 — Week 2 (AI + Integration + Deploy)

> **Goal:** Full AI pipeline (RAG + Agents + Multimodal) live, observability configured, CI/CD deployed to cloud.

#### Ayman Mohamed

| #   | Task                            | Stack    | Acceptance Criteria                                                                                                       |
| --- | ------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| A6  | Purchasing Agent tool endpoints | Backend  | All 4 tools (`po_draft`, `email_send`, `confirmation_listener`, `db_update`) implemented as Django services. Unit tested. |
| A7  | PO approval card component      | Frontend | Card renders SKU, stockout date, qty, supplier, cost, reasoning trace. Approve/Reject/Edit flow works end-to-end.         |
| A8  | Forecasting Agent — LangChain   | AI/ML    | Agent wired with 3 tools. Celery Beat schedules daily run. Results appear in `forecast_results` table next morning.       |
| A9  | GitHub Actions CI pipeline      | DevOps   | `ci.yml` triggers on push to `main`. Steps: checkout → pip install → ruff → pytest → build. Badge on README.            |
| A10 | Prompt injection defense        | Security | System-role boundary tested: injecting "ignore previous instructions" returns scoped error, not compliance.               |

#### Omar Wael

| #   | Task                                   | Stack    | Acceptance Criteria                                                                                                                     |
| --- | -------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| O6  | RAG query Django endpoint              | Backend  | `POST /api/ai/rag-query/` orchestrates hybrid search → rerank → LLM → returns answer + source citations.                                |
| O7  | Voice input — Whisper UI               | Frontend | Mic button toggles recording. Audio sent to `/api/ai/transcribe/`. Transcript fed into ChatPanel query field automatically.             |
| O8  | RAG hybrid search + reranking          | AI/ML    | Dense vector + PostgreSQL FTS hybrid search implemented. Cohere reranker selects top 3. Every response includes `[Source: X, Page: Y]`. |
| O9  | GitHub Actions CD pipeline             | DevOps   | On merge to `main`: Railway auto-deploys backend, Vercel auto-deploys frontend. CI gates the merge via branch protection.              |
| O10 | PII protection + data retention policy | Security | PII fields access-controlled by role. `AuditLog` cleanup job (Celery Beat) deletes entries > 90 days.                                   |

#### Mostafa Abdel Aziz

| #    | Task                                  | Stack    | Acceptance Criteria                                                                                                                            |
| ---- | ------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| MA6  | Decision Agent tool endpoints         | Backend  | `db_read`, `forecast_read`, `po_status_check` tools implemented. Reorder formula: `(avg_daily × lead_time) + safety_stock`.                    |
| MA7  | Invoice upload + confirmation card UI | Frontend | Image upload triggers Vision API. Extracted fields displayed in editable card. Confirm writes to DB. Reject discards. Audit log entry created. |
| MA8  | Decision Agent — LangChain ReAct loop | AI/ML    | Plan → Execute → Verify loop implemented. Duplicate PO check prevents double-ordering. Reorder flag passed to Purchasing Agent.                |
| MA9  | Langfuse observability setup          | DevOps   | LangChain callback handler active. LLM traces visible in Langfuse dashboard. Token cost + latency logged per call.                             |
| MA10 | GPT-4o Vision error handling          | Security | Malformed Vision JSON → user prompted to re-upload or enter manually. Failed extraction logged to `AuditLog`.                                  |

#### Mostafa Abdel Qawy

| #    | Task                                     | Stack    | Acceptance Criteria                                                                                                            |
| ---- | ---------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| MQ6  | Purchasing Agent — full LangChain wire   | Backend  | All 4 tools wired. HITL gate blocks dispatch until manager approves. Exponential backoff retry on email failure.               |
| MQ7  | Reorder alerts + agent status UI         | Frontend | Live reorder alert list renders. Agent run status indicators show last run time. Pending PO queue with approve/reject actions. |
| MQ8  | Langfuse alert thresholds + eval metrics | AI/ML    | 4 alert thresholds configured. Precision@5, Faithfulness, Agent Success Rate logged after each run cycle.                      |
| MQ9  | Pytest unit + integration tests          | DevOps   | Prophet model tests: MAE/MAPE on holdout data. Agent tool integration tests. Minimum 80% test coverage on `ai/` and `apps/`.   |
| MQ10 | Agent error handling + 48hr timeout      | Security | Email retry logic tested. 48hr timeout sets PO to `"Pending — Supplier Unresponsive"`. Manager notified via dashboard banner.  |

#### Mawada Alexander

| #    | Task                              | Stack    | Acceptance Criteria                                                                                                                  |
| ---- | --------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| MW6  | OpenAPI docs — drf-spectacular    | Backend  | `/api/docs/` renders Swagger UI. All 30+ endpoints documented with request/response schemas.                                         |
| MW7  | AI chat panel + citation tag UI   | Frontend | ChatPanel displays message history. CitationTag renders `[Source: X, Page: Y]` as clickable badge. Loading skeleton during API call. |
| MW8  | Golden dataset — 30 NL test cases | AI/ML    | 30 annotated queries across 5 categories created. Pytest test reads dataset and asserts correct `action` + `filters`. Runs in CI.    |
| MW9  | Production deployment + HTTPS     | DevOps   | Backend live on Railway with HTTPS. Frontend live on Vercel. All env vars injected via platform. Smoke test passes.                   |
| MW10 | Final security audit              | Security | No hardcoded secrets in repo (confirmed by `grep -r "sk-" .`). HTTPS enforced. CORS + rate limit verified on production URL.         |

---

### 8.4 Definition of Done

A task is **done** when all of the following are true:

- [ ] Code is pushed to a feature branch named `feature/{task-id}-short-description`
- [ ] A Pull Request is opened targeting `main`
- [ ] All CI checks pass (lint + tests + build)
- [ ] At least one other team member has reviewed the PR
- [ ] The PR is merged and the feature branch is deleted
- [ ] `SystemArchitecture.md` and this `PROJECT_BLUEPRINT.md` are updated if the task changed any architecture decision

---

### 8.5 Critical Path & Dependencies

```
Week 1 Dependencies (must complete before Week 2 starts):
  A1 (DB schema) ──► All backend tasks in Week 2
  MQ4 (docker-compose) ──► MA4 (backend Dockerfile) ──► MW4 (frontend Dockerfile)
  O3 (Prophet training) ──► A8 (Forecasting Agent, Week 2)
  MA3 (LangChain chain) ──► MW1 (NL query endpoint) ──► O6 (RAG endpoint, Week 2)
  MW3 (RAG ingestion) ──► O8 (hybrid search, Week 2)

Week 2 Critical Sequence:
  MA6 (Decision Agent tools) ──► MA8 (Decision Agent)
  MA8 (Decision Agent) ──► MQ6 (Purchasing Agent)
  A6 (Purchasing tools) ──► MQ6 (Purchasing Agent)
  A9 (CI) ──► O9 (CD) ──► MW9 (production deploy)
  MW8 (golden dataset) ──► MQ9 (pytest integration) ──► O9 (CD triggers tests)
```

---

### 8.6 Environment Variables Reference

```bash
# .env.example — copy to .env and fill in values

# OpenAI
OPENAI_API_KEY=

# LangChain / LLM
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=

# Langfuse
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# Cohere
COHERE_API_KEY=

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smartstock

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Email (SMTP)
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Cloudinary (file storage for RAG documents)
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Frontend
VITE_API_URL=http://localhost:8000/api
```

> ⚠️ **Never commit `.env` to git. The `.gitignore` must block it. Rotate any key that is ever accidentally exposed.**

---

### 8.7 Remaining Risks & Mitigations

| Risk                                               | Impact                        | Likelihood | Mitigation                                                                                    |
| -------------------------------------------------- | ----------------------------- | ---------- | --------------------------------------------------------------------------------------------- |
| Insufficient historical sales data for Prophet     | High — poor forecast accuracy | Medium     | Fallback to moving average. Seed DB with synthetic data for demo.                             |
| OpenAI API rate limits during demo                 | High — live demo failure      | Low        | Implement Redis response cache for identical queries. Have offline demo screenshots ready.    |
| pgvector HNSW index build time on large corpus     | Medium — slow RAG startup     | Low        | Build index during ingestion, not at query time. Pre-build in Docker entrypoint.              |
| Celery worker not running = no daily agent trigger | High — agents don't fire      | Medium     | Health check endpoint for Celery worker. Alerting if no forecast job ran in 25 hours.         |
| Supplier email marked as spam                      | Medium — PO not received      | Low        | Use transactional email provider (SendGrid). SPF/DKIM configured on sending domain.           |
| Team member unavailability mid-sprint              | Medium — task bottleneck      | Medium     | Cross-stack task design ensures any member can pick up any task. Document all decisions here. |

---

_This blueprint is the single source of truth. Last updated: June 2025._
_All code, tests, and deployment configurations must align with this document._
_When in doubt: Views call Services. Services call Repositories. Repositories call the DB._
