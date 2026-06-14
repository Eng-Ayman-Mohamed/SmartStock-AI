# SmartStock AI — Integration Audit Report

**Date:** 2026-06-15  
**Scope:** Frontend↔Backend integration surfaces across all layers  
**Auditors:** 8 parallel sub-agents (API Contract, Auth, Envelope, CORS/Proxy, Config Drift, Types, Build Pipeline, UX States)  
**Delivery-Readiness Score: 33/100**

---

## Executive Summary

58 issues found across 8 audit dimensions. The application functions in development (Vite proxy + local Django) and Docker Compose, but is **not ready for production delivery** due to 3 blocker issues that cause complete failure in cross-origin deployments (Vercel + Railway).

**Top 3 blockers:**
1. Production API routing broken — axios baseURL hardcoded to `/api` with no proxy/rewrite
2. `SameSite=Strict` blocks refresh cookie cross-origin — users silently logged out every 15min
3. Docker Compose missing `OPENAI_API_KEY` / `COHERE_API_KEY` — all AI features fail

### Severity Distribution

```
Blocker   ████  3
Critical  ███████████████  10
Major     ██████████████████████████████████  23
Minor     ██████████████████████████████  20
Info      ███  2
Total                     58
```

### Score by Audit Area

| Area | Weight | Score | Contribution |
|------|--------|-------|-------------|
| API Contract Verification | 20% | 45/100 | 9.0 |
| Auth Flow & Token Chain | 15% | 35/100 | 5.3 |
| Response Envelope & Error Handling | 10% | 40/100 | 4.0 |
| CORS, Proxy & Deployment Routing | 10% | 25/100 | 2.5 |
| Environment & Config Drift | 15% | 20/100 | 3.0 |
| Type & Model Alignment | 10% | 30/100 | 3.0 |
| Docker & Build Pipeline | 10% | 35/100 | 3.5 |
| Loading/Error/Empty State Coverage | 10% | 30/100 | 3.0 |
| **Weighted Total** | **100%** | — | **33.3/100** |

---

## Table of Contents

1. [🔴 Blocker Issues](#1--blocker-issues)
2. [🟠 Critical Issues](#2--critical-issues)
3. [🟡 Major Issues](#3--major-issues)
4. [🔵 Minor Issues](#4--minor-issues)
5. [Appendix A: Per-Task Detailed Findings](#appendix-a-per-task-detailed-findings)
6. [Appendix B: Remediation Roadmap](#appendix-b-remediation-roadmap)

---

## 1. 🔴 Blocker Issues (3)

### B1 — Production API routing broken (no proxy, no env var consumption)

| Field | Value |
|-------|-------|
| **Files** | `smartstock-frontend/src/lib/axios.ts:28`, `smartstock-frontend/Dockerfile`, missing `vercel.json` |
| **Task** | CORS/Proxy/Deployment |
| **Description** | axios instance hardcodes `baseURL: '/api'` which resolves to same origin as frontend. In Vercel production (`https://smart-stock-dev.vercel.app`), API calls hit `https://smart-stock-dev.vercel.app/api/...` but backend runs on Railway. No `vercel.json` rewrite exists. `.env.example` documents `VITE_API_URL` but zero code reads `import.meta.env.VITE_API_URL` or `window.__ENV__`. |
| **Evidence** | `axios.ts:28`: `baseURL: '/api'`. `grep VITE_API_URL src/` → 0 results. `vercel.json` → file does not exist. `docker-entrypoint.sh` writes `window.__ENV__` but no code reads it. |
| **Suggested fix** | Option A: Make axios read `import.meta.env.VITE_API_URL \|\| '/api'`. Option B: Create `vercel.json` with rewrites to Railway backend. |

---

### B2 — SameSite=Strict blocks refresh cookie in cross-origin production

| Field | Value |
|-------|-------|
| **Files** | `smartstock-backend/config/settings/base.py:200`, `apps/authentication/views.py:114,183` |
| **Task** | Auth Flow |
| **Description** | Refresh token cookie set with `SameSite='Strict'` in three places. Browser will never send the cookie on cross-site requests. In Vercel→Railway topology (different registrable domains), `POST /api/auth/refresh/` with `withCredentials: true` arrives without the cookie → backend returns 400 → frontend `clearAuth()` → user silently logged out every 15min. Works in dev/Docker because Vite/Nginx proxies make all requests same-origin to the browser. |
| **Evidence** | `views.py:114,183`: `samesite='Strict'` in `set_cookie`. `base.py:200`: `'AUTH_COOKIE_SAMESITE': 'Strict'`. `serializers.py:37-38`: reads from `request.COOKIES` — empty cross-origin. |
| **Suggested fix** | Option A (cross-origin): Change to `SameSite='None'` with `Secure=True`. Option B (same-origin): Use Vercel rewrites so all API calls appear same-origin. |

---

### B3 — Docker Compose missing OPENAI_API_KEY and COHERE_API_KEY

| Field | Value |
|-------|-------|
| **Files** | `docker-compose.yml:46-71`, root `.env`, `config/validators.py:6-12` |
| **Task** | Config Drift |
| **Description** | Root `.env` does not contain `OPENAI_API_KEY` or `COHERE_API_KEY`. Backend `environment` block in docker-compose also does not set them. `config/validators.py` lists both as **required**. The `try/except` at `base.py:251-257` catches the `ImproperlyConfigured` error and only logs a warning, so the backend boots — but any code path using AI features (NL queries, document ingestion, forecasting, agents) will fail at runtime. |
| **Evidence** | Root `.env` has no AI keys. `docker-compose.yml` backend environment sets DB/REDIS/CELERY vars but not AI keys. `validators.py:7-8`: both in `REQUIRED_ENV_VARS`. `apps/ingestion/services.py:385-387`: `os.getenv('COHERE_API_KEY')` raises `ConnectionError`. `ai/multimodal/vision.py:23`: `os.getenv('OPENAI_API_KEY')` with no default → `None` → crash. |
| **Suggested fix** | Add `OPENAI_API_KEY` and `COHERE_API_KEY` to root `.env` and to `docker-compose.yml` backend `environment`. |

---

## 2. 🟠 Critical Issues (10)

### C1 — `listSuppliers()` envelope mismatch returns pagination object

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/purchasing/api.ts:6-8` |
| **Task** | API Contract |
| **Description** | Frontend expects `{status, data: Supplier[]}` envelope, backend `SupplierViewSet` returns paginated `{count, next, previous, results}`. The axios interceptor only unwraps `{status: 'success', data}` envelopes. `data.data` is `undefined`, fallback `data` returns the full pagination object. |
| **Suggested fix** | Access `data.results`: `const { data } = await api.get<{ results?: Supplier[] }>('/purchasing/suppliers/'); return data.results ?? [];` |

---

### C2 — `listPendingPOs()` envelope mismatch always returns empty `[]`

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/purchasing/api.ts:37-41` |
| **Task** | API Contract |
| **Description** | Same root cause as C1. Backend `PurchaseOrderViewSet.list` returns paginated `{count, next, previous, results}`. `data.data` is `undefined`, `items = data.data ?? []` = `[]`. **The list will always appear empty.** |
| **Suggested fix** | `const items = data.results ?? [];` |

---

### C3 — `GET /inventory/products/` pagination causes `.flatMap()` crash

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/inventory/pages/InventoryPage.tsx:261` |
| **Task** | API Contract |
| **Description** | The `unwrap()` helper at line 62-66 only checks for `{data: T}` envelope, NOT DRF's `{results: T[]}`. Backend `ProductViewSet.list` returns paginated response with `results` key. `data.products` is `{count, next, previous, results}`, not an array. Calling `.flatMap()` on it at line 261 throws `TypeError: data.products.flatMap is not a function`. |
| **Suggested fix** | Extend `unwrap` to handle `results` key: `if ('results' in payload && Array.isArray((payload as any).results)) return (payload as any).results;`. At minimum access `data.results` before calling array methods. |

---

### C4 — `sendChatMessage()` double-unwrap returns `undefined`

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/ai-assistant/api.ts:16` |
| **Task** | API Contract |
| **Description** | Axios interceptor unwraps `{status: 'success', data: ChatResponse}` → `ChatResponse`. Then `sendChatMessage` accesses `data.data` on the already-unwrapped result — always `undefined`. The chat assistant will never receive responses. |
| **Suggested fix** | `return data;` instead of `return data.data;` |

---

### C5 — Two `.env` files with completely divergent configuration

| Field | Value |
|-------|-------|
| **Files** | root `.env` vs `smartstock-backend/.env` |
| **Task** | Config Drift |
| **Description** | Root `.env` (loaded by docker-compose): 9 lines, DB points to Docker postgres, no AI keys, no Cloudinary. Backend `.env` (loaded by `manage.py` via `load_dotenv()`): 8 lines, DB points to Neon production, has `OPENAI_API_KEY`, `CI=True`. Same `docker compose up` and `python manage.py runserver` load radically different configurations. |
| **Suggested fix** | Unify into single `.env` at root. Remove `smartstock-backend/.env`. Ensure both Docker and `manage.py` read from same source. |

---

### C6 — `VITE_API_URL` and `window.__ENV__` are dead infrastructure

| Field | Value |
|-------|-------|
| **Files** | `smartstock-frontend/.env.example:12`, `docker-entrypoint.sh:6`, `src/lib/axios.ts:28` |
| **Task** | Config Drift |
| **Description** | Three related issues: (1) `.env.example` documents `VITE_API_URL` but no code reads it. (2) `.env` and `.env.local` define different vars with different values. (3) `docker-entrypoint.sh` writes runtime env to `window.__ENV__` but zero code reads `window.__ENV__`. All this infrastructure — the entrypoint script, the injection pattern, `env-config.js` — is dead code. |
| **Suggested fix** | Either make axios read `import.meta.env.VITE_API_URL \|\| '/api'` and remove `docker-entrypoint.sh`, or keep the runtime injection and make axios read `window.__ENV__.VITE_API_URL`. Pick one. |

---

### C7 — DashboardPage missing page-level loading/error states

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/dashboard/pages/DashboardPage.tsx:140-143` |
| **Task** | UX States |
| **Description** | Page destructures data from 4 hooks but never checks `isLoading` or `isError` at page level. During loading, stat cards flash "0" counts. On error, they silently show zeros. Child components handle their own states, but the stat cards and chart header are unprotected. |
| **Suggested fix** | Add page-level loading guard (skeleton layout for stat cards) and error fallback. Destructure `isLoading`/`isError` from each hook. |

---

### C8 — PurchasingPage shows mock data as real data during loading

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/purchasing/pages/PurchasingPage.tsx:59` |
| **Task** | UX States |
| **Description** | `const pendingPOs = isPendingLoading ? mockPendingPOs : (pendingPOsData ?? []);` — during loading, real-looking mock data ("Wireless Mouse", "Mechanical Keyboard") is shown. Users could mistake these for real pending orders, potentially acting on fake data. |
| **Suggested fix** | Replace with `Skeleton` components during loading. Keep mock data for development only. |

---

### C9 — UsersTable silent mutation failures

| Field | Value |
|-------|-------|
| **File** | `smartstock-frontend/src/features/users/components/UsersTable.tsx:76,118` |
| **Task** | UX States |
| **Description** | Role updates via `updateRole.mutate()` and deactivations via `deactivate.mutate()` have no success or error feedback. No toast, no inline message, no console warning. If a role change fails on the server, the user sees nothing — the UI silently stays the same. |
| **Suggested fix** | Add `onSuccess`/`onError` callbacks to both mutations with toast notifications. |

---

### C10 — InvoiceScanResult.scan_id vs backend id — field name mismatch

| Field | Value |
|-------|-------|
| **Files** | `smartstock-frontend/src/features/invoice-scan/types.ts:14`, backend `ingestion/serializers.py:108` |
| **Task** | Types |
| **Description** | Frontend expects field named `scan_id` but backend `InvoiceScanSerializer` emits `id`. Unless a view transformation renames it, every invoice scan response will have `scan_id === undefined`. The input side (`ConfirmInvoicePayload` sends `scan_id`) is correct — only the output side is wrong. |
| **Suggested fix** | Add `scan_id = SerializerMethodField()` to serializer that returns `id`, or rename frontend field to `id`. |

---

## 3. 🟡 Major Issues (23)

### API Contract (4)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M1 | `fetchAgentRuns()` — DRF pagination returns `{count,next,previous,results}`, frontend expects array | `dashboard/api.ts:12` | Access `data.results` |
| M2 | `fetchPendingPOs()` — same DRF pagination mismatch | `dashboard/api.ts:20` | Access `data.results` |
| M3 | Duplicate chat functions: `sendChatMessage` (broken) + `sendChat` (working) | `ai-assistant/api.ts:11-27` | Remove one, keep canonical |
| M4 | Hardcoded `confidence_score: 85` ignores backend computation | `forecasting/hooks/useForecastDashboard.ts:53` | Use backend value with fallback |

---

### Auth Flow (2)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M5 | `AUTH_COOKIE_SECURE` reads `os.environ` instead of `settings.DEBUG` | `base.py:199` | Use `not settings.DEBUG` or set in production.py |
| M6 | No `CORS_ALLOW_CREDENTIALS` in dev settings | `development.py` | Add `CORS_ALLOW_CREDENTIALS = True` to base.py |

---

### Response Envelope (3)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M7 | `RegisterForm` ignores wrapped validation error envelope — reads `data.name` instead of `data.fields.name` | `RegisterForm.tsx:60-73` | Check `fields` sub-object first |
| M8 | `toAuthError` doesn't handle 422 → always returns generic "unknown" | `useAuth.ts:10-21` | Add 422 handler for validation errors |
| M9 | `confirmDelete` reads `data.detail` instead of `data.message` | `SuppliersPage.tsx:122-126` | Change to `data.message` |

---

### CORS/Proxy (1)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M10 | Nginx `location /api/` doesn't match `/api` (no trailing slash) — falls through to SPA | `nginx.conf:11-17` | Add `location = /api { return 302 /api/; }` or use regex match |

---

### Config Drift (5)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M11 | `VITE_AUTH_BYPASS` defined in `.env.example` and `docker-compose.yml` but never consumed | `.env.example:22`, `docker-compose.yml:149` | Implement auth bypass or remove |
| M12 | `cloudinary` duplicated in `requirements.txt` with different pins | `requirements.txt:2,30` | Remove duplicate, keep single pin |
| M13 | `pydantic` is transitive-only dependency — 8 files import it but it's not in `requirements.txt` | `ai/` layer (8 files) | Add `pydantic>=2.0,<3.0` to `requirements.txt` |
| M14 | `CI=True` in backend `.env` silences all env var validation | `smartstock-backend/.env:8` | Remove `CI=True` from committed env file |
| M15 | Python 3.12 + `prophet` build compatibility risk — slim image lacks build deps | `Dockerfile`, `requirements.txt` | Switch to full `python:3.12` or add build deps |

---

### Type Alignment (7)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M16 | `authStore.User` missing `is_active` from `MeSerializer` | `authStore.ts:6-11` | Add `is_active?: boolean` |
| M17 | `Product` inline type missing 8 backend fields (`unit_price`, `unit_of_measure`, `is_active`, etc.) | `InventoryPage.tsx:32-41` | Add all serializer fields |
| M18 | `LowStockItem` missing 4 backend fields (`product_id`, `reorder_quantity`, `supplier_name`, `predicted_stockout_date`) | `InventoryPage.tsx:52-58` | Add missing fields |
| M19 | `PendingPO.id` is `string` (prefixed `PO-42`) but backend `id` is `int` — broke approve/reject | `purchasing/types.ts:25` | Keep `id: number`, format display separately |
| M20 | `POHistory` inline type has wrong field names (`product` vs `product_name`, `qty` vs `quantity`, `total` vs `total_cost`) | `PurchasingPage.tsx:29-38` | Align with backend serializer or remove mock |
| M21 | `InvoiceScanResult` missing 7 backend fields (`original_filename`, `content_type`, `file_size`, timestamps) | `invoice-scan/types.ts` | Add missing fields |
| M22 | No shared PO status enum — frontend uses `string` everywhere, mock data uses capitalized values | `dashboard/types.ts:33` | Create union type matching backend 11-value enum |

---

### Build Pipeline (5)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M23 | No `.dockerignore` for frontend — `node_modules/`, `.git/`, `dist/` included in build context | `smartstock-frontend/` | Create `.dockerignore` |
| M24 | `collectstatic` never called — admin static files will 404 | `Dockerfile`, `entrypoint.sh` | Add `collectstatic --noinput` step |
| M25 | `nginx.conf` missing `client_max_body_size` — file uploads >1MB return 413 | `nginx.conf` | Add `client_max_body_size 10M;` |
| M26 | `noUnusedLocals` + `noUnusedParameters: true` — any unused import breaks `npm run build` | `tsconfig.app.json:19-20` | Set both to `false`, rely on ESLint for warnings |
| M27 | CI missing `makemigrations --check --dry-run` — model changes without migrations pass CI | `.github/workflows/ci.yml` | Add migration check step |

---

### UX States (4)

| ID | Issue | File | Fix |
|----|-------|------|-----|
| M28 | `SupplierWarningBadge` — silent failure (loading and error both return `null`) | `SupplierWarningBadge.tsx:7-9` | Show skeleton on loading, muted warning on error |
| M29 | `PendingPOQueue` — generic mutation error, no retry button | `PendingPOQueue.tsx:101-102` | Show actual server error, add "Try again" button |
| M30 | `AgentRunStatus` — no retry button on error | `AgentRunStatus.tsx:64-65` | Add inline "Try again" calling `refetch()` |
| M31 | `InvoiceScanPage` — reject catch block is empty `return`, user gets no feedback | `InvoiceScanPage.tsx:207-208` | Add error toast or inline banner |

---

## 4. 🔵 Minor Issues (20)

### API Contract (5)
- `LoginResponse` includes unused `refresh?: string` field (backend never returns it in body)
- Register returns 201, frontend doesn't differentiate from 200 (harmless)
- Logout sends redundant `withCredentials: true`
- Overdue suppliers OpenAPI schema outdated (documents `integer` for `overdue_pos`, actual is array)
- `fetchOverdueSuppliers()` and `listUsers()` handle pagination correctly (good, but noted as fragile patterns)

### Auth Flow (5)
- Refresh interceptor uses global axios with hardcoded path instead of `api` instance
- `User` type omits `is_active` from `MeSerializer`
- Logout cookie name reads non-existent `settings.REFRESH_TOKEN_COOKIE_NAME`
- Empty catch in `bootstrapSession` swallows actionable errors
- Refresh endpoint returns 400 for missing cookie (should be 401)

### Envelope (3)
- Validation error envelope missing `code` field
- `data.pop('results')` mutates input dict in renderer
- `UserListCreateView` envelope_exempt creates dual pagination format

### CORS/Proxy (4)
- Vite proxy lacks X-Forwarded-* header forwarding (dev vs Docker inconsistency)
- Railway runs migrations twice (entrypoint.sh + startCommand)
- CSRF middleware active but unused — latent risk if SameSite is relaxed
- Backend no explicit healthcheck in Docker Compose service definition

### Config Drift (2)
- `CORS_ALLOWED_ORIGINS` drift between base.py default and docker-compose
- `CSRF_TRUSTED_ORIGINS` not set for development settings

### Build Pipeline (7)
- CI Node.js version (20) doesn't match Docker (22)
- Docker compose backend volume mount overrides `appuser` permissions
- Monitoring config files not guarded for presence
- `entrypoint.sh` `pg_isready -d` with full URI is fragile
- Backend `COPY . .` before `chown` adds image bloat layer
- No frontend build smoke test in CI

### UX States (4)
- `InventoryPage` no retry button on query error
- `SuppliersPage` no retry button on query error
- `ProfilePage` missing loading guard for `isBootstrapping`
- `PurchasingPage` `isError` + empty state render simultaneously (contradictory messaging)

---

## 5. Appendix A: Per-Task Detailed Findings

### Task 1 — API Contract Verification

12 endpoints audited. 13 issues found.

**Endpoints checked:**
- `src/features/auth/api.ts` — login, register, logout, me ✅ (1 minor)
- `src/features/dashboard/api.ts` — low stock, agent runs, POs, overdue suppliers ⚠️ (2 major, 1 minor)
- `src/features/ai-assistant/api.ts` — chat, RAG, transcribe ⚠️ (1 critical, 1 major)
- `src/features/users/api.ts` — list, create, update, deactivate ✅
- `src/features/purchasing/api.ts` — suppliers, POs, approve/reject ⚠️ (2 critical, 1 major)
- `src/features/invoice-scan/api.ts` — scan, confirm, reject ✅
- `src/features/forecasting/hooks/useForecastDashboard.ts` — dashboard endpoint ⚠️ (1 minor)
- `src/store/authStore.ts` — bootstrap refresh + me ✅
- `src/features/inventory/pages/InventoryPage.tsx` — products, low stock, stock adjust ⚠️ (1 critical, 1 major)

---

### Task 2 — Auth Flow & Token Chain

9 issues found. One blocker (SameSite), one major (cookie secure flag), rest minor.

**Flow verified:** Login → Register → Token attachment → 401 refresh (queue) → Bootstrap → Logout → Roles. Cookie config, CORS credentials, edge cases all checked.

---

### Task 3 — Response Envelope & Error Handling

9 issues found. One critical (register form validation parsing), rest major/minor/info.

**Envelope format:**
```
Backend success: {status: "success", data: T, meta: {...}}
Backend error:   {status: "error", error: "Type", message: "...", code: NNN}
Frontend:        Interceptor unwraps success, creates ApiResponseError for errors
```

Key inconsistency: Auth views use `envelope_exempt = True` (raw DRF responses), all other views use envelope. Frontend handles both inconsistently.

---

### Task 4 — CORS, Proxy & Deployment Routing

8 issues found. One blocker (production routing), one critical (SameSite), two major (CORS credentials, nginx trailing slash).

**Environment routing matrix:**

| Environment | Frontend → Backend | Same-origin? | Works? |
|-------------|-------------------|--------------|--------|
| Dev (Vite) | `localhost:5173` → Vite proxy → `localhost:8000` | Yes (proxy) | ✅ |
| Docker | Nginx on :80 → `http://backend:8000` | Yes (same container network) | ✅ |
| Production (Vercel+Railway) | `vercel.app` → ? → `railway.app` | No | ❌ B1 |

---

### Task 5 — Environment & Config Drift

16 issues found. One blocker (AI keys), 2 critical (dead env infrastructure, dual .env files), 5 major.

**Key config file map:**

```
Root .env (9 vars)              ← docker-compose loads this
  ├── Missing: OPENAI_API_KEY, COHERE_API_KEY, CLOUDINARY_URL
  └── Has: basic Django, DB, Redis

smartstock-backend/.env (8 vars)  ← manage.py loads this
  ├── Has: OPENAI_API_KEY (production), CI=True
  ├── Missing: COHERE_API_KEY, CLOUDINARY_URL
  └── DB points to Neon, not Docker postgres

Expected (from validators.py):
  REQUIRED: OPENAI_API_KEY, COHERE_API_KEY, DJANGO_SECRET_KEY, DATABASE_URL, REDIS_URL
```

---

### Task 6 — Type & Model Alignment

28 type pairs checked. 1 critical (scan_id vs id), 7 major, 11 minor. 8 pairs aligned correctly.

**Best aligned:** Invoice field keys, invoice status, chat modes, forecast day shape, user admin types, dashboard agent runs, overdue suppliers.

**Worst aligned:** Inventory Product (missing 8 fields), InvoiceScanResult (missing 7 fields + wrong primary key name), Purchasing POHistory (all field names wrong).

---

### Task 7 — Docker & Build Pipeline

14 issues found. 5 major, 9 minor.

**Docker Compose service health:**

| Service | Health Check | Status |
|---------|-------------|--------|
| PostgreSQL | `pg_isready` | ✅ |
| Redis | `redis-cli ping` | ✅ |
| Backend | Inherits Dockerfile HEALTHCHECK (python HTTP) | ✅ (fragile) |
| Celery Worker | `celery inspect ping` | ✅ |
| Celery Beat | Python `/proc` parsing | ❌ M3 — broken |
| Frontend | `wget http://localhost:80/` | ✅ |

---

### Task 8 — Loading/Error/Empty State Coverage

16 components checked. 3 critical, 4 major, 4 minor.

**State coverage summary:**

```
Components with all 3 states:  10/16 (62%)
Components missing 1+ states:   6/16 (38%)
Components with retry button:    2/16 (12%)
```

---

## 6. Appendix B: Remediation Roadmap

### Phase 1 — Immediate (Blocker fixes, ~2 hours)

| Order | Issue | Effort | Owner |
|-------|-------|--------|-------|
| 1 | B1: Fix axios baseURL to read env var | 15min | Frontend |
| 2 | B1: Create vercel.json with rewrites OR add runtime env consumption | 30min | DevOps |
| 3 | B2: Fix SameSite for production (None + Secure) | 15min | Backend |
| 4 | B3: Add OPENAI_API_KEY + COHERE_API_KEY to Docker Compose | 10min | DevOps |
| 5 | B3: Add missing AI keys to root `.env` | 5min | All |

### Phase 2 — Today (Critical runtime bugs, ~4 hours)

| Order | Issue | Effort | Owner |
|-------|-------|--------|-------|
| 6 | C1, C2, C3: Fix pagination envelope in purchasing & inventory APIs | 1h | Frontend |
| 7 | C4: Fix sendChatMessage double-unwrap | 15min | Frontend |
| 8 | C5: Unify .env files | 30min | DevOps |
| 9 | C6: Fix or remove dead env infrastructure | 30min | Frontend |
| 10 | C7, C8, C9: Fix missing loading/error states | 1.5h | Frontend |

### Phase 3 — This Sprint (Major issues, ~8 hours)

| Order | Issues | Effort | Owner |
|-------|--------|--------|-------|
| 11 | M1, M2: Fix dashboard pagination | 30min | Frontend |
| 12 | M5, M6: Fix auth cookie config | 30min | Backend |
| 13 | M7, M8, M9: Fix error handling in forms | 1h | Frontend |
| 14 | M10: Fix nginx trailing-slash routing | 15min | DevOps |
| 15 | M11-M15: Fix config drift issues | 1h | Backend |
| 16 | M16-M22: Align frontend types with backend serializers | 2h | Frontend |
| 17 | M23-M27: Fix build pipeline | 1h | DevOps |
| 18 | M28-M31: Add missing UX states | 1h | Frontend |

### Phase 4 — Backlog (Minor issues, ongoing)

All 20 minor issues are non-blocking but should be tracked. Key areas:
- Clean up dead code (`tailwind.config.ts`, stale types, mock data)
- Add retry buttons to all error states
- Align CI Node version with Docker
- Add build smoke test

---

## Remediation Estimate

| Phase | Effort | Issues Fixed | Score After |
|-------|--------|-------------|-------------|
| Phase 1 | ~2h | 3 blocker | 45/100 |
| Phase 2 | ~4h | 10 critical | 65/100 |
| Phase 3 | ~8h | 23 major | 85/100 |
| Phase 4 | ongoing | 20 minor | 90+/100 |

**Target: 14 hours to reach 85/100 delivery-readiness.**
