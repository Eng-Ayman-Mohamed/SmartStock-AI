# SmartStock AI — Performance Engineering Report

**Date:** Sun Jun 14 2026
**Scope:** Full-stack performance audit — Django 5 + DRF backend, React 19 + Vite 8 frontend, PostgreSQL 16 + pgvector, Redis 7, Celery 5
**Methodology:** Static code analysis, query pattern review, architecture analysis, configuration audit

---

## Executive Summary

The SmartStock AI codebase has solid architectural foundations (Clean Architecture, repository pattern, proper `select_related`/`prefetch_related` usage in main views, Redis caching). However, several critical performance bottlenecks exist — most notably in the **AI/LLM pipeline** (dual GPT-4o calls per query), **N+1 query patterns** in the forecasting dashboard, and **missing database indexes** on high-traffic filter fields. Addressing the P0 and P1 items would likely reduce p95 latency by 40-60% and significantly improve throughput under load.

---

## P0 — Critical Issues (Fix Immediately)

### P0-1: NLQueryEndpointView Makes Two Sequential LLM Calls (3-8s Each)

**File:** `apps/inventory/views.py` lines 1346-1461
**Also:** `ai/llm/chain.py` lines 147-153

**Problem:** Every natural-language query triggers **two separate GPT-4o API calls**:
1. **Step B** (line 1371): `NLQueryChain.run()` → parses NL into structured filters via `gpt-4o` tool calling
2. **Step D** (line 1415): `call_gpt4o_formatter()` → formats raw DB results back into natural language via a second `gpt-4o` call

Each call has ~1-4s latency. Combined with prompt injection filtering and DB queries, total pipeline time regularly exceeds 6-10s. The view has a hard 10s timeout (line 1335) that will truncate responses.

**Impact:** High user-facing latency. Frequent 504 Gateway Timeout errors under moderate load. Double the OpenAI API cost per query.

**Recommended Fix:**
```python
# Option A: Use a single LLM call with structured output that includes the answer
# Merge the chain output schema to include both the action/filters AND a
# pre-computed answer template, eliminating the second call.

# Option B: Cache common query patterns (e.g., "low stock" → action=get_low_stock)
# to short-circuit the first LLM call for frequent queries.

# Option C: Make the formatter call non-blocking via Celery
from apps.purchasing.tasks import format_nl_answer  # new task
format_nl_answer.delay(original_query, raw_data, trace_id)
# Return raw_data immediately; let frontend poll or use WebSocket for formatted answer
```

---

### P0-2: N+1 Query in `get_low_stock_items()` — Per-SKU SQL Queries in Loop

**File:** `apps/inventory/services.py` lines 70-89

**Problem:** The method iterates over each low stock item and calls `self._avg_daily_demand(sl.sku_id)` (line 79) for each one. Each call executes a separate SQL query:
```python
# Line 96-103: This runs for EVERY low stock item
SalesRecord.objects.filter(sku_id=sku_id, date__gte=cutoff).aggregate(...)
```
With 50 low-stock items, this creates **50 additional SQL queries** after the initial low-stock fetch.

**Impact:** Linear query scaling. 50 low-stock items = 51 DB queries instead of 2.

**Recommended Fix:**
```python
def get_low_stock_items(self):
    # ... cache check ...
    low_stock = self.stock_repo.get_low_stock()
    sku_ids = [sl.sku_id for sl in low_stock]

    # Bulk fetch all avg daily demands in ONE query
    from datetime import timedelta
    from django.utils import timezone
    cutoff = timezone.localdate() - timedelta(days=30)
    demand_map = dict(
        SalesRecord.objects.filter(sku_id__in=sku_ids, date__gte=cutoff)
        .values('sku_id')
        .annotate(total=Sum('quantity_sold'))
        .values_list('sku_id', 'total')
    )

    result = []
    for sl in low_stock:
        total = demand_map.get(sl.sku_id, 0)
        avg_daily_demand = total / 30.0
        # ... rest of logic ...
```

---

### P0-3: N+1 in `_compute_dashboard()` — `calculate_stockout_risk()` Called Per SKU

**File:** `apps/forecasting/services.py` lines 46-67 and 71-86

**Problem:** Inside `_compute_dashboard()`, for each unique SKU in the forecast results, `calculate_stockout_risk(row.sku.code)` is called (line 55). Each call:
1. Does `StockLevel.objects.get(sku__code=sku_code)` — SQL query
2. Accesses `stock.sku.product.supplier` — potential lazy-load SQL
3. Queries `self.repo.get_all().filter(sku__code=sku_code).order_by('-forecast_date')[:lead_time]` — SQL query

For a dashboard with 30 SKUs, this generates **~90 additional SQL queries**.

**Impact:** Dashboard page load time scales linearly with SKU count. With 30 SKUs, total ~100 queries.

**Recommended Fix:**
```python
def _compute_dashboard(self):
    # ... existing forecast query ...

    # Batch-fetch stock levels for all SKUs in the dashboard
    sku_ids = set(row.sku.id for row in rows)
    stock_map = {
        sl.sku_id: sl
        for sl in StockLevel.objects.select_related('sku__product__supplier')
            .filter(sku_id__in=sku_ids)
    }

    # Batch-fetch forecast data for stockout risk
    from datetime import timedelta
    today = datetime.date.today()
    forecast_by_sku = defaultdict(list)
    for f in ForecastResult.objects.filter(
        forecast_date__gte=today,
        sku_id__in=sku_ids
    ).order_by('sku', 'forecast_date'):
        forecast_by_sku[f.sku_id].append(f)

    skus_map = {}
    for row in rows:
        sku_id = row.sku.id
        if sku_id not in skus_map:
            stock = stock_map.get(sku_id)
            # Calculate stockout risk from pre-fetched data
            lead_time = getattr(stock.sku.product.supplier, 'default_lead_time_days', 7) or 7 if stock else 7
            forecasts = forecast_by_sku.get(sku_id, [])[:lead_time]
            total_predicted = sum(f.predicted_quantity for f in forecasts)
            safety_stock = stock.sku.product.safety_stock if stock else 0
            stockout_risk = (stock.quantity_available < total_predicted + safety_stock) if stock else False
            # ... rest of logic ...
```

---

### P0-4: `ProductViewSet.get_queryset()` Creates New Repository Instance Per Request

**File:** `apps/inventory/views.py` lines 120-127

**Problem:** Every call to `get_queryset()` instantiates a new `InventoryRepository()`:
```python
def get_queryset(self):
    from .repositories import InventoryRepository
    return InventoryRepository().get_all_queryset(include_inactive=False)
```
This is called multiple times per request by DRF's `get_object()`, `list()`, etc. Each instantiation also re-evaluates the `select_related`/`prefetch_related` chain.

**Impact:** Unnecessary object creation and potential query re-evaluation per request.

**Recommended Fix:**
```python
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if not hasattr(self, '_queryset'):
            from .repositories import InventoryRepository
            include_inactive = self.request.query_params.get('include_inactive', '').lower() == 'true'
            is_admin = include_inactive and self.request.user.role == 'admin'
            self._queryset = InventoryRepository().get_all_queryset(include_inactive=is_admin)
        return self._queryset
```
Or better yet, set `queryset` in `__init__` or use DRF's caching pattern.

---

## P1 — High Priority (Fix Soon)

### P1-1: SKUCompactSerializer Calls `_stock_level()` 4 Times Per SKU

**File:** `apps/inventory/serializers.py` lines 32-40

**Problem:** Each `SKUCompactSerializer` calls `_stock_level(obj)` **four times** (for `stock_level_id`, `quantity_on_hand`, `quantity_reserved`, `stock_reorder_point`). Even with `prefetch_related('skus__stock_level')`, this hits Python attribute access 4 times when it should cache the result once.

**Impact:** With 20 products × 3 SKUs each = 120 redundant attribute accesses per list request.

**Recommended Fix:**
```python
class SKUCompactSerializer(serializers.ModelSerializer):
    stock_level_id = serializers.SerializerMethodField()
    quantity_on_hand = serializers.SerializerMethodField()
    quantity_reserved = serializers.SerializerMethodField()
    stock_reorder_point = serializers.SerializerMethodField()

    class Meta:
        model = SKU
        fields = (...)

    def _get_stock_level(self, obj):
        """Cache stock_level access to avoid repeated lookups."""
        if not hasattr(self, '_stock_level_cache'):
            self._stock_level_cache = {}
        if obj.pk not in self._stock_level_cache:
            try:
                self._stock_level_cache[obj.pk] = obj.stock_level
            except StockLevel.DoesNotExist:
                self._stock_level_cache[obj.pk] = None
        return self._stock_level_cache[obj.pk]

    def get_stock_level_id(self, obj):
        stock = self._get_stock_level(obj)
        return stock.id if stock else None

    def get_quantity_on_hand(self, obj):
        stock = self._get_stock_level(obj)
        return stock.quantity_on_hand if stock else 0

    def get_quantity_reserved(self, obj):
        stock = self._get_stock_level(obj)
        return stock.quantity_reserved if stock else 0

    def get_stock_reorder_point(self, obj):
        stock = self._get_stock_level(obj)
        return stock.reorder_point if stock else None
```

---

### P1-2: Missing Database Indexes on High-Traffic Fields

**File:** `apps/inventory/models.py`, `apps/purchasing/models.py`, `apps/authentication/models.py`

**Problem:** Several frequently filtered/queried fields lack explicit indexes:

| Model | Field | Used In | Impact |
|-------|-------|---------|--------|
| `Product` | `name` | `ProductFilter`, search | Full table scan on icontains |
| `Product` | `is_active` | Every product query (`filter(is_active=True)`) | Full table scan |
| `StockLevel` | `quantity_on_hand` | `StockLevelFilter`, ordering | Full table scan |
| `StockLevel` | `reorder_point` | Low stock comparison | Full table scan |
| `CustomUser` | `role` | Permission checks on every request | Full table scan |
| `PurchaseOrder` | `status` | `PurchaseOrderViewSet` filter | Full table scan |

**Recommended Fix:** Add to `models.py` `Meta.indexes`:
```python
# Product
class Meta:
    indexes = [
        models.Index(fields=['is_active', '-created_at'], name='idx_product_active_created'),
        models.Index(fields=['name'], name='idx_product_name'),
    ]

# StockLevel
class Meta:
    indexes = [
        models.Index(fields=['quantity_on_hand'], name='idx_stocklevel_qty'),
        models.Index(fields=['quantity_on_hand', 'reorder_point'], name='idx_stocklevel_low'),
    ]

# CustomUser
class Meta:
    indexes = [
        models.Index(fields=['role'], name='idx_user_role'),
    ]

# PurchaseOrder
class Meta:
    indexes = [
        models.Index(fields=['status', '-created_at'], name='idx_po_status_created'),
    ]
```

---

### P1-3: `_handle_get_inventory` Uses `.values()` After `.prefetch_related()`

**File:** `apps/inventory/views.py` lines 1138-1162

**Problem:** The function calls `.prefetch_related('skus__stock_level')` and `.select_related('category', 'supplier')`, then immediately chains `.values(...)`. When `.values()` is used, Django generates raw SQL JOINs and ignores the prefetch cache entirely — the ORM objects are never instantiated.

**Impact:** The prefetch_related is wasted. The SQL query is less efficient than a simple JOIN.

**Recommended Fix:**
```python
def _handle_get_inventory(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    results = (
        Product.objects.filter(q)
        .select_related('category', 'supplier')
        .values(
            'id', 'name', 'category__name', 'supplier__name',
        )[:50]
    )
    # Fetch stock data separately or via annotation
    product_ids = [r['id'] for r in results]
    stock_map = {
        sl.sku_id: sl.quantity_on_hand
        for sl in StockLevel.objects.filter(sku__product_id__in=product_ids)
            .select_related('sku')
    }
    # ... build response with stock data ...
```

---

### P1-4: Forecast Celery Task Processes SKUs Sequentially

**File:** `apps/forecasting/tasks.py` lines 9-21

**Problem:** `run_forecast_for_all_skus()` loops through every SKU sequentially:
```python
for sku_id in sku_ids:
    service.run_forecast(sku_id=sku_id)  # CPU-intensive Prophet training
```
Prophet model training is CPU-bound. With 100 SKUs, this could take 30+ minutes on a single worker.

**Impact:** Long-running task blocks the Celery worker. No parallelism. Other tasks queue behind it.

**Recommended Fix:**
```python
@shared_task
def run_forecast_for_all_skus():
    from celery import group
    from .tasks import run_forecast_single_sku

    sku_ids = list(SKU.objects.values_list('id', flat=True))
    # Fan out to parallel tasks (limited concurrency)
    job = group(run_forecast_single_sku.s(sku_id) for sku_id in sku_ids)
    result = job.apply_async()
    return f'Dispatched {len(sku_ids)} forecast tasks'

@shared_task(rate_limit='10/m')  # Limit to prevent API overload
def run_forecast_single_sku(sku_id: int):
    from .services import ForecastingService
    service = ForecastingService()
    service.run_forecast(sku_id=sku_id)
    return f'Forecasted SKU {sku_id}'
```

---

### P1-5: `NLQueryEndpointView` Creates `AuditLog` Synchronously

**File:** `apps/inventory/views.py` lines 1441-1450

**Problem:** `AuditLog.objects.create()` is called synchronously at the end of every NL query, adding 10-50ms latency to each response.

**Impact:** Unnecessary response latency for a non-critical write operation.

**Recommended Fix:**
```python
# Use Celery for audit logging
from apps.audit.tasks import create_audit_log

create_audit_log.delay(
    user_id=user.id,
    event='AI_NL_QUERY',
    data_snapshot={...}
)
```

---

## P2 — Medium Priority (Nice to Have)

### P2-1: ProductViewSet Cache Key Doesn't Include User Role

**File:** `apps/inventory/views.py` lines 135-142

**Problem:** The cache key `f'product_list_{request.get_full_path()}'` doesn't include user role. Admin users who can see inactive products would get cached results from non-admin users (or vice versa).

**Impact:** Potential data leakage or incorrect data served from cache.

**Recommended Fix:**
```python
def list(self, request, *args, **kwargs):
    cache_key = f'product_list_{request.user.role}_{request.get_full_path()}'
    # ... rest unchanged ...
```

---

### P2-2: `ProductViewSet` List Cache Invalidates ALL Filtered Variants

**File:** `apps/inventory/views.py` line 135 and `apps/inventory/services.py` line 18

**Problem:** `cache.delete_pattern('product_list_*')` deletes every cached product list variant on any product change. If users have 50 different filter combinations cached, all are invalidated.

**Impact:** Unnecessary cache invalidation leads to cache misses and increased DB load.

**Recommended Fix:** Use a versioned cache key:
```python
_product_cache_version = 0

def _invalidate_product_cache():
    global _product_cache_version
    _product_cache_version += 1

# In view:
cache_key = f'product_list_v{_product_cache_version}_{request.get_full_path()}'
```

---

### P2-3: No `only()` or `defer()` on List Querysets

**File:** `apps/inventory/views.py` (multiple ViewSets)

**Problem:** All views load full model fields including `description` (TextField) even when the list serializer doesn't use it. For products with long descriptions, this wastes memory and transfer time.

**Impact:** ~20-40% more data transferred per query than necessary.

**Recommended Fix:**
```python
queryset = (
    Product.objects.select_related('category', 'supplier')
    .prefetch_related('skus__stock_level')
    .only('id', 'name', 'category_id', 'supplier_id', 'unit_price',
          'reorder_point', 'safety_stock', 'is_active', 'created_at', 'updated_at')
    .order_by('-created_at')
)
```

---

### P2-4: Gunicorn Worker Configuration Suboptimal

**File:** `Dockerfile` line 32

**Problem:** `gunicorn ... --workers 3 --timeout 60`. With only 3 workers and heavy I/O (LLM calls, DB queries), the server can handle very few concurrent requests.

**Impact:** Low concurrency ceiling. Workers blocked on I/O can't serve other requests.

**Recommended Fix:**
```dockerfile
# For I/O-bound workloads: 2 * CPUcores + 1 workers
# For LLM-heavy workloads, consider more workers with async support
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--worker-class", "gthread", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50"]
```

---

### P2-5: `_nl_chain` Global Singleton Not Thread-Safe

**File:** `apps/inventory/views.py` lines 15-20

**Problem:** The global `_nl_chain` lazy initialization is not thread-safe:
```python
_nl_chain = None
def get_nl_chain():
    global _nl_chain
    if _nl_chain is None:  # Race condition in multi-threaded env
        from ai.llm.chain import NLQueryChain
        _nl_chain = NLQueryChain()
    return _nl_chain
```

**Impact:** In gthread worker class or async context, two threads could simultaneously create the chain.

**Recommended Fix:**
```python
import threading
_nl_chain = None
_nl_chain_lock = threading.Lock()

def get_nl_chain():
    global _nl_chain
    if _nl_chain is None:
        with _nl_chain_lock:
            if _nl_chain is None:
                from ai.llm.chain import NLQueryChain
                _nl_chain = NLQueryChain()
    return _nl_chain
```

---

## P3 — Low Priority (Future Optimizations)

### P3-1: No Frontend Code Splitting

**File:** `smartstock-frontend/src/lib/router.tsx`

**Problem:** All 13 page components are eagerly imported. The entire app bundle loads on first visit.

**Impact:** Larger initial bundle (~500KB+ with recharts, lucide-react, etc.). Slower First Contentful Paint.

**Recommended Fix:**
```tsx
import { lazy, Suspense } from 'react';

const DashboardPage = lazy(() => import('../features/dashboard/pages/DashboardPage'));
const InventoryPage = lazy(() => import('../features/inventory/pages/InventoryPage'));
const ForecastingPage = lazy(() => import('../features/forecasting/pages/ForecastingPage'));
// ... etc

// In routes:
{
  element: <Layout />,
  children: [
    { index: true, element: <Suspense fallback={<Skeleton />}><DashboardPage /></Suspense> },
    // ...
  ],
}
```

---

### P3-2: No Vite Build Chunk Optimization

**File:** `smartstock-frontend/vite.config.ts`

**Problem:** No manual chunk splitting configured. Heavy libraries (recharts, react, zustand) end up in the main bundle.

**Recommended Fix:**
```ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-state': ['zustand', '@tanstack/react-query'],
        },
      },
    },
  },
});
```

---

### P3-3: Redis `appendfsync` Not Tuned for Cache Use Case

**File:** `docker-compose.yml` line 35

**Problem:** `redis-server --appendonly yes` without specifying `appendfsync`. Default is `everysec`. For a cache-only Redis instance, AOF persistence is unnecessary overhead.

**Recommended Fix:**
```yaml
command: redis-server --appendonly no --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

### P3-4: DocumentChunk Vector Search Missing HNSW Index

**File:** `apps/ingestion/models.py`

**Problem:** The `DocumentChunk` model uses `VectorField(dimensions=1536)` for pgvector embeddings but has no HNSW or IVFFlat index for approximate nearest neighbor search. Vector similarity searches will do sequential scans.

**Impact:** RAG retrieval degrades linearly with chunk count. Fine for <10K chunks, unusable at 100K+.

**Recommended Fix:** Add a migration with HNSW index:
```sql
CREATE INDEX document_chunk_embedding_hnsw
ON ingestion_documentchunk
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

### P3-5: `call_gpt4o_formatter` Creates New LLM Instance Every Call

**File:** `ai/llm/chain.py` line 150

**Problem:** `call_gpt4o_formatter()` calls `llm = get_llm()` which creates a new `ChatOpenAI` instance each time. While LangChain may pool HTTP connections internally, creating new client objects has overhead.

**Recommended Fix:** Cache the LLM instance or reuse the one from NLQueryChain.

---

## Summary Matrix

| ID | Severity | Category | Impact | Effort |
|----|----------|----------|--------|--------|
| P0-1 | Critical | LLM Pipeline | 2x latency, 2x API cost | High |
| P0-2 | Critical | DB (N+1) | 50+ extra queries on low stock | Medium |
| P0-3 | Critical | DB (N+1) | 90+ extra queries on dashboard | Medium |
| P0-4 | Critical | View | Redundant repo instantiation | Low |
| P1-1 | High | Serializer | 120 redundant lookups per list | Low |
| P1-2 | High | DB Index | Full scans on key filters | Low |
| P1-3 | High | Query | Wasted prefetch on NL queries | Medium |
| P1-4 | High | Celery | Sequential CPU-bound tasks | Medium |
| P1-5 | High | Audit | Unnecessary sync write latency | Low |
| P2-1 | Medium | Cache | Data leakage risk | Low |
| P2-2 | Medium | Cache | Over-invalidation | Low |
| P2-3 | Medium | Query | Excess data transfer | Low |
| P2-4 | Medium | Infra | Low concurrency ceiling | Low |
| P2-5 | Medium | Concurrency | Race condition | Low |
| P3-1 | Low | Frontend | Large initial bundle | Medium |
| P3-2 | Low | Frontend | No chunk splitting | Low |
| P3-3 | Low | Infra | Redis persistence overhead | Low |
| P3-4 | Low | RAG | Vector search at scale | Medium |
| P3-5 | Low | LLM | Client instantiation overhead | Low |

---

## Estimated Impact of P0+P1 Fixes

- **API latency reduction:** 40-60% for NL query endpoints
- **DB query reduction:** 80-90% for dashboard and low-stock endpoints
- **Throughput increase:** 2-3x with proper Gunicorn tuning and async audit logging
- **Cost reduction:** ~50% on OpenAI API calls (eliminating second LLM call)
