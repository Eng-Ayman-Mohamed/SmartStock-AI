# SmartStock AI — Go-Live Checklist

**Date:** 2026-06-27
**Certified By:** Automated Audit System

---

## Pre-Deployment Checklist

### Security
- [x] Exception class names sanitized in API responses
- [x] Prompt injection filter applied to all AI agents
- [x] Auto-approve disabled in production environment
- [x] Notifications scoped to authenticated user (IDOR fixed)
- [x] Audio upload MIME type validation enforced
- [x] `.env` excluded from git via `.gitignore`
- [x] No secrets committed to repository
- [x] CORS configured for allowed origins only
- [x] CSRF trust origins configured

### Reliability
- [x] Email service uses Celery with retry/backoff
- [x] Verification emails async with fallback
- [x] Alert emails async with retry
- [x] Critical Celery tasks use `bind=True` + `acks_late`
- [x] Chat endpoint handles LLM unavailability gracefully
- [x] Prompt injection filter exception handled gracefully

### Testing
- [x] 1,754 tests passing (0 failures)
- [x] Unit tests: 1,343 passed
- [x] Integration tests: 381 passed
- [x] Golden dataset tests: 30 passed
- [x] Ruff lint: all checks passed
- [x] TypeScript: no errors
- [x] ESLint: no errors

### Infrastructure
- [x] Docker compose builds successfully
- [x] All 10 services healthy
- [x] Backend health endpoints responding (live + ready)
- [x] Frontend serving on port 5173
- [x] PostgreSQL (pgvector/pg16) running
- [x] Redis running
- [x] Celery worker connected and processing
- [x] Celery beat scheduled
- [x] Mailpit SMTP test server running
- [x] Prometheus + Grafana + Alertmanager monitoring stack

### Code Quality
- [x] Clean Architecture layers enforced (Views → Services → Repositories → DB)
- [x] No DB queries in views
- [x] AI layer isolated (no direct imports from apps/)
- [x] Domain layer imports nothing from apps/ or ai/
- [x] Error responses use standard envelope format
- [x] Domain exceptions preserved for frontend error handling

## Post-Deployment Checklist

### Immediate (Day 1)
- [ ] Rotate all API keys (OpenAI, Cohere, Langfuse, Cloudinary, Groq, Google)
- [ ] Set production `DJANGO_SECRET_KEY`
- [ ] Configure production database (Railway Neon/Postgres)
- [ ] Configure production Redis (Railway plugin)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `ESCALATION_RECIPIENT_EMAILS` for production
- [ ] Verify health endpoints from external monitoring

### Short-Term (Week 1)
- [ ] Run end-to-end email certification (3 cycles × 4 email types × 3 suppliers)
- [ ] Run purchase order workflow certification (5 cycles)
- [ ] Run agent certification (20 scenarios × 3 agents)
- [ ] Load testing (100 concurrent users)
- [ ] Stress testing (peak load)

### Medium-Term (Month 1)
- [ ] Monitor error rates in Grafana
- [ ] Review Celery task execution logs
- [ ] Verify backup/restore procedures
- [ ] Document runbook for on-call

## Service Ports

| Service | External Port | Internal Port | Protocol |
|---------|--------------|---------------|----------|
| Backend API | 8000 | 8000 | HTTP |
| Frontend | 5173 | 5173 | HTTP |
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6379 | TCP |
| Mailpit UI | 8025 | 8025 | HTTP |
| Mailpit SMTP | 1025 | 1025 | TCP |
| Prometheus | 9090 | 9090 | HTTP |
| Alertmanager | 9093 | 9093 | HTTP |
| Grafana | 3001 | 3000 | HTTP |

## Rollback Procedure

```bash
# Stop all services
docker compose down

# Restore from previous image tag
docker compose up -d --build

# Verify health
curl http://localhost:8000/api/health/live/
curl http://localhost:8000/api/health/ready/
```
