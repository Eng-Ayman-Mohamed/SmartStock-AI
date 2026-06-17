# Performance Report: Table Loading Issues

**Date:** 2026-06-16
**Scope:** All frontend data tables and their backend API endpoints
**Severity Summary:** 2 CRITICAL, 6 HIGH, 8 MEDIUM, 4 LOW

---

## 1. Inventory Products Table

**Route:** `InventoryPage.tsx` → `GET /api/inventory/products/`
**Severity: MEDIUM**

### Backend

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 1.1 | **Extra low-stock scan per paginated page** | `views.py:231-245` | `list()` calls `get_low_stock_items()` on every paginated request — executes a full `StockLevel` scan + 30-day `SalesRecord` aggregation. 3 DB queries per page instead of 1. Browsing 5 pages = 15 queries. |
| 1.2 | **Cache key fragmentation** | `views.py:233` | Key embeds `request.get_full_path()` (search, sort, filter). Each unique param combo creates a separate cache entry → low hit rate, negating cache benefit. |
| 1.3 | **`defer('description')` is a no-op** | `views.py:212` | Applied after `select_related`/`prefetch_related` already loaded the column. No actual IO savings. |

### Frontend

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 1.4 | **Columns defined inline every render** | `InventoryPage.tsx:309-440` | 130-line column definitions create new arrow function references on every render → defeats any possible `DataTable` memoization. |
| 1.5 | **Form state at page level causes full re-renders** | `InventoryPage.tsx:134-137` | 6 form fields (`formName`, `formDescription`, `formReorder`, `formSafety`, `stockDelta`, `stockReason`) live on the page, not in modals. Every keystroke re-renders the entire page including DataTable. |
| 1.6 | **Duplicate filtering** | `InventoryPage.tsx:167,294` | `statusFilter` is sent to the API **and** applied again client-side after the `flatMap`. Double work, no benefit. |
| 1.7 | **Duplicate pagination UI** | `InventoryPage.tsx:554-645` | Hand-rolled pagination (~90 lines) instead of using DataTable's built-in `pagination` prop. Code duplication and inconsistency risk. |
| 1.8 | **No `React.memo` on DataTable** | `DataTable.tsx:35` | Every parent re-render re-executes all `col.render(row)` calls for every cell. |

---

## 2. Suppliers Table

**Route:** `SuppliersPage.tsx` → `GET /api/purchasing/suppliers/`
**Severity: HIGH**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 2.1 | **Broken pagination — frontend sees only page 1** | `SuppliersPage.tsx:138-147` | Frontend sends no `page`/`page_size`. Backend paginates (page_size=20) and returns page 1 only. Frontend thinks it has **all** suppliers but only has 20. Bug, not optimization. |
| 2.2 | **Search is silently broken** | Backend `views.py:119` | `SupplierViewSet` has no `search_fields` or `filterset_class`. Frontend sends `?search=...` but backend ignores it. Returns unfiltered page 1 regardless of search query. |
| 2.3 | **Backend queryset has no `select_related`** | `apps/purchasing/views.py:119` | `Supplier.objects.all()` — if any serializer accesses related `products`, it triggers N+1. |
| 2.4 | **`setPage()` side-effect in render body** | `SuppliersPage.tsx:162-163` | Calls `setPage(maxPage)` directly during render when page exceeds max → triggers an extra re-render. |

---

## 3. PO History Table

**Route:** `PurchasingPage.tsx` → `GET /api/purchasing/orders/`
**Severity: HIGH**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 3.1 | **Hard-coded `page_size=100` cap** | `PurchasingPage.tsx` data hook | Cannot see POs beyond the latest 100. If the business has 1000+ POs, 90% are invisible. |
| 3.2 | **Client-side pagination on a subset** | `PurchasingPage.tsx:112-113` | Paginates the 100 fetched records. Total page count doesn't reflect actual data. |
| 3.3 | **N+1 in `get_by_id()`** | **CRITICAL** — `repositories.py:9` | `get_by_id()` has NO `select_related`. Every PO action (approve, reject, send, confirm) triggers 5+ extra queries for `po.sku`, `po.sku.product`, `po.supplier`, `po.requested_by`, `po.approved_by`. |
| 3.4 | **`get_all()` lacks `select_related`** | `repositories.py:12` | View layer adds `select_related`, so list endpoint is covered. But any future direct caller gets N+1. |
| 3.5 | **Unnecessary `useMemo` wrappers** | `PurchasingPage.tsx:91-92` | `useMemo(() => data ?? [], [data])` on TanStack Query data — structural sharing already provides stable refs. Pure overhead. |

---

## 4. Users Table

**Route:** `UsersSettingsPage.tsx` → `GET /api/auth/users/`
**Severity: MEDIUM**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 4.1 | **Backend has no search or filter** | `views.py:236-276` | `UserListCreateView` has no `search_fields`, `filterset_class`, or `ordering_fields`. Admin cannot find a specific user. |
| 4.2 | **Frontend pagination broken — only page 1** | Frontend `listUsers()` in `api.ts` | Backend paginates (page_size=20). Frontend unwraps `{results, count}` but never fetches beyond page 1. Only 20 users displayed. |
| 4.3 | **No `select_related` on user queryset** | `views.py:236` | `CustomUser.objects.all().order_by('-date_joined')` — if serializer accesses related fields (e.g., `groups`), N+1. |
| 4.4 | **Client-side search is useless** | `UsersTable.tsx:42-147` | Filters only the 20 fetched users. If user #42 matches the search, invisible. |

---

## 5. Forecasting Dashboard

**Route:** `GET /api/forecasting/dashboard/`
**Severity: HIGH**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 5.1 | **Redundant duplicate forecast query** | `services.py:99-102` | `_compute_dashboard()` fetches `ForecastResult` twice: query 1 loads all rows, query 3 re-fetches same rows with `.order_by()`. Doubles forecast DB time. |
| 5.2 | **N+1 in `get_sales_for_all_skus()`** | **CRITICAL** — `repositories.py:78-93` | Loops over SKUs calling `get_sales_for_sku()` per SKU → **1 + N queries**. With 200 active SKUs = 201 queries. |
| 5.3 | **Alerts scan all SKUs per paginated page** | `services.py:41-68` | Even showing page 1 (6 of N items) forces scan of the entire SKU set for alerts. Defeats pagination. |
| 5.4 | **Massive cache entry** | `services.py:41-68` | Caches the entire unfiltered dataset. 500 SKUs at ~2KB each = ~1MB per cache key. |
| 5.5 | **`calculate_stockout_risk()` does 3 queries** | `services.py:21-39` | Stock lookup + lazy supplier load + forecast fetch. Should be single query with `select_related`. |

---

## 6. Stock Adjustment

**Route:** `StockAdjustView` / `StockLevelViewSet.adjust_stock`
**Severity: LOW**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 6.1 | **Duplicate validation in two endpoints** | `views.py:1002-1080` | Two endpoints with identical manual extraction (`quantity_delta`, `int()` conversion, bounds checks). |
| 6.2 | **`get_by_product_id()` does 2 queries** | `repositories.py:143-154` | SKU lookup + StockLevel lookup. Collapsible to 1 query. |

---

## 7. Invoice Processing

**Route:** `apply_confirmed_invoice()`
**Severity: MEDIUM**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 7.1 | **5-6 sequential queries, no transaction** | `services.py:177-222` | Supplier lookup, SKU lookup, stock lookup, update + re-read. No `transaction.atomic()`. Partial writes survive if a later step fails. |

---

## 8. Cross-Cutting: Frontend Rendering

**Severity: MEDIUM**

| # | Issue | File | Impact |
|---|-------|------|--------|
| 8.1 | **No `React.memo` on any shared component** | `DataTable.tsx`, `Skeleton.tsx`, `EmptyState.tsx` | Cascade re-renders from parent propagate through the entire component tree. |
| 8.2 | **No `useCallback` on event handlers** | All table pages | Handlers like `handleSort`, `handlePageChange` re-created every render → child components always receive new props. |
| 8.3 | **SkuChart recomputes every render** | `SkuChart.tsx:25-34` | No `useMemo` on `chartData`. Calls `new Date()` + `toLocaleDateString` for each forecast item on every re-render. |

---

## 9. Cross-Cutting: Database & Infrastructure

**Severity: MEDIUM**

| # | Issue | File:Line | Impact |
|---|-------|-----------|--------|
| 9.1 | **No `ATOMIC_REQUESTS`** | `settings/base.py` | Each request runs in autocommit. Partial writes survive on error. |
| 9.2 | **No statement timeout** | `settings/base.py` | Runaway query can hang DB indefinitely and pile up connections until outage. |
| 9.3 | **No query logging** | `settings/base.py` | Zero observability into slow queries in production. Cannot diagnose without reproducing. |
| 9.4 | **`IGNORE_EXCEPTIONS` masks Redis failures** | `settings/base.py:277` | Redis down → all cache calls silently return `None` → DB gets full load with zero alerts. |
| 9.5 | **Redundant composite index** | `models.py:101` | `Index(fields=['sku', 'date'])` duplicates the index from `unique_together`. Wasted write overhead. |

---

## 10. Missing Database Indexes

| Table | Missing Index | Impact |
|-------|--------------|--------|
| `PurchaseOrder` | `sku_id`, `supplier_id`, `requested_by_id`, `approved_by_id` | Every PO join (list, approve, reject) does sequential scan on FK columns |
| `Supplier` | `name` (searched via `icontains`) | Supplier search falls back to full table sequential scan |
| `CustomUser` | `email`, `is_active`, `role` | Login lookup, role filtering, user listing do full scans |
| `ForecastResult` | `sku_id`, `forecast_date` | Dashboard forecast queries scan all rows |
| `AuditLog` | `event`, `user_id`, `entity_type`, `timestamp` | Filtering by event type/user has no index support |

---

## Priority Action Plan

### P0 — Immediate
- [ ] Fix N+1 in `PurchasingRepository.get_by_id()` — add `select_related`
- [ ] Fix N+1 in `ForecastingRepository.get_sales_for_all_skus()` — use `Prefetch`
- [ ] Fix broken supplier pagination + search on backend
- [ ] Fix redundant duplicate forecast query in `_compute_dashboard()`

### P1 — This Sprint
- [ ] Add `select_related` on user list view
- [ ] Move form state to modal components in InventoryPage
- [ ] Add FK indexes on `PurchaseOrder`, `Supplier.name`, `CustomUser`
- [ ] Remove redundant composite index on `SalesRecord`

### P2 — Next Sprint
- [ ] Add `React.memo` to DataTable + shared components
- [ ] Extract column definitions from render body to module scope
- [ ] Add statement timeout + query logging to DB config
- [ ] Implement server-side search/filter for users

### P3 — Backlog
- [ ] Memoize `chartData` in SkuChart
- [ ] Remove unnecessary `useMemo` wrappers on TanStack Query data
- [ ] Evaluate `CursorPagination` for large tables
- [ ] Enable `ATOMIC_REQUESTS`
