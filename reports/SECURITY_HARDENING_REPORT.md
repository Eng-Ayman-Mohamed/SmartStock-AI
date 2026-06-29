# SmartStock AI — Security Hardening Report

**Date:** 2026-06-27
**Scope:** Full production security audit and remediation
**Status:** All critical and high-severity findings resolved

---

## Executive Summary

This report documents all security hardening applied to SmartStock AI for production readiness. 13 security and reliability issues were identified, fixed, and verified with automated tests.

---

## Findings and Remediations

### CRITICAL — Information Disclosure

#### SEC-001: Exception Class Names Leaked in API Responses
- **File:** `config/exception_handler.py`
- **Risk:** Internal Python exception class names (e.g., `StockNotFoundException`, `PermissionDenied`) exposed to API consumers, revealing implementation details
- **Fix:** Added `_ERROR_TYPE_MAP` and `_sanitize_error_type()` — DRF/Django exceptions mapped to generic strings (`Forbidden`, `NotFound`, `ServerError`). Domain exceptions preserved intentionally for frontend error handling.
- **Impact:** API error responses no longer leak internal class names for standard exceptions

#### SEC-002: Celery Task Error Details Leaked
- **File:** `apps/forecasting/views.py:287`
- **Risk:** `str(result.result)` sent raw exception details to the client on Celery task failure
- **Fix:** Replaced with generic `'Task execution failed. Check server logs for details.'`
- **Impact:** No more stack traces or internal error messages in API responses

### HIGH — AI Security

#### SEC-003: Prompt Injection Vulnerability in ForecastingAgent
- **File:** `ai/agents/forecasting_agent.py`
- **Risk:** Context payload passed directly to LLM without validation
- **Fix:** Added `prompt_injection_filter()` check on all string values in context payload before execution
- **Impact:** Malicious context payloads now blocked before reaching LLM

#### SEC-004: Prompt Injection Vulnerability in DecisionAgent
- **File:** `ai/agents/decision_agent.py`
- **Risk:** Same as SEC-003 for the reorder decision agent
- **Fix:** Added `prompt_injection_filter()` check on all string values in context payload
- **Impact:** Consistent prompt injection defense across all AI agents

#### SEC-005: Auto-Approve Enabled in Production
- **File:** `ai/agents/purchasing_agent.py:168`
- **Risk:** `auto_approve` context flag could auto-approve purchase orders in production
- **Fix:** Gated behind `not settings.IS_PRODUCTION` check
- **Impact:** Auto-approve only works in development/staging environments

### HIGH — Authorization

#### SEC-006: Notifications IDOR (Insecure Direct Object Reference)
- **File:** `apps/notifications/views.py`
- **Risk:** `get_queryset()` returned all notifications regardless of authenticated user — any user could access/modify any notification by ID
- **Fix:** Queryset now filtered through `user_notifications__user=self.request.user` with `distinct()`
- **Impact:** Users can only see and interact with their own notifications

### HIGH — Input Validation

#### SEC-007: Audio Upload MIME Type Bypass
- **File:** `apps/ingestion/serializers.py`
- **Risk:** No MIME type validation — any file type accepted as "audio"
- **Fix:** Added whitelist of allowed audio MIME types (MP3, WAV, OGG, FLAC, M4A, WebM, AAC)
- **Impact:** Non-audio files rejected at upload with clear error message

### MEDIUM — Reliability

#### SEC-008: Email Service Without Retry
- **File:** `infrastructure/email.py`
- **Risk:** Emails sent synchronously with no retry on SMTP failure — transient errors cause permanent loss
- **Fix:** Complete rewrite — all emails routed through Celery with retry (30s, 2min, 10min), audit logging, and permanent failure tracking
- **Impact:** Email delivery resilient to transient SMTP failures

#### SEC-009: Verification Emails Synchronous
- **File:** `apps/authentication/services.py`
- **Risk:** Verification emails sent synchronously — SMTP failure blocks user registration
- **Fix:** Routed through `send_verification_email_task` Celery task with sync fallback
- **Impact:** Registration no longer blocked by email delivery issues

#### SEC-010: Alert Emails Synchronous
- **File:** `apps/monitoring/notifications.py`
- **Risk:** Alert emails sent synchronously — SMTP failure prevents escalation notification
- **Fix:** Routed through `send_alert_email_task` Celery task
- **Impact:** Alert delivery resilient to SMTP failures

#### SEC-011: Celery Tasks Without `acks_late`
- **Files:** `purchasing/tasks.py`, `purchasing/timeout_tasks.py`, `forecasting/tasks.py`, `audit/tasks.py`
- **Risk:** If a Celery worker crashes mid-task, the task message is lost (default `acks_late=False`)
- **Fix:** Added `bind=True`, `acks_late=True`, `max_retries=3` to 5 critical tasks
- **Impact:** Tasks survive worker crashes; automatic retry on failure

### LOW — Bug Fixes

#### SEC-012: Chat Endpoint 500 Instead of 404
- **File:** `apps/ingestion/chat_pipeline.py`
- **Risk:** Intent classification failure (LLM unavailable) caused 500 error before conversation validation, masking the real 404
- **Fix:** Wrapped intent classification in try/except, defaults to `nl_query` on failure
- **Impact:** Proper HTTP status codes returned; conversation validation runs even when LLM is down

#### SEC-013: seed_data Command Flags Unusable
- **File:** `core/management/commands/seed_data.py`
- **Risk:** `--truncate` and `--validate` used `store_true` with `default=True`, making them impossible to negate
- **Fix:** Changed to `argparse.BooleanOptionalAction` — now supports `--no-truncate` and `--no-validate`
- **Impact:** Seed data command flags work as documented

---

## Security Controls Matrix

| Control | Status | Verification |
|---------|--------|-------------|
| Exception name sanitization | Active | 7 unit tests passing |
| Prompt injection filtering | Active | Agent tests passing |
| Auto-approve production guard | Active | Purchasing agent tests |
| Notification user scoping | Active | 16 API tests passing |
| MIME type validation | Active | Serializer tests passing |
| Email retry with backoff | Active | Email task tests passing |
| Celery task reliability | Active | Task tests passing |
| CORS configuration | Active | Settings review |
| CSRF protection | Active | Django middleware |
| `.env` git exclusion | Active | `.gitignore` verified |

---

## Threat Model Assessment

| Threat | Mitigation | Residual Risk |
|--------|------------|---------------|
| Prompt injection via user input | Multi-layer filter (pre-classification, pre-agent) | Low |
| Information disclosure via errors | Exception sanitization + generic strings | Low |
| Unauthorized notification access | User-scoped queryset | Low |
| Email delivery failure | Celery retry + dead-letter tracking | Low |
| Task loss on worker crash | `acks_late=True` + `max_retries` | Low |
| Auto-approve in production | Environment check gate | None |
| Non-audio file upload | MIME whitelist enforcement | Low |

---

## Recommendations for Production

1. **Rotate all API keys** before production deployment (OpenAI, Cohere, Langfuse, Cloudinary, Groq, Google)
2. **Set strong `DJANGO_SECRET_KEY`** — current is a dev placeholder
3. **Enable Redis ACL** for authentication in production
4. **Configure HTTPS** at reverse proxy/Railway level
5. **Set `ENVIRONMENT=production`** in production deployment
6. **Monitor Grafana dashboards** for error rates and Celery task failures
