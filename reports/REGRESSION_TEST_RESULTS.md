# SmartStock AI — Regression Test Results

**Date:** 2026-06-27
**Test Runner:** pytest 8.x + Django test framework
**Environment:** config.settings.test (SQLite in-memory with monkey-patches)

---

## Summary

| Metric | Result |
|--------|--------|
| Total tests | 1,754 |
| Passed | 1,754 |
| Failed | 0 |
| Warnings | 136 (deprecated NumPy/Prophet APIs) |
| Duration | ~2 minutes |

---

## Unit Tests (1,343 passed)

### Exception Handler
- `StockNotFoundExceptionTest` — 2/2 passed
- `InsufficientStockExceptionTest` — 2/2 passed
- `DuplicatePOErrorTest` — 1/1 passed
- `ForecastingModelErrorTest` — 1/1 passed
- `SupplierNotFoundExceptionTest` — 1/1 passed
- `GenericExceptionHandlerTest` — 1/1 passed (expects `ServerError` for unknown exceptions)
- `DRFExceptionHandlerStringDetailTest` — 3/3 passed

### Notifications API
- `TestNotificationViewSet` — 10/10 passed (IDOR fix verified)
- `TestUnreadCountView` — 6/6 passed

### Monitoring Notifications
- `SendAlertEmailTest` — 5/5 passed (Celery task mocking verified)
- `SendDashboardNotificationTest` — 2/2 passed
- `SeverityToBannerLevelTest` — 4/4 passed

### AI Agents
- Agent tracking, tools, and orchestration tests: all passed
- Prompt injection filter tests: all passed
- Forecasting agent comprehensive tests: all passed

### Purchasing
- Workflow model and service tests: all passed
- Email task retry/backoff tests: all passed

### Forecasting
- Prophet engine tests: all passed
- Forecasting service tests: all passed

### Ingestion
- Chat pipeline tests: all passed
- Transcription serializer MIME validation: passed
- Invoice scan serializer tests: all passed

### Other Unit Tests
- Authentication: all passed
- Inventory: all passed
- Audit: all passed
- Core: all passed

---

## Integration Tests (381 passed)

### Chat Endpoint
- `test_chat_with_nonexistent_conversation_returns_404` — PASSED (was failing with 500)
- All chat pipeline integration tests: passed
- Timeout handling: passed
- RAG service unavailable: passed
- LLM quota exhausted: passed

### Authentication Flow
- Registration, login, token refresh: all passed
- Email verification flow: all passed

### Inventory CRUD
- Full CRUD operations: all passed
- Stock level management: all passed

### Purchasing Workflow
- PO creation through approval: all passed
- Supplier timeout detection: all passed

### Forecasting
- Forecast generation and retrieval: all passed
- Agent run tracking: all passed

---

## Golden Dataset Tests (30 passed)

All 30 annotated natural language queries executed successfully against the NL query pipeline.

---

## Linting Results

### Python (Ruff)
```
All checks passed!
```
- Line length: 100 (configured in ruff.toml)
- Ignored: E501 (line too long)

### TypeScript
```
npx tsc --noEmit — no errors
```

### JavaScript/React (ESLint)
```
npm run lint — no errors
```

---

## Regression Verification

### Changed Files and Test Coverage

| File Changed | Tests Verified |
|-------------|----------------|
| `config/exception_handler.py` | 7 exception handler tests |
| `apps/forecasting/views.py` | 3 forecasting view tests |
| `ai/agents/forecasting_agent.py` | Agent tracking + tool tests |
| `ai/agents/decision_agent.py` | Agent orchestration tests |
| `ai/agents/purchasing_agent.py` | Workflow model + service tests |
| `infrastructure/email.py` | Email task + monitoring tests |
| `apps/authentication/services.py` | Auth flow integration tests |
| `apps/monitoring/notifications.py` | 5 alert email tests |
| `apps/purchasing/tasks.py` | Celery task tests |
| `apps/purchasing/timeout_tasks.py` | Timeout detection tests |
| `apps/forecasting/tasks.py` | Forecast task tests |
| `apps/audit/tasks.py` | Audit task tests |
| `core/management/commands/seed_data.py` | Command argument tests |
| `apps/notifications/views.py` | 16 notification API tests |
| `apps/ingestion/serializers.py` | Serializer validation tests |
| `apps/ingestion/chat_pipeline.py` | Chat pipeline integration tests |

### No Regressions Detected

All existing tests continue to pass after modifications. New behavior is covered by updated test expectations.
