# Implementation Plan — Unfixed Items from Future-Work.md

Generated: 2026-06-21

Based on investigation of `reports/Future-Work.md`, 12 of 18 identified issues remain unfixed. This report organizes them into phases by effort and dependency.

---

## Phase 0 — Quick CSS Fixes (~30 min each)

| # | Item | File(s) | Fix | Estimate |
|---|------|---------|-----|----------|
| 1 | **8px grid drift** | `ForecastingPage.tsx:79,96` | Change `gap-5` → `gap-6` | ~15 min |
| 2 | **StatCard hardcoded sizes** | `StatCard.tsx:33`, `Header.tsx:131` | `text-[26px]` → `text-2xl` (or token), `text-[11px]` → `text-xs` | ~20 min |
| 3 | **Sidebar tooltip overflow** | `Sidebar.tsx:56,171` | Add `right-0` + `max-w-[200px]`, switch from `whitespace-nowrap` to truncation | ~20 min |

---

## Phase 1 — RAG Backend Improvements (1-2 days each)

| # | Item | Scope | Approach |
|---|------|-------|----------|
| 4 | **Bulk document upload** | Backend + Frontend | Serializer: accept `ListField` of files. View: loop/parallel upload. Frontend: `multiple` attr on file input, batch POST or single multi-file endpoint |
| 5 | **Signals/Celery for Cloudinary re-ingest** | Backend | Add `tasks.py` to `ingestion` app. Move `ingest_pdf` into Celery task. Add Cloudinary webhook handler or Celery beat poller. Make upload view delegate to background task |
| 6 | **Document versioning** | Backend | Add `version_number` + `previous_version` FK to `Document` model (or use `django-simple-history`). Archive old chunks on re-ingest instead of delete. Add `GET /api/ai/documents/:id/versions/` endpoint |

---

## Phase 2 — Frontend Delight & Micro-interactions (2-4 hrs each)

| # | Item | File(s) | Approach |
|---|------|---------|----------|
| 7 | **Chart hover effects** | `SkuChart.tsx`, `DashboardPage.tsx` | Add Recharts `<Crosshair>`, custom `activeDot` styling, gradient fill on hover |
| 8 | **Success animations on mutations** | `InventoryPage.tsx`, `PurchasingPage.tsx`, `DataTable.tsx` | Add CSS keyframes for green row flash; checkmark stamp animation on toast; integrate into mutation `onSuccess` callbacks |
| 9 | **Empty state custom SVGs** | `EmptyState.tsx`, `InventoryPage.tsx`, `PurchasingPage.tsx` | Create 3-4 sticker-palette SVGs (brand, green, amber, purple). Support custom SVG in `EmptyState` alongside Lucide. Replace per-page instances |

---

## Phase 3 — Frontend Feature Work (0.5-1 day each)

| # | Item | File(s) | Approach |
|---|------|---------|----------|
| 10 | **Bulk operations** | `DataTable.tsx`, `InventoryPage.tsx`, `PurchasingPage.tsx` | Add checkbox column, `selectedIds` state, select-all to DataTable. Add bulk action toolbar (delete, status update). Wire to backend batch endpoints |

---

## Phase 4 — Major Features (1-2 days each)

| # | Item | Approach |
|---|------|----------|
| 11 | **Keyboard shortcuts** | Add `react-hotkeys-hook` or custom hook. Register: `Ctrl+K` command palette, `n` new product, `a` approve PO, `?` shortcut overlay. Build command palette modal component |
| 12 | **Help system & onboarding** | Add `react-joyride` or custom step wizard. 3-step first-time tour for new users. Contextual tooltip system on complex features. Help menu in header |

---

## Recommended Execution Order

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
```

**Rationale:** Quick CSS wins first (low risk, immediate visual improvement), then backend infrastructure (foundation for document features), then smaller frontend polish, then feature builds.

---

## Summary Table

| Phase | Items | Total Estimate |
|-------|-------|----------------|
| Phase 0 — Quick CSS Fixes | 3 | ~1 hr |
| Phase 1 — RAG Backend | 3 | ~3-6 days |
| Phase 2 — Delight & Micro-interactions | 3 | ~6-12 hrs |
| Phase 3 — Feature Work | 1 | ~0.5-1 day |
| Phase 4 — Major Features | 2 | ~2-4 days |
| **Total** | **12** | **~7-13 days** |
