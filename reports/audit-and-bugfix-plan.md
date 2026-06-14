# SmartStock AI — Comprehensive Audit & Bug-Fix Plan

**Date:** June 15, 2026  
**Team Size:** 5 members  
**Scope:** Full-stack (Django 5 + DRF backend, React 19 + Vite 8 frontend, AI/LLM layer, infrastructure)  
**Estimated Duration:** 5 days (3 sprint + 1 integration + 1 validation)

---

## Existing Reports (Already Complete)

| Report | Issues Found | Location |
|--------|-------------|----------|
| Security Audit | 12 (2 Critical, 4 High, 4 Medium, 2 Low) | `reports/security-audit-report.md` |
| Performance Audit | 19 (4 P0, 5 P1, 5 P2, 5 P3) | `reports/performance-report.md` |

This plan incorporates remediation of all existing issues plus new findings across architecture, code quality, testing, and edge cases.

---

## Team Distribution & Ownership

| Member | Domain | Scope | Est. Effort |
|--------|--------|-------|-------------|
| **Member 1** | Security Remediation | Fix SEC-001 through SEC-012 from existing report + new findings | 2-3 days |
| **Member 2** | Performance & Database | Fix P0-1 through P3-5 from existing report + N+1 queries, missing indexes | 2-3 days |
| **Member 3** | AI/LLM Layer Hardening | Prompt injection, input validation, error recovery, cost controls, thread safety | 2-3 days |
| **Member 4** | Frontend Audit & Testing | Set up Vitest, write component/hook/store tests, audit React patterns | 3-4 days |
| **Member 5** | Backend Code Quality & Testing | Fill testing gaps (core/, monitoring, management commands), fix error handling, clean architecture compliance | 2-3 days |

---

## Phase 1: Independent Parallel Sprints (Days 1-3)

Each member works in their domain with no cross-dependencies. All work should be on individual feature branches.

### Member 1 — Security Remediation

**Deliverable:** All 12 SEC issues resolved, security report updated with verification.

| # | Task | Issues Fixed | Files |
|---|------|-------------|-------|
| 1.1 | Move Grafana credentials to `.env` variables | SEC-001 | `docker-compose.yml` |
| 1.2 | Remove SECRET_KEY fallback, raise `ImproperlyConfigured` | SEC-002 | `config/settings/base.py` |
| 1.3 | Remove `*` from ALLOWED_HOSTS, use explicit domains | SEC-003 | `.env`, `config/settings/base.py` |
| 1.4 | Add `--requirepass` to Redis, update REDIS_URL in settings | SEC-004 | `docker-compose.yml`, `config/settings/base.py` |
| 1.5 | Add shared-secret header verification for health endpoints | SEC-005 | `apps/health/views.py` |
| 1.6 | Change DEBUG default to `'False'` | SEC-006 | `config/settings/base.py` |
| 1.7 | Restrict CORS_ALLOWED_ORIGINS in production | SEC-007 | `config/settings/production.py` |
| 1.8 | Add throttle classes to health endpoints | SEC-008 | `apps/health/views.py` |
| 1.9 | Harden prompt injection filter — Unicode normalization, second classifier layer | SEC-009 | `ai/llm/chain.py` |
| 1.10 | Reduce REFRESH_TOKEN_LIFETIME to 3 days | SEC-010 | `config/settings/base.py` |
| 1.11 | Remove default DB credentials, require env vars | SEC-011 | `docker-compose.yml` |
| 1.12 | Add SECURE_HSTS_SECONDS, INCLUDE_SUBDOMAINS, PRELOAD | SEC-012 | `config/settings/production.py` |
| 1.13 | Verify all fixes, update `reports/security-audit-report.md` | — | `reports/security-audit-report.md` |

---

### Member 2 — Performance & Database

**Deliverable:** All P0/P1 issues fixed, P2 addressed where low-effort, performance report updated.

| # | Task | Issues Fixed | Files |
|---|------|-------------|-------|
| 2.1 | Merge dual LLM calls in NLQueryEndpointView (single call with structured output) | P0-1 | `apps/inventory/views.py`, `ai/llm/chain.py` |
| 2.2 | Batch `_avg_daily_demand()` — single bulk query instead of per-SKU loop | P0-2 | `apps/inventory/services.py` |
| 2.3 | Batch `calculate_stockout_risk()` — prefetch all stock levels and forecasts | P0-3 | `apps/forecasting/services.py` |
| 2.4 | Cache `get_queryset()` instance in ProductViewSet | P0-4 | `apps/inventory/views.py` |
| 2.5 | Cache `_stock_level()` access in SKUCompactSerializer | P1-1 | `apps/inventory/serializers.py` |
| 2.6 | Add DB indexes (Product, StockLevel, CustomUser, PurchaseOrder) + migration | P1-2 | `apps/*/models.py` |
| 2.7 | Remove `.prefetch_related()` before `.values()` — use JOIN or manual fetch | P1-3 | `apps/inventory/views.py` |
| 2.8 | Parallelize forecast Celery tasks (group + rate-limited subtasks) | P1-4 | `apps/forecasting/tasks.py` |
| 2.9 | Make audit log writes async via Celery | P1-5 | `apps/inventory/views.py` |
| 2.10 | Include user role in cache key | P2-1 | `apps/inventory/views.py` |
| 2.11 | Thread-safe `_nl_chain` singleton with lock | P2-5 | `apps/inventory/views.py` |
| 2.12 | Verify all fixes, update `reports/performance-report.md` | — | `reports/performance-report.md` |

---

### Member 3 — AI/LLM Layer Hardening

**Deliverable:** AI layer hardened, error handling improved, edge-case tests written.

| # | Task | Files |
|---|------|-------|
| 3.1 | Add input length limits on NL queries (max 2000 chars) | `ai/llm/chain.py` |
| 3.2 | Sanitize database records before injecting into LLM formatter prompt | `ai/llm/chain.py` |
| 3.3 | Fix prompt injection filter failure default — crash closed instead of defaulting to "safe" | `apps/ingestion/views.py`, `apps/inventory/views.py` |
| 3.4 | Add error handling to `VisionExtractor.extract()` (try/except on OpenAI API call, json parsing) | `ai/multimodal/vision.py` |
| 3.5 | Add error handling to `WhisperTranscriber.transcribe()` (API failures, file format, network timeouts) | `ai/multimodal/whisper.py` |
| 3.6 | Add input validation to AI tools (integer range checks, bound checks on top_k) | `ai/agents/tools/*.py` |
| 3.7 | Implement `inject_citations()` — currently a no-op stub | `ai/rag/citation.py` |
| 3.8 | Add thread safety to Langfuse singletons | `ai/observability/langfuse.py` |
| 3.9 | Add thread safety to `_ClassifierLLM` singleton | `ai/llm/intent_classifier.py` |
| 3.10 | Add OpenAI API retry/backoff (exponential backoff, 3 retries) | `ai/llm/chain.py` |
| 3.11 | Add token budget enforcement (per-request cap, per-user daily cap) | `ai/llm/chain.py` |
| 3.12 | Add circuit breaker pattern for OpenAI API calls | `ai/llm/chain.py` |
| 3.13 | Write tests for all new edge case handling | `tests/unit/ai/` |

---

### Member 4 — Frontend Audit & Testing

**Deliverable:** Vitest configured, critical paths tested, React patterns audited, bundle optimized.

| # | Task | Files/Area |
|---|------|------------|
| 4.1 | Install and configure Vitest + React Testing Library + jsdom + @testing-library/user-event | `smartstock-frontend/package.json`, `vitest.config.ts` |
| 4.2 | Write tests for Zustand stores (authStore, toastStore, uiStore) | `store/` |
| 4.3 | Write tests for auth flow (LoginForm, RegisterForm, JWT refresh, ProtectedRoute) | `features/auth/` |
| 4.4 | Write tests for core hooks (useDebounce, usePagination) | `shared/hooks/` |
| 4.5 | Write tests for API client functions (all feature `api.ts` files) | `features/*/api.ts` |
| 4.6 | Write tests for shared components (DataTable, Modal, Sidebar, Layout, Button, Toast) | `shared/components/` |
| 4.7 | Audit React patterns — identify unnecessary re-renders, missing useEffect cleanup, stale closures | `src/` |
| 4.8 | Audit TypeScript — replace `any` usage, add missing types, remove unsafe type assertions | `src/` |
| 4.9 | Implement code splitting — convert all route imports to `lazy()` + `Suspense` | `lib/router.tsx` |
| 4.10 | Add Vite chunk optimization — vendor-react, vendor-charts, vendor-state | `vite.config.ts` |
| 4.11 | Ensure `npm run lint && npm run build` passes clean | `smartstock-frontend/` |

---

### Member 5 — Backend Code Quality & Testing

**Deliverable:** Testing gaps filled, error handling cleaned up, architecture compliance verified.

| # | Task | Files |
|---|------|-------|
| 5.1 | Write tests for `core/base_repository.py` | `tests/unit/` |
| 5.2 | Write tests for `core/pagination.py` | `tests/unit/` |
| 5.3 | Write tests for `core/validators.py` | `tests/unit/` |
| 5.4 | Write tests for `core/mixins.py` | `tests/unit/` |
| 5.5 | Write tests for `core/throttles.py` | `tests/unit/` |
| 5.6 | Write tests for `apps/monitoring/middleware.py` | `tests/unit/` |
| 5.7 | Write tests for `apps/monitoring/evaluation_tasks.py` | `tests/unit/` |
| 5.8 | Write tests for management command `seed_data` | `tests/unit/` |
| 5.9 | Narrow broad `except Exception:` blocks across the codebase (24 occurrences) | `apps/*/views.py`, `apps/*/tasks.py`, `apps/*/services.py` |
| 5.10 | Fix silent `except Exception: pass` in Langfuse tracing (add proper logging) | `apps/inventory/views.py:1438` |
| 5.11 | Fix `calculate_stockout_risk` returning `False` on DB error (re-raise or log properly) | `apps/forecasting/services.py:37` |
| 5.12 | Fix Cloudinary upload failure creating document with empty URL | `apps/ingestion/services.py:275` |
| 5.13 | Verify Clean Architecture compliance — no DB queries in views, no AI imports in apps | `apps/`, `ai/`, `core/` |
| 5.14 | Add write tests for services that are missing tests | `tests/unit/` |
| 5.15 | Run full test suite, verify `pytest --cov --cov-fail-under=80` passes | `smartstock-backend/` |

---

## Phase 2: Cross-Team Integration (Day 4)

| Time | Activity | Owner | Purpose |
|------|----------|-------|---------|
| AM | Merge all PRs to `main` sequentially | Member 5 | Consolidate fixes, coordinate merge order |
| AM | Resolve file conflicts | All | High-conflict files: `apps/inventory/views.py` (Members 1,2,3,5), `config/settings/base.py` (1,2), `ai/llm/chain.py` (1,2,3), `docker-compose.yml` (1,2) |
| PM | Run full CI pipeline | Member 5 | Lint + tests + build + OpenAPI validation |
| PM | Integration testing — NL query, forecasting, purchasing workflow, auth flows | All | End-to-end manual smoke tests |

**Merge Order (minimize rebase pain):**
1. Member 1 (security — touches most foundational config)
2. Member 2 (performance — touches same files as 1, rebases on top)
3. Member 3 (AI — rebases on top of 1+2)
4. Member 5 (code quality — rebases on top of 1+2+3)
5. Member 4 (frontend — independent, can merge anytime)

---

## Phase 3: Validation & Sign-off (Day 5)

| # | Activity | Owner | Deliverable |
|---|----------|-------|-------------|
| 6.1 | Run `pytest tests/ --cov --cov-fail-under=80 -v` | Member 5 | Coverage report |
| 6.2 | Run `ruff check .` | Member 5 | Backend lint clean |
| 6.3 | Run `python manage.py check --deploy --settings=config.settings.production` | Member 1 | Django deployment check |
| 6.4 | Run `npm run lint && npm run build` | Member 4 | Frontend clean |
| 6.5 | Security re-scan and report update | Member 1 | `reports/security-audit-report.md` v2 |
| 6.6 | Performance re-benchmark and report update | Member 2 | `reports/performance-report.md` v2 |
| 6.7 | Architecture compliance summary | Member 5 | Brief ADR or report note |
| 6.8 | Final PR review and merge to `main` | All | Clean `main` branch |

---

## File Conflict Matrix

Files modified by multiple members. Use the merge order above to minimize conflicts.

| File | Member 1 | Member 2 | Member 3 | Member 5 |
|------|:--------:|:--------:|:--------:|:--------:|
| `apps/inventory/views.py` | X | X | X | X |
| `config/settings/base.py` | X | X | | |
| `ai/llm/chain.py` | X | X | X | |
| `apps/forecasting/services.py` | | X | | X |
| `docker-compose.yml` | X | X | | |
| `apps/ingestion/views.py` | | | X | X |
| `apps/inventory/services.py` | | X | | X |

---

## Quick Reference: File-Only Checklist (Summary)

### Backend Files

| File | Action | Member |
|------|--------|--------|
| `docker-compose.yml` | Remove hardcoded Grafana creds → `.env`, add Redis `--requirepass`, remove default DB creds | 1 |
| `config/settings/base.py` | Remove SECRET_KEY fallback, fix ALLOWED_HOSTS, change DEBUG default, add Redis auth URL, reduce JWT refresh to 3d | 1 |
| `config/settings/production.py` | Restrict CORS origins, add HSTS headers | 1 |
| `apps/health/views.py` | Add shared-secret header check, add throttle classes | 1 |
| `ai/llm/chain.py` | Unicode normalization on injection filter, merge dual LLM calls, add input length limit, sanitize DB records in formatter, add retry/backoff, add token budget | 1, 2, 3 |
| `apps/inventory/views.py` | Merge dual LLM calls, cache queryset, fix prefetch before values, add role to cache key, thread-safe singleton, audit log async, fix Langfuse silent pass, fix injection default | 1, 2, 3, 5 |
| `apps/inventory/services.py` | Batch `_avg_daily_demand` queries | 2 |
| `apps/inventory/serializers.py` | Cache `_stock_level` lookups | 2 |
| `apps/forecasting/services.py` | Batch `calculate_stockout_risk`, fix exception swallowing | 2, 5 |
| `apps/forecasting/tasks.py` | Parallelize forecast tasks via Celery group | 2 |
| `apps/inventory/models.py` | Add indexes (Product) | 2 |
| `apps/purchasing/models.py` | Add indexes (PurchaseOrder) | 2 |
| `apps/authentication/models.py` | Add indexes (CustomUser.role) | 2 |
| `apps/ingestion/views.py` | Fix injection filter default on exception | 3 |
| `ai/multimodal/vision.py` | Add error handling | 3 |
| `ai/multimodal/whisper.py` | Add error handling | 3 |
| `ai/agents/tools/*.py` | Add input validation | 3 |
| `ai/rag/citation.py` | Implement stubbed function | 3 |
| `ai/observability/langfuse.py` | Add thread safety | 3 |
| `ai/llm/intent_classifier.py` | Add thread safety | 3 |
| `apps/ingestion/services.py` | Fix empty URL on Cloudinary failure | 5 |
| `apps/*/views.py`, `tasks.py`, `services.py` | Narrow broad `except Exception:` blocks | 5 |

### Frontend Files

| File | Action | Member |
|------|--------|--------|
| `package.json` | Add Vitest + testing-library dependencies | 4 |
| `vitest.config.ts` | New file — configure test runner | 4 |
| `lib/router.tsx` | Code splitting via lazy/Suspense | 4 |
| `vite.config.ts` | Add manualChunks for vendor splitting | 4 |
| `store/*.ts` | Add tests | 4 |
| `features/auth/*` | Add tests | 4 |
| `shared/hooks/*` | Add tests | 4 |
| `shared/components/*` | Add tests | 4 |

### Infrastructure Files

| File | Action | Member |
|------|--------|--------|
| `.env` | Update ALLOWED_HOSTS, add Grafana/Redis secrets | 1 |
| `.env.example` | Document new required vars | 1 |

---

## Test Files to Create

| Test File | Tests For | Member |
|-----------|-----------|--------|
| `tests/unit/test_base_repository.py` | `core/base_repository.py` | 5 |
| `tests/unit/test_pagination.py` | `core/pagination.py` | 5 |
| `tests/unit/test_validators.py` | `core/validators.py` | 5 |
| `tests/unit/test_mixins.py` | `core/mixins.py` | 5 |
| `tests/unit/test_throttles.py` | `core/throttles.py` | 5 |
| `tests/unit/test_monitoring_middleware.py` | `apps/monitoring/middleware.py` | 5 |
| `tests/unit/test_evaluation_tasks.py` | `apps/monitoring/evaluation_tasks.py` | 5 |
| `tests/unit/test_seed_command.py` | `core/management/commands/seed_data.py` | 5 |
| `tests/unit/ai/test_ai_error_recovery.py` | AI error handling (Member 3's changes) | 3 |
| `tests/unit/ai/test_ai_input_validation.py` | AI input validation (Member 3's changes) | 3 |
| `smartstock-frontend/src/store/__tests__/*.test.ts` | Zustand stores | 4 |
| `smartstock-frontend/src/features/auth/__tests__/*.test.tsx` | Auth components | 4 |
| `smartstock-frontend/src/shared/components/__tests__/*.test.tsx` | Shared components | 4 |

---

## Success Criteria

| Criterion | How to Verify | Owner |
|-----------|--------------|-------|
| All 12 SEC issues fixed | Security re-scan, updated report | Member 1 |
| All 4 P0 + 5 P1 issues fixed | Benchmark comparison, updated report | Member 2 |
| All AI edge cases addressed | New tests pass, code review | Member 3 |
| Frontend has ≥30 tests | `vitest run --coverage` | Member 4 |
| Backend coverage ≥80% | `pytest --cov --cov-fail-under=80` | Member 5 |
| CI pipeline passes | GitHub Actions green | Member 5 |
| No `except Exception: pass` patterns | `grep -r "except Exception" apps/ ai/` audit | Member 5 |
