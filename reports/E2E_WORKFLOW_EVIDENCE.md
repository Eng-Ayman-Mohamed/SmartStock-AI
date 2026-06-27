# SmartStock AI — E2E Workflow Evidence

**Date:** 2026-06-27
**Stack:** Docker Compose (10 services)
**Duration:** Full stack boot verified, all services healthy

---

## Docker Stack Status

```
NAME                      STATUS                        PORTS
smartstock_alertmanager   Up (healthy)                  127.0.0.1:9093->9093/tcp
smartstock_backend        Up (healthy)                  0.0.0.0:8000->8000/tcp
smartstock_celery         Up (healthy)                  8000/tcp
smartstock_celery_beat    Up (healthy)                  8000/tcp
smartstock_db             Up (healthy)                  0.0.0.0:5432->5432/tcp
smartstock_frontend       Up (healthy)                  0.0.0.0:5173->5173/tcp
smartstock_grafana        Up (healthy)                  127.0.0.1:3001->3000/tcp
smartstock_mailpit        Up (healthy)                  0.0.0.0:8025->8025/tcp
smartstock_prometheus     Up (healthy)                  127.0.0.1:9090->9090/tcp
smartstock_redis          Up (healthy)                  0.0.0.0:6379->6379/tcp
```

---

## Health Endpoint Verification

### Backend Liveness
```bash
$ curl http://localhost:8000/api/health/live/
{"status":"success","data":{"status":"ok"},"meta":{}}
```

### Backend Readiness
```bash
$ curl http://localhost:8000/api/health/ready/
{"status":"success","data":{"status":"ok"},"meta":{}}
```

### Frontend
```bash
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/
200
```

### OpenAPI Schema
```bash
$ curl -s http://localhost:8000/api/schema/ -o /dev/null -w "%{http_code}"
200
```

---

## Service Dependency Chain

```
PostgreSQL (db:5432) ─────┐
Redis (redis:6379) ───────┤
                          ├──→ Backend (8000) ──→ Frontend (5173)
Mailpit (1025/8025) ──────┤        │
                          │        ├──→ Celery Worker
                          │        └──→ Celery Beat
Prometheus (9090) ────────┤
Alertmanager (9093) ──────┤
Grafana (3001) ───────────┘
```

---

## Email Delivery Evidence

### Mailpit SMTP Capture
All emails during testing captured by Mailpit for inspection:
- SMTP server: `localhost:1025`
- Web UI: `http://localhost:8025`

### Email Task Execution
```
Task infrastructure.email.send_email_task[6f6b9a7e-...] succeeded:
  {'status': 'sent', 'message_id': 'email-1ccb479e30e7', 'recipient': 'admin@example.com', 'attempts': 1}

Task infrastructure.email.send_alert_email_task[5d31c71f-...] succeeded:
  {'status': 'queued', 'results': [{'recipient': 'admin@example.com', 'task_id': '6f6b9a7e-...'}]}
```

---

## Celery Worker Evidence

### Worker Startup
```
[INFO/MainProcess] Connected to redis://redis:6379/0
[INFO/MainProcess] celery@059188bf54b3 ready.
```

### Beat Scheduler
```
[INFO] celery@... beat: Starting...
```

---

## Test Execution Evidence

### Unit Tests
```bash
$ DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest tests/ -q --ignore=tests/integration
1343 passed, 136 warnings in 69.30s
```

### Integration Tests
```bash
$ DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest tests/integration/ -q
381 passed, 1 warning in 50.32s
```

### Golden Dataset Tests
```bash
$ DJANGO_SETTINGS_MODULE=config.settings.test python -m pytest tests/golden_dataset/ -q
30 passed in 0.86s
```

### Linting
```bash
$ ruff check .
All checks passed!

$ npx tsc --noEmit
(no errors)

$ npm run lint
(no errors)
```

---

## API Response Format Evidence

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "meta": {}
}
```

### Error Response
```json
{
  "status": "error",
  "error": "ServerError",
  "message": "An unexpected error occurred.",
  "code": 500
}
```

Note: Internal exception class names are sanitized. Domain exceptions (StockNotFoundException, etc.) preserved for frontend error handling.

---

## Key Bug Fix Evidence

### Chat Endpoint 500→404
**Before:** Nonexistent conversation_id + unavailable LLM = HTTP 500
**After:** Nonexistent conversation_id + unavailable LLM = HTTP 404 with `"message": "Conversation not found."`

Verified by: `tests/integration/test_chat_endpoint.py::ChatEndpointTests::test_chat_with_nonexistent_conversation_returns_404` — PASSED

---

## Certification

| Criterion | Status |
|-----------|--------|
| All 10 Docker services healthy | PASS |
| Backend API responding | PASS |
| Frontend serving | PASS |
| Celery worker processing | PASS |
| 1,754 tests passing | PASS |
| Lint checks passing | PASS |
| Type checks passing | PASS |
| Email delivery verified | PASS |
| Security hardening applied | PASS |
| Clean Architecture compliance | PASS |

**E2E Workflow Status: CERTIFIED**
