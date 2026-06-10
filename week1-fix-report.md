# SmartStock AI — Week 1 Fix Report

> **Generated:** 2026-06-10  
> **Source:** Cross-referenced `tasks_assignment.md` against codebase + three audit models  
> **Purpose:** Single authoritative list of what needs fixing, ordered by impact  

---

## Priority 1 — Blocking / Critical

### P1.1 [MW3] RAG Document Upload Pipeline — NOT BUILT

**Files affected:** `apps/ingestion/` (models.py), `ai/rag/ingestion.py`

**What's wrong:** REST endpoints don't exist, DOCUMENT model doesn't exist, Cloudinary not integrated.

**Fix steps:**

1. **Create `Document` model** in `apps/ingestion/models.py`:
```python
class Document(models.Model):
    filename = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    file_size = models.IntegerField()
    total_chunks = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    cloudinary_url = models.URLField(max_length=1000)
```
2. **Add `document` FK to `DocumentChunk`** (currently no parent link).
3. **Create `POST /api/ai/documents/upload/`** in `apps/ingestion/views.py` — multipart PDF upload, validate magic bytes (`b'%PDF'`), validate size ≤ 10MB, upload to Cloudinary via `cloudinary.uploader.upload()`, run ingestion pipeline.
4. **Create `GET /api/ai/documents/`** — paginated list with chunk counts, `GET /api/ai/documents/{id}/` — single doc detail.
5. **Create `DELETE /api/ai/documents/{id}/`** — Admin-only, soft delete (`is_active=False`), deactivate chunks.
6. **Add `CLOUDINARY_URL`** → `requirements.txt`, `settings/base.py`, `.env.example`.
7. **Wire URLs** — create `apps/ingestion/urls.py`, include in root `urls.py`.

---

### P1.2 [MA3 + MQ3] `tool_choice: "required"` — NOT IMPLEMENTED

**File:** `smartstock-backend/ai/llm/chain.py`

**What's wrong:** Chain uses `StrOutputParser` + prompt-based JSON. Task requires OpenAI function calling via `llm.bind_tools([nl_query_schema], tool_choice="required")`.

**Fix:** Replace the prompt-based output approach:
```python
from langchain_core.pydantic_v1 import BaseModel, Field

class NLQueryToolSchema(BaseModel):
    action: str = Field(description="Action enum value")
    filters: Optional[dict] = None
    sort: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

llm_with_tools = llm.bind_tools([NLQueryToolSchema], tool_choice="required")
chain = prompt | llm_with_tools | output_parser
```

---

### P1.3 [MA3] NLQueryChain Instantiated Per Request

**File:** `smartstock-backend/apps/inventory/views.py:558`

**What's wrong:** `chain_instance = NLQueryChain()` is called inside every POST request handler. Creates new ChatOpenAI + prompt + parser each time.

**Fix:** Make it a module-level singleton:
```python
_nl_chain = None

def get_nl_chain():
    global _nl_chain
    if _nl_chain is None:
        from ai.llm.chain import NLQueryChain
        _nl_chain = NLQueryChain()
    return _nl_chain
```

---

### P1.4 [MA3 + MQ3] Missing Few-Shot Examples

**File:** `smartstock-backend/ai/llm/few_shots.py`

**What's wrong:** Only 7 examples exist (need 10 per MA3 task). Missing:
- Multi-condition query (stock below X AND name starts with Y)
- List filter (from Supplier A or B)
- Combined filters with sort

**Fix:** Add 3 more examples to `FEW_SHOT_EXAMPLES` list.

---

### P1.5 [MA1] Missing `stockout_risk` Calculation

**Files:** `smartstock-backend/apps/forecasting/views.py`, `services.py`

**What's wrong:** Dashboard endpoint returns `current_stock` and `threshold` but never computes `stockout_risk`.

**Fix:** Add to `ForecastingService`:
```python
def calculate_stockout_risk(self, sku_code: str) -> bool:
    stock = StockLevel.objects.get(sku__sku_code=sku_code)
    lead_time = stock.sku.product.supplier.default_lead_time_days or 7
    forecast = ForecastResult.objects.filter(
        sku__sku_code=sku_code
    ).order_by('-forecast_date')[:lead_time]
    total_predicted = sum(f.predicted_quantity for f in forecast)
    return stock.quantity_available < total_predicted + stock.sku.product.safety_stock
```
Add `stockout_risk: bool` field to `ForecastDashboardView` response.

---

### P1.6 [MA1] No Redis Caching on Forecast Endpoints

**Files:** `smartstock-backend/apps/forecasting/views.py`

**What's wrong:** No `cache.set()`/`cache.get()` anywhere in forecasting views. Task requires 1-hour TTL (3600s).

**Fix:** Add caching layer in `ForecastingService`:
```python
from django.core.cache import cache

def get_dashboard_data(self):
    cache_key = 'forecast_dashboard_data'
    data = cache.get(cache_key)
    if data is not None:
        return data
    data = self._compute_dashboard()
    cache.set(cache_key, data, timeout=3600)
    return data
```
Add cache invalidation in `TriggerForecastView`:
```python
cache.delete_pattern('forecast_dashboard_*')
```

---

### P1.7 [A5] Registration Allows Role Escalation

**File:** `smartstock-backend/apps/authentication/serializers.py:51-72`

**What's wrong:** `RegisterSerializer` exposes `role` field and accepts it without restriction — user can POST `{"email": "...", "password": "...", "role": "admin"}` to self-escalate.

**Fix:** Remove `role` from `RegisterSerializer.fields` or add validation:
```python
def validate_role(self, value):
    if value != CustomUser.Role.VIEWER:
        raise serializers.ValidationError("Only viewer role allowed at registration.")
    return value
```

---

### P1.8 [A5] No Auth Integration Tests

**File:** `smartstock-backend/tests/` — no `test_auth*.py` found.

**What's wrong:** DoD requires tests for: login, invalid credentials, token refresh (with/without cookie), logout, protected endpoint (with/without token), duplicate email → 409, password validation.

**Fix:** Create `tests/integration/test_auth_endpoints.py` covering all 7 scenarios using Django test client.

---

### P1.9 [A4] Root `.gitignore` Nearly Empty

**File:** `.gitignore` (root)

**Current contents:** Only `.impeccable/` and model report files. Everything else leaks.

**Fix — replace with:**
```gitignore
# Environment
.env
.env.local
.env.*.local
*.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/

# Django
db.sqlite3
db.sqlite3-journal
staticfiles/
media/

# Node
node_modules/
.npm
.vite/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Docker
*.log
```

Also extend `smartstock-backend/.gitignore` with: `*.pyd`, `.Python`, `.eggs/`, `htmlcov/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `staticfiles/`, `media/`, `.vscode/`, `.idea/`, `*.swp`, `Thumbs.db`.

---

### P1.10 [MA5] All Throttle Rates Wrong

**File:** `smartstock-backend/config/settings/base.py:135-139`

**Current:** `anon: 100/hour` (spec: 20/min), `user: 1000/hour` (spec: 100/min), `nlquery: 30/minute` (spec: 10/min for AI)

**Fix:**
```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '20/minute',
    'user': '100/minute',
    'login': '5/minute',
    'ai': '10/minute',
},
```

---

### P1.11 [MA5] Missing Custom `AIRateThrottle` Class

**File:** Create `smartstock-backend/core/throttles.py`

**What's wrong:** Task requires a dedicated class extending `UserRateThrottle`.

**Fix:**
```python
from rest_framework.throttling import UserRateThrottle

class AIRateThrottle(UserRateThrottle):
    scope = 'ai'
```

---

### P1.12 [MQ2] Forecast Chart Missing Confidence Bounds + SKU Selector

**File:** `smartstock-frontend/src/features/forecasting/components/SkuChart.tsx`

**What's wrong:**
1. Only `demand` series rendered — no `upper_bound`/`lower_bound` dashed lines
2. No confidence band fill between bounds (brand-50 at 40% opacity)
3. No SKU selector dropdown
4. No accessible data table below chart
5. X-axis uses `.slice(0, 5)` instead of "DD MMM" format
6. No `@media (prefers-reduced-motion: reduce)`

**Fix steps:**
1. Map `upperBound: d.upper_bound`, `lowerBound: d.lower_bound` in chart data
2. Add two `<Area>` components with `strokeDasharray="4 4"` for bounds
3. Add `<Area>` with fill `url(#confidence-gradient)` between bounds
4. Add SKU `<select>` dropdown above chart with loading state
5. Add `<table>` below chart with all 30 rows + `aria-label`
6. Fix X-axis: `format(new Date(d.date), 'dd MMM')`
7. Add `@media (prefers-reduced-motion: reduce) { @keyframes ... animation: none; }`

---

### P1.13 [MQ1] AuditLog Event Type Not an Enumeration

**File:** `smartstock-backend/apps/audit/models.py:7`

**Current:** `event = models.CharField(max_length=100)` — no constraints.

**Fix:** Convert to `TextChoices`:
```python
class AuditEvent(models.TextChoices):
    USER_LOGIN = 'USER_LOGIN'
    PO_CREATED = 'PO_CREATED'
    PO_APPROVED = 'PO_APPROVED'
    PO_REJECTED = 'PO_REJECTED'
    PO_SENT = 'PO_SENT'
    STOCK_ADJUSTED = 'STOCK_ADJUSTED'
    PRODUCT_CREATED = 'PRODUCT_CREATED'
    PRODUCT_UPDATED = 'PRODUCT_UPDATED'
    INVOICE_CONFIRMED = 'INVOICE_CONFIRMED'
    INVOICE_REJECTED = 'INVOICE_REJECTED'
    PROMPT_INJECTION_ATTEMPT = 'PROMPT_INJECTION_ATTEMPT'
    VISION_EXTRACTION_FAILED = 'VISION_EXTRACTION_FAILED'
    AGENT_RUN_COMPLETED = 'AGENT_RUN_COMPLETED'

event = models.CharField(max_length=100, choices=AuditEvent.choices)
```

---

### P1.14 [MQ4] Missing `CREATE EXTENSION vector` Init SQL

**File:** `docker-compose.yml`

**Fix:** Create `docker-entrypoint-initdb.d/01-init-vector.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
Mount in docker-compose:
```yaml
volumes:
  - ./docker-entrypoint-initdb.d:/docker-entrypoint-initdb.d
```

---

### P1.15 [MA4] No Database Readiness Wait Loop

**File:** `smartstock-backend/Dockerfile`

**Current:** CMD directly runs `python manage.py migrate --noinput && gunicorn ...`. No retry if DB isn't ready.

**Fix:** Add entrypoint script:
```dockerfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```
`entrypoint.sh`:
```bash
#!/bin/sh
until pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
python manage.py migrate --noinput
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

### P1.16 [O2] `tailwind.config.ts` Missing

**File:** `smartstock-frontend/tailwind.config.ts` — doesn't exist.

**What's wrong:** Project uses `bg-brand-600`, `text-green-800` etc. but no Tailwind config file defines these tokens.

**Fix:** Create `smartstock-frontend/tailwind.config.ts`:
```ts
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#...', 100: '#...', ..., 900: '#...' },
        green: { 50: '#...', ..., 900: '#...' },
        amber: { 50: '#...', ..., 900: '#...' },
        red: { 50: '#...', ..., 900: '#...' },
        purple: { 50: '#...', ..., 900: '#...' },
        gray: { 50: '#...', ..., 900: '#...' },
      },
    },
  },
  plugins: [],
}
```

---

### P1.17 [O4] Health Check Never Returns 503

**File:** `smartstock-backend/apps/health/views.py`

**What's wrong:** `HealthCheckView` always returns 200. `ReadinessView` exists (returns 503 on failure) but isn't registered in URLs.

**Fix:** Register readiness URL:
```python
# apps/health/urls.py
urlpatterns = [
    path('', HealthCheckView.as_view(), name='health-check'),
    path('readiness/', ReadinessView.as_view(), name='readiness'),
]
```

---

## Priority 2 — Major Gaps

### P2.1 [A1] Supplier Model Duplicated

**Files:** `apps/inventory/models.py` (full supplier) vs `apps/purchasing/models.py` (incomplete — missing `is_active`, `default_lead_time_days`, `updated_at`).

**Fix:** Remove Supplier from `purchasing/models.py`. Update `purchasing` app to import from `inventory.models`.

---

### P2.2 [O1] No Swagger/OpenAPI Schema URL

**File:** `smartstock-backend/config/urls.py`

**Current:** `drf-spectacular` installed + configured, but no URL registered.

**Fix:**
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

### P2.3 [O2] Sidebar Collapse Not in Zustand

**File:** `smartstock-frontend/src/shared/components/Sidebar.tsx`

**Fix:** Use `useUIStore.sidebarOpen` from Zustand instead of local `useState`. Add auto-collapse at 768px viewport width.

---

### P2.4 [MA2] Inventory Table Missing Stock Level Visual Bar

**File:** `smartstock-frontend/src/features/inventory/pages/InventoryPage.tsx`

**Fix:** Add a `<div>` bar per row with width proportional to `on_hand / reorder_point`, colored via `bg-green-500`/`bg-amber-500`/`bg-red-500`. Pulsing red animation for zero stock.

---

### P2.5 [MA2] Missing Server-Side Sorting + URL Query Params

**Fix:** Add `?ordering=` query param to API calls. Sync search/filter state to URL params via `useSearchParams`.

---

### P2.6 [MW5] Startup Validation Import-Order Dependency

**File:** `smartstock-backend/config/validators.py` + `core/apps.py`

**Fix:** Move eager validation to `settings/base.py` module level, before other imports.

---

### P2.7 [MW2] Viewer Role Redaction Not Implemented

**File:** `smartstock-frontend/src/features/purchasing/pages/SuppliersPage.tsx`

**Fix:** Check `user.role === 'viewer'` from auth store, conditionally render "—" for email/phone columns.

---

### P2.8 [MW1] Langfuse Client Created Per Request

**Fix:** Initialize Langfuse at module level, not inside request handler.

---

### P2.9 [MQ5] Price Field Missing Decimal Validation

**Fix:** Add `validate_unit_price` across all serializers — reject more than 2 decimal places.

---

### P2.10 [O3] MAE/MAPE Evaluated on Training Data

**File:** `smartstock-backend/apps/forecasting/prophet_engine.py:79`

**Current:** `model.fit(df[...])` → `_compute_accuracy(df, model)` — `df` includes test split, so metrics reflect training accuracy.

**Fix:** Split BEFORE fitting:
```python
split_idx = max(1, int(len(df) * 0.9))
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

model.fit(train_df[['ds', 'y']])
mae, mape = _compute_accuracy(test_df, model)  # true holdout

model2 = Prophet(weekly_seasonality=True, yearly_seasonality=len(df) >= 365)
model2.fit(df[['ds', 'y']])
```

---

## Priority 3 — Minor / Polish

| ID | Task | Issue | Fix |
|----|------|-------|-----|
| P3.1 | MW2 | `window.confirm()` not accessible | Replace with `<Dialog>` modal |
| P3.2 | MW2 | Search is client-side only | Add `?search=` query param |
| P3.3 | MW2 | No error toast on save failure | Wrap with try/catch + `toast.error()` |
| P3.4 | MA2 | `font-mono` not consistent on SKU | Apply `className="font-mono"` to SKU cell |
| P3.5 | MA2 | Keyboard navigation missing | Add `tabIndex`, `onKeyDown` handlers |
| P3.6 | MA2 | Reserved quantity column missing | Add `quantity_reserved` from API |
| P3.7 | A5 | Refresh without cookie → 422 (should be 401) | Exception handler maps missing cookie to 401 |
| P3.8 | A1 | Missing `Meta.ordering` on 5 models | Add `ordering = ['-created_at']` |
| P3.9 | A4 | Frontend `.env.example` has only `VITE_API_URL` | Expand to list all backend vars |
| P3.10 | MQ5 | Stock adjustment returns 400 not 422 | Change `status=400` → `status=422` |
| P3.11 | MA5 | CORS headers/methods not explicit | Add `CORS_ALLOW_HEADERS` + `CORS_ALLOW_METHODS` |
| P3.12 | MA5 | No OPTIONS throttle exemption | Add `throttle_classes = []` for OPTIONS |
| P3.13 | MW4 | Docker HEALTHCHECK missing | Add `HEALTHCHECK` instruction in Dockerfile |
| P3.14 | MQ1 | Most event types not wired to signals | Add signal handlers for all 13 event types |

---

## Verification Checklist (run after all fixes)

```
✓ python manage.py check -- no errors
✓ python manage.py migrate -- zero errors on fresh DB
✓ pytest tests/ -- all tests pass
✓ npm run lint -- no lint errors
✓ npm run build -- tsc -b && vite build succeeds
✓ docker compose up -d -- all services healthy
✓ curl -X POST .../api/auth/register/ cannot create admin
✓ curl .../api/auth/refresh/ without cookie -- returns 401
✓ gtimeout 61 bash -c 'for i in {1..101}; do curl ...; done' -- 101st returns 429
✓ curl -X POST .../api/ai/nlquery/ with injection -- returns 400 + audit log
✓ curl .../api/health/ with Redis down -- returns 503
✓ git status with .env file -- shows untracked
✓ grep -r "sk-" . (excluding .env.example) -- zero results
✓ grep -r "cursor.execute(f" . -- zero results
```
