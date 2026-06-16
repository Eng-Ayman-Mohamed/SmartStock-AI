# SmartStock-AI — Comprehensive Bugs & Errors Report

**Date:** June 16, 2026  
**Prepared by:** Omar (automated testing, API testing & code review)

---

## Table of Contents

1. [Test Summary](#test-summary)
2. [CRITICAL Bugs](#critical-bugs)
3. [HIGH Bugs](#high-bugs)
4. [MEDIUM Bugs](#medium-bugs)
5. [LOW Bugs](#low-bugs)
6. [Security Issues](#security-issues)
7. [Configuration Issues](#configuration-issues)
8. [Frontend Bugs](#frontend-bugs)
9. [Hardcoded / Fake Data](#hardcoded--fake-data)

---

## Test Summary

| Test Type | Result |
|-----------|--------|
| Backend Unit/Integration Tests | **1278 passed** / 0 failed |
| Backend Linting (ruff) | 25 warnings (E501 line-too-long) |
| Frontend Linting (eslint) | **0 errors** |
| Frontend Build (tsc + vite) | **Success** |
| API Endpoint Tests | **41 passed** / **18 failed** |

### API Endpoint Test Breakdown

| Category | Passed | Failed | Total |
|----------|--------|--------|-------|
| Auth | 12 | 3 | 15 |
| Inventory | 12 | 6 | 18 |
| Forecasting | 3 | 1 | 4 |
| Purchasing | 9 | 2 | 11 |
| AI/Ingestion | 3 | 5 | 8 |
| Health | 1 | 1 | 2 |
| Audit | 1 | 0 | 1 |
| **Total** | **41** | **18** | **59** |

---

## CRITICAL Bugs

### BUG-01: AI Chat Endpoint Returns 500 — LangChain Template Error

**Endpoint:** `POST /api/ai/chat/`  
**Steps to reproduce:**
```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the total inventory value?"}'
```
**Expected:** 200 with chat response  
**Actual:** 500 Internal Server Error  
**Error message:**
```
LLM Chain failure: 'Input to ChatPromptTemplate is missing variables {'"error"'}. 
Expected: ['"error"', 'few_shot_query'] Received: ['few_shot_query']
```
**Root cause:** `ai/` module has a LangChain `ChatPromptTemplate` with a broken variable reference `{"error"}` that doesn't exist in the chain input.  
**Impact:** AI Chat feature is completely broken.  
**File:** `apps/ingestion/views.py` or `ai/` chain configuration

---

### BUG-02: Forecasting Run Endpoint Returns 500 — DB Connection Error

**Endpoint:** `POST /api/forecasting/run/`  
**Steps to reproduce:**
```bash
curl -X POST http://localhost:8000/api/forecasting/run/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Expected:** 200 with forecast results or 202 if async  
**Actual:** 500 Internal Server Error  
**Error message:** `"Connection closed by server."` (OperationalError)  
**Root cause:** Database or Redis connection is being closed during the forecasting pipeline execution. Likely a connection pool exhaustion or timeout issue.  
**Impact:** Cannot trigger new forecasting runs from the UI.

---

### BUG-03: Readiness Health Check Returns 503

**Endpoint:** `GET /api/health/ready/`  
**Steps to reproduce:**
```bash
curl http://localhost:8000/api/health/ready/
```
**Expected:** 200 with `{"database":"connected","redis":"connected"}`  
**Actual:** 503 with `{"status":"degraded"}`  
**Root cause:** Redis connection check is failing. The Neon PostgreSQL database may be slow/sleeping.  
**Impact:** Docker healthcheck and monitoring systems will report the service as unhealthy.

---

### BUG-04: `prometheus_client` Was Missing — 292 Tests Failed (FIXED)

**File:** `requirements.txt:34`  
**Root cause:** `prometheus-client>=0.20,<0.22` listed in `requirements.txt` but not installed in the virtualenv. This caused `apps/monitoring/metrics.py` to fail on import, cascading into EVERY integration test that makes an HTTP request.  
**Fix applied:** `pip install prometheus-client==0.21.1`  
**Impact:** All 292 integration tests now pass.

---

## HIGH Bugs

### BUG-05: Categories Endpoint is Read-Only (405)

**Endpoint:** `POST /api/inventory/categories/`  
**Steps to reproduce:**
```bash
curl -X POST http://localhost:8000/api/inventory/categories/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Category"}'
```
**Expected:** 201 with created category  
**Actual:** 405 Method Not Allowed  
**Impact:** Categories cannot be created through the API. Users must manually add them in Django admin.

---

### BUG-06: Stock Adjustment Route Returns 405

**Endpoint:** `POST /api/inventory/stock/{product_id}/`  
**Steps to reproduce:**
```bash
curl -X POST http://localhost:8000/api/inventory/stock/1601/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"quantity":5,"reason":"Test adjustment"}'
```
**Expected:** 200 with updated stock  
**Actual:** 405 Method Not Allowed  
**Impact:** Cannot adjust stock through this route. The `adjust-stock` sub-route also only accepts GET.

---

### BUG-07: Missing Inventory Endpoints (404)

**Endpoints returning 404:**
- `GET /api/inventory/stock-adjust/` → 404
- `GET /api/inventory/low-stock/` → 404
- `GET /api/inventory/total-value/` → 404
- `GET /api/inventory/top-products/` → 404

**Correct URLs:**
- Low stock: `/api/inventory/stock-levels/low_stock/` (works)
- Stock adjust: No working POST route
- Total value & top products: No equivalent route found

**Impact:** Frontend or documentation references non-existent URLs.

---

### BUG-08: `GET /api/purchasing/pending-pos/` Returns 404

**Endpoint:** `GET /api/purchasing/pending-pos/`  
**Expected:** Should return pending purchase orders  
**Actual:** 404 Page Not Found  
**Impact:** Dashboard pending PO widget may fail to load data.

---

### BUG-09: AI Ingestion Endpoint Missing (404)

**Endpoint:** `POST /api/ai/ingest/`  
**Expected:** Should accept file upload for document ingestion  
**Actual:** 404 Page Not Found  
**Impact:** Document upload from frontend will fail.

---

### BUG-10: RAG Query Always Times Out (504)

**Endpoint:** `POST /api/ai/rag-query/`  
**Steps to reproduce:**
```bash
curl -X POST http://localhost:8000/api/ai/rag-query/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"What products are low on stock?"}'
```
**Expected:** 200 with query results  
**Actual:** 504 Gateway Timeout — `"Request timed out. Please try a simpler question."`  
**Root cause:** The RAG pipeline (Cohere + vector search) is too slow or the external API is unresponsive.  
**Impact:** AI-assisted inventory queries don't work.

---

### BUG-11: NL Query Endpoint Always Times Out (504)

**Endpoint:** `POST /api/ai/nlquery/`  
**Expected:** 200 with natural language query results  
**Actual:** 504 Gateway Timeout — `"Gateway Timeout: AI pipeline took too long."`  
**Impact:** Natural language inventory queries don't work.

---

### BUG-12: `IllegalPOTransitionError` Missing from Exception Handler (500)

**File:** `config/exception_handler.py:142-148`  
**Root cause:** `IllegalPOTransitionError` (defined in `core/exceptions.py:21`) is raised by `apps/purchasing/services.py:180` but has no mapping in the `STATUS_MAP`. Falls through to default 500.  
**Steps to reproduce:** Try to transition a PO from an illegal state (e.g., approve a `cancelled` PO)  
**Expected:** 409 Conflict  
**Actual:** 500 Internal Server Error  
**Fix:** Add to imports and STATUS_MAP:
```python
from core.exceptions import IllegalPOTransitionError
IllegalPOTransitionError: 409,
```

---

### BUG-13: Docker Compose Uses `development` Settings (DEBUG=True)

**File:** `docker-compose.yml:63,99,131`  
```yaml
DJANGO_SETTINGS_MODULE: config.settings.development
```
All backend containers use `DEBUG = True` in production. Full Django debug pages are exposed on 404 errors, leaking internal URL structure, settings, and stack traces.  
**Impact:** Security risk — exposes internal configuration.

---

## MEDIUM Bugs

### BUG-14: Refresh Token Lifetime Mismatch (3 days vs 7 days)

**Files:** `config/settings/base.py:240` vs `apps/authentication/views.py:117,188`  
```python
# base.py — JWT refresh token expires in 3 days
'REFRESH_TOKEN_LIFETIME': timedelta(days=3),

# views.py — Cookie persists for 7 days
max_age=7 * 24 * 60 * 60,  # 7 days
```
After day 3, the cookie still exists but the JWT is expired. Users get silent logout loops.

---

### BUG-15: Logout Does Not Blacklist JWT

**File:** `apps/authentication/views.py:210-214`  
The logout only deletes the cookie but does NOT blacklist the token. A stolen token remains valid until expiry (15 min for access, 3 days for refresh).

---

### BUG-16: Login Missing Fields Returns 401 Instead of 400/422

**Endpoint:** `POST /api/auth/login/`  
**Steps to reproduce:** Send `{"email":"test@test.com"}` without password  
**Expected:** 400 or 422 with field-level validation errors  
**Actual:** 401 with generic "Invalid email or password."  
**Impact:** Client cannot distinguish between invalid credentials vs missing fields.

---

### BUG-17: Inconsistent Response Envelope Format

**Affected endpoints:**
- `GET /api/auth/me/` → raw object (no envelope)
- `POST /api/auth/logout/` → `{"detail":"..."}` (no envelope)
- All other endpoints → `{"status":"success","data":...,"meta":...}`

**Impact:** Client must handle multiple response formats.

---

### BUG-18: `ForecastDashboardView` Missing Input Validation

**File:** `apps/forecasting/views.py:227-228`  
```python
page = int(request.query_params.get('page', 1))      # ValueError if page=abc
page_size = int(request.query_params.get('page_size', 6))  # ValueError if page_size=xyz
```
No try/except around `int()`. Passing `?page=abc` raises unhandled `ValueError` → 500.

---

### BUG-19: Thread-Safety Issue in `_nl_chain` Initialization

**File:** `apps/inventory/views.py:75-87`  
Classic double-checked locking bug. The lock is created inside the check, so two threads can create separate locks.

---

### BUG-20: `DjangoValidationError` Returns HTTP 409 Instead of 422

**File:** `config/exception_handler.py:122-132`  
Django validation errors return 409 Conflict instead of 422 Unprocessable Entity.

---

### BUG-21: PUT Purchase Orders Require ALL Fields (No Partial Update)

**Endpoint:** `PUT /api/purchasing/orders/{id}/`  
**Steps to reproduce:** Send `{"notes":"Updated"}` to an existing PO  
**Expected:** Partial update — only send changed fields  
**Actual:** 422 requiring `quantity`, `total_cost`, `sku`, `supplier`  
**Impact:** Cannot update individual fields; must send complete object every time.

---

### BUG-22: `max_warehouse_capacity` Silently Ignored on Update

**Endpoint:** `PUT /api/inventory/products/{id}/`  
**Steps to reproduce:** PUT with `{"max_warehouse_capacity": 200, ...other required fields}`  
**Expected:** Field updated to 200  
**Actual:** Field stays at default value (1000)  
**Impact:** Warehouse capacity cannot be configured through the API.

---

### BUG-23: AI `/nlquery/` Field Name Mismatch

**Endpoint:** `POST /api/ai/chat/`  
**Expected:** Accept `message` field (as documented)  
**Actual:** Returns 422 `"query":["This field is required."]` when sending `{"message":"..."}`  
**Impact:** Field naming inconsistency between documentation and implementation.

---

### BUG-24: `RAGQueryView` Returns Raw Exception Messages

**File:** `apps/ingestion/views.py:363-368`  
Raw `str(e)` in error responses can leak internal details (DB connection strings, file paths, API keys).

---

### BUG-25: Production `SECURE_SSL_REDIRECT = False`

**File:** `config/settings/production.py:7`  
Disables HTTPS redirect in production.

---

### BUG-26: `_invalidate_product_cache` Uses `cache.delete_pattern`

**File:** `apps/inventory/services.py:26`  
`delete_pattern` is django-redis specific. If cache backend changes, this raises `AttributeError`.

---

## LOW Bugs

### BUG-27: Register Duplicate Email Has Empty Message

**Endpoint:** `POST /api/auth/register/` (duplicate email)  
**Expected:** 409 with message "A user with this email already exists"  
**Actual:** 409 with empty `message` field

---

### BUG-28: Refresh Token Error Says "cookies" but Token Sent in Body

**Endpoint:** `POST /api/ai/refresh/`  
Message says "Refresh token not found in cookies." even when sending via JSON body.

---

### BUG-29: Optional Env Vars Logged Without Masking

**File:** `config/validators.py:53-55`  
`EMAIL_HOST_PASSWORD` and `CLOUDINARY_URL` are logged in plain text.

---

### BUG-30: `NLQueryEndpointView._run_pipeline` Returns Response Inside Thread

**File:** `apps/inventory/views.py:1416-1418`  
DRF `Response` objects are created in a different thread than the Django request thread.

---

### BUG-31: `DocumentViewSet.create` Creates Orphaned Records on Ingestion Failure

**File:** `apps/ingestion/views.py:208-226`  
If PDF ingestion fails, the `Document` record remains in DB with `total_chunks=0`.

---

### BUG-32: Inconsistent HTTP Status Codes for DELETE

- `DELETE /api/purchasing/orders/` → 204 (No Content)
- `DELETE /api/auth/users/` → 200 with body (soft delete)
- `DELETE /api/inventory/products/` → 204 (No Content)

---

## Security Issues

### SEC-01: Refresh Token Stored in `sessionStorage` (XSS-Vulnerable)

**Files:** `src/store/authStore.ts:46-57` + `src/lib/axios.ts:116-128`  
Backend sets refresh token as HttpOnly cookie, but frontend also stores it in `sessionStorage`, negating the cookie's security benefit.

---

### SEC-02: `ALLOWED_HOSTS = '*'` in `.env`

**File:** `smartstock-backend/.env:5`  
Wildcard allows any Host header, enabling HTTP Host header attacks.

---

### SEC-03: DEBUG=True Exposes Full Error Pages

404 errors return full Django debug page with URL patterns and server configuration. **FIXED:** Docker compose still uses `development` settings.

---

### SEC-04: Real API Keys in `.env` (Local Only)

**File:** `smartstock-backend/.env:8-12`  
Contains real OpenAI, Cohere, Langfuse, Cloudinary keys. Not committed to git (`.gitignore`), but should be rotated if repo was ever shared.

---

## Configuration Issues

### CONFIG-01: `.env` Frontend Missing `/api` Prefix (FIXED)

**File:** `smartstock-frontend/.env`  
**Before:** `VITE_API_URL=http://127.0.0.1:8000`  
**After:** `VITE_API_URL=/api`  
Missing `/api` prefix caused all API calls to hit wrong URL (404). Now routes through Vite proxy.

---

### CONFIG-02: Docker Healthcheck Hits Liveness, Not Readiness

**File:** `docker-compose.yml:71`  
Healthcheck hits `/api/health/` (always 200) instead of `/api/health/ready/` (checks DB/Redis).

---

## Frontend Bugs

### FE-01: Duplicate `pending-pos` Query Keys — Cross-Feature Cache Corruption

**Files:** `src/features/dashboard/hooks/usePendingPOs.ts:9` + `src/features/purchasing/hooks/usePurchasing.ts:5,10`  
Both use `['pending-pos']` but fetch from different endpoints with different response shapes. React-Query serves stale data from wrong endpoint.

---

### FE-02: `Array.sort()` Mutates Props in AlertSidebar

**File:** `src/features/forecasting/components/AlertSidebar.tsx:87`  
`alerts.sort()` mutates the React-Query cache directly. Sort comparator only takes one argument.

---

### FE-03: No Error Boundaries — Any Render Crash Kills the App

No `ErrorBoundary` components exist. If any component throws during render, the entire app shows a white screen.

---

### FE-04: Lazy Routes Without Error Handling

**File:** `src/lib/router.tsx:8-18`  
No `onError` handler for failed chunk loads. Network drop during lazy load → blank screen.

---

### FE-05: `setState` During Render

**Files:** `src/features/purchasing/pages/SuppliersPage.tsx:163` + `src/features/users/pages/UsersSettingsPage.tsx:55`  
Causes unnecessary double-renders.

---

### FE-06: Hardcoded Dashboard Stats

**File:** `src/features/dashboard/pages/DashboardPage.tsx:231,248`  
```tsx
<StatCard label="Total SKUs" value="1,247" ... />
<StatCard label="Forecast Accuracy" value="87.4%" ... />
```
These values never update from the API.

---

### FE-07: Hardcoded AI Assistant & PO History Data

**Files:** `src/features/ai-assistant/pages/AIAssistantPage.tsx:23-42`, `src/features/purchasing/pages/PurchasingPage.tsx:27-31`

---

## Fixed Issues (This Session)

| Issue | Fix |
|-------|-----|
| `prometheus_client` not installed | `pip install prometheus-client==0.21.1` |
| 1 unapplied migration | `python manage.py migrate` |
| Backend server won't start | Fixed by installing prometheus_client |
| Frontend `.env` missing `/api` prefix | Changed to `VITE_API_URL=/api` |
| No test user for Omar | Created `omarwaelkishk@gmail.com` (admin) |
