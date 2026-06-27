# SMTP Audit Report

**Audit Date:** 2026-06-25
**Scope:** Full SmartStock AI monorepo (backend + frontend + infrastructure)
**Mode:** READ-ONLY — No files modified

---

## Executive Verdict

| Metric | Value |
|--------|-------|
| SMTP_FUNCTIONALITY_EXISTS | YES |
| SMTP_CONFIGURATION_FOUND | YES |
| EMAIL_SENDING_WORKING | PARTIAL — 3 of 4 subsystems functional, purchasing email dispatch is ORPHANED |
| CRITICAL_ISSUE | PurchasingAgent HITL migration removed email dispatch from agent, but backend never gained post-approval email sending |

---

## SMTP Settings Location

| File | Status | Details |
|------|--------|---------|
| `config/settings/production.py:49-55` | ACTIVE | Full SMTP config: backend, host, port, user, password, TLS, from_email |
| `config/settings/development.py:10-19` | ACTIVE | Conditional: SMTP if `EMAIL_HOST` set, else console backend |
| `config/settings/test.py:128` | ACTIVE | `locmem.EmailBackend` for tests |
| `config/validators.py:24-29` | ACTIVE | Optional env vars with defaults |
| `smartstock-backend/.env` | ACTIVE | `EMAIL_HOST=localhost`, `EMAIL_PORT=25`, no user/password |
| `smartstock-backend/.env.docker` | ACTIVE | Same: `localhost:25`, no auth |
| `smartstock-backend/.env.example` | ACTIVE | All 5 vars documented |
| `monitoring/alertmanager/alertmanager.yml` | ACTIVE | Uses env var interpolation for SMTP |

---

## Environment Variables Found

| Variable | `.env` | `.env.docker` | `.env.example` | `production.py` | `development.py` |
|----------|--------|---------------|----------------|-----------------|-------------------|
| `EMAIL_HOST` | `localhost` | `localhost` | empty | `os.environ.get()` | `os.environ.get()` |
| `EMAIL_PORT` | `25` | `25` | `587` | `os.environ.get(, 587)` | `os.environ.get(, 587)` |
| `EMAIL_HOST_USER` | **MISSING** | **MISSING** | empty | `os.environ.get()` | `os.environ.get()` |
| `EMAIL_HOST_PASSWORD` | **MISSING** | **MISSING** | empty | `os.environ.get()` | `os.environ.get()` |
| `EMAIL_USE_TLS` | N/A | N/A | N/A | `True` (hardcoded) | `True` (hardcoded) |
| `DEFAULT_FROM_EMAIL` | **MISSING** | **MISSING** | `noreply@smartstock.ai` | `os.environ.get(, 'noreply@smartstock.ai')` | `os.environ.get(, 'owael20003@gmail.com')` |
| `ESCALATION_RECIPIENT_EMAILS` | `ops@smartstock.ai` | `ops@smartstock.ai` | empty | via settings | via settings |

**Configuration gap:** `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are not set anywhere. SMTP will attempt unauthenticated connection to `localhost:25`.

---

## Email Usage Locations

### Subsystem 1: Authentication — Email Verification

| File | Function | Purpose | Still Active? |
|------|----------|---------|---------------|
| `apps/authentication/services.py:23-50` | `send_verification_email()` | Sends verification link after registration | YES |
| `apps/authentication/views.py:117-118` | `RegisterView.post()` | Calls `send_verification_email()` on new user | YES |
| `apps/authentication/views.py:302-303` | `ResendVerificationView.post()` | Calls `send_verification_email()` on resend | YES |
| `apps/authentication/views.py:270` | `VerifyEmailView.post()` | Verifies token (no email sent) | YES |

**Flow:** User registers → `send_verification_email()` → `django.core.mail.send_mail()` → SMTP

### Subsystem 2: Purchasing — PO Email Dispatch to Suppliers

| File | Function | Purpose | Still Active? |
|------|----------|---------|---------------|
| `apps/purchasing/email_tasks.py:50-191` | `send_email_with_retry()` | Celery task: send PO email with retry logic (30s→2min→10min) | YES (code exists) |
| `apps/purchasing/email_tasks.py:194-228` | `_trigger_escalation()` | Creates escalation notification on permanent email failure | YES (code exists) |
| `ai/agents/tools/email_send.py:13-80` | `EmailSendTool.run()` | Agent tool: dispatches PO to supplier via `send_email_with_retry.delay()` | YES (code exists) |
| `apps/purchasing/templates/purchasing/po_email.txt` | Template | PO email body template | YES (file exists) |
| `ai/agents/purchasing_agent.py` | Agent workflow | Previously called `EmailSendTool` | **NO — REMOVED by HITL migration** |
| `apps/purchasing/services.py` | `approve_po()` | Changes status to `approved` | YES — but does NOT trigger email |

**CRITICAL FINDING:** The email dispatch pipeline is fully implemented (`EmailSendTool` → `send_email_with_retry` → SMTP), but the trigger chain is broken:

1. PurchasingAgent creates PO as `pending_approval` → stops (correct)
2. Human approves via `approve_po()` → status changes to `approved` → **no email sent**
3. `EmailSendTool` exists and works → but nothing calls it after approval
4. No Celery beat task polls for `approved` POs to dispatch emails
5. No API endpoint triggers email after approval

### Subsystem 3: Monitoring — Alert Emails

| File | Function | Purpose | Still Active? |
|------|----------|---------|---------------|
| `apps/monitoring/notifications.py:11-49` | `send_alert_email()` | Sends email for firing alert events | YES |
| `apps/monitoring/alerts.py:150-178` | `_fire_alert()` | Calls `send_alert_email()` when alert fires | YES |
| `apps/monitoring/tasks.py:18-35` | `evaluate_all_alerts_task()` | Celery beat: evaluates alerts every 5 min | YES |
| `config/settings/base.py:360-363` | Beat schedule | `evaluate-monitoring-alerts` every 300s | YES |

**Flow:** Celery beat → `evaluate_all_alerts_task()` → `_fire_alert()` → `send_alert_email()` → `django.core.mail.send_mail()` → SMTP

**Condition:** Only sends if `ESCALATION_RECIPIENT_EMAILS` is non-empty (it is: `ops@smartstock.ai`).

### Subsystem 4: Escalation — PO Escalation Emails

| File | Function | Purpose | Still Active? |
|------|----------|---------|---------------|
| `apps/notifications/service.py:41-100` | `create_escalation_notification()` | Creates escalation + sends email | YES |
| `apps/notifications/service.py:103-130` | `_send_escalation_email()` | Sends escalation email via `EmailService` | YES |
| `infrastructure/email.py:5-12` | `EmailService.send()` | Wrapper around `django.core.mail.send_mail()` | YES |
| `apps/purchasing/timeout_tasks.py:99-119` | `_trigger_escalation()` | Creates escalation on supplier timeout | YES |
| `apps/purchasing/timeout_tasks.py:13-74` | `check_supplier_timeouts()` | Celery beat: checks timeouts hourly | YES |
| `config/settings/base.py:356-358` | Beat schedule | `check-supplier-timeouts` every 3600s | YES |

**Flow 1 (Supplier Timeout):** Celery beat → `check_supplier_timeouts()` → `_trigger_escalation()` → `create_escalation_notification()` → `_send_escalation_email()` → `EmailService.send()` → SMTP

**Flow 2 (Email Delivery Failed):** `send_email_with_retry()` fails permanently → `_trigger_escalation()` → same chain as above

### Subsystem 5: AlertManager (External)

| File | Function | Purpose | Still Active? |
|------|----------|---------|---------------|
| `monitoring/alertmanager/alertmanager.yml:22-39` | Email receivers | Sends Prometheus alert emails | YES |
| `docker-compose.yml:160-176` | AlertManager container | Runs alertmanager | YES |

**Flow:** Prometheus → AlertManager → SMTP email to `ESCALATION_RECIPIENT_EMAILS`

**Condition:** Requires `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` as env vars in the container. Docker Compose uses `env_file: .env.docker` which has `EMAIL_HOST=localhost:25` but no auth credentials.

---

## Email Features Still Active

1. **User registration email verification** — fully functional
2. **Resend verification email** — fully functional
3. **Monitoring alert emails** — functional (if SMTP is configured)
4. **Escalation notification emails** — functional (if SMTP is configured)
5. **Supplier timeout escalation** — functional (email path works)
6. **Email retry with exponential backoff** — fully implemented
7. **Escalation deduplication** (24h window) — functional
8. **AlertManager email routing** — configured but untested with localhost SMTP

---

## Email Features Removed / Broken

1. **PurchasingAgent email dispatch** — `EmailSendTool` no longer imported/used by agent after HITL migration
2. **Post-approval email dispatch** — `approve_po()` changes status but does not trigger email sending
3. **No automated email dispatch task** — No Celery beat task polls for `approved` POs to send emails

---

## Git History Results

| Commit | Date | Change |
|--------|------|--------|
| `a008267` | Initial | `EmailSendTool`, `email_tasks.py`, infrastructure email scaffolded |
| `7094778` | Agent logic | PurchasingAgent wired up with `EmailSendTool` |
| `67c8f1e` | PO template | Added `po_email.txt` template |
| `35bdff5` | 2026-06-24 | Added email verification system with Brevo SMTP |
| `fa4dc76` | 2026-06-24 | Fixed email verification idempotency (Gmail pre-fetch) |
| `a0e8786` | Recent | HITL migration — Removed `EmailSendTool` usage from PurchasingAgent, removed `_send_email()`, `_poll_for_confirmation()` |

**Verdict:** Email code was never deleted from the repository. It was disconnected from the purchasing agent workflow during the HITL migration. All email modules, tasks, templates, and infrastructure remain intact.

---

## Runtime Test Result

| Test | Result | Details |
|------|--------|---------|
| Django settings load | PASS | `EMAIL_BACKEND = smtp.EmailBackend` loads in development (EMAIL_HOST=localhost is set) |
| `send_mail` importable | PASS | `django.core.mail.send_mail` available |
| `EmailMessage` importable | PASS | `django.core.mail.EmailMessage` available |
| `smtplib` importable | PASS | Python stdlib |
| `EmailService` functional | PASS | Simple wrapper, will call `send_mail` |
| `send_email_with_retry` functional | PASS | Celery task, calls `EmailMessage.send()` |
| `EmailSendTool` functional | PASS | Calls `send_email_with_retry.delay()` |
| Email template exists | PASS | `purchasing/po_email.txt` at correct app directory |
| SMTP connection to localhost:25 | UNTESTED | No local SMTP server in Docker stack |
| Actual email delivery | FAIL | No SMTP server configured — `localhost:25` has no MTA running |

---

## Missing Configuration

1. **No SMTP server in Docker stack** — Docker Compose has no mail container (e.g., `mailhog`, `mailpit`, `postal`). `EMAIL_HOST=localhost` points to nothing.
2. **No `EMAIL_HOST_USER`** — Not set in `.env` or `.env.docker`
3. **No `EMAIL_HOST_PASSWORD`** — Not set in `.env` or `.env.docker`
4. **No `DEFAULT_FROM_EMAIL` in runtime** — Falls back to code default `noreply@smartstock.ai` (production) or `owael20003@gmail.com` (development)
5. **Port mismatch** — `.env` uses port 25 (unencrypted), but `EMAIL_USE_TLS=True` is hardcoded (port 25 typically doesn't use TLS; port 587 does)
6. **TLS/Port conflict** — Settings force `EMAIL_USE_TLS=True` but port 25 is configured. Standard SMTP submission is port 587 with TLS.
7. **`FRONTEND_URL` missing from `.env`** — `development.py` defaults to `https://smart-stock-dev.vercel.app`, needed for email verification links

---

## Recommendations

### P0 — Critical (Email dispatch is broken in production)

1. **Add post-approval email dispatch to `approve_po()`** — After status changes to `approved`, call `send_email_with_retry.delay()` (or `EmailSendTool.run()`) to dispatch the PO to the supplier. This is the gap left by the HITL migration.

2. **OR add a Celery beat task** that polls for `status='approved'` POs and dispatches emails automatically.

3. **Add a mail server to Docker Compose** — Add `mailpit` or `mailhog` service for local development email testing:

```yaml
mailpit:
  image: axllent/mailpit
  ports:
    - "1025:1025"  # SMTP
    - "8025:8025"  # Web UI
```

Set `EMAIL_HOST=mailpit`, `EMAIL_PORT=1025`, remove `EMAIL_USE_TLS`.

### P1 — High (Production email won't work)

4. **Set real SMTP credentials** — Configure `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` with actual provider (Brevo, SendGrid, etc.) in production environment.

5. **Fix TLS/Port mismatch** — Either:
   - Use port 587 with TLS (recommended), or
   - Use port 25 without TLS (local only)

6. **Set `DEFAULT_FROM_EMAIL`** in production environment (currently defaults to `noreply@smartstock.ai` which is fine).

### P2 — Medium (Robustness)

7. **Add `DEFAULT_FROM_EMAIL` to `.env.example`** — Already present, no action needed.

8. **Add `ESCALATION_RECIPIENT_EMAILS` to `.env.example`** — Already present, no action needed.

9. **Consider adding email delivery metrics** — Track sent/failed emails in Prometheus via the monitoring subsystem.

10. **Verify AlertManager SMTP** — The alertmanager.yml uses env var interpolation. Ensure the alertmanager container receives `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`.

---

## Architecture Diagram — Email Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMAIL SUBSYSTEMS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. AUTH VERIFICATION                                            │
│     RegisterView → send_verification_email() → send_mail() ─┐   │
│                                                              │   │
│  2. PO DISPATCH (BROKEN)                                     │   │
│     ApproveView → approve_po() [NO EMAIL]                    │   │
│     EmailSendTool → send_email_with_retry.delay() ────────┐  │   │
│     [DISCONNECTED — nothing calls this after approval]    │  │   │
│                                                            │  │   │
│  3. MONITORING ALERTS                                      │  │   │
│     evaluate_all_alerts_task() → _fire_alert()            │  │   │
│     → send_alert_email() → send_mail() ─────────────────┐ │  │   │
│                                                          │ │  │   │
│  4. ESCALATION                                           │ │  │   │
│     check_supplier_timeouts() → _trigger_escalation()   │ │  │   │
│     → create_escalation_notification()                  │ │  │   │
│     → _send_escalation_email() → EmailService.send() ─┐│ │  │   │
│                                                       ││ │  │   │
│  5. ALERTMANAGER                                       ││ │  │   │
│     Prometheus → AlertManager → SMTP ─────────────────┤│ │  │   │
│                                                       ││ │  │   │
│                                                       ▼▼ ▼  ▼   │
│                                              ┌──────────────┐   │
│                                              │  SMTP Backend │   │
│                                              │  (localhost:25│   │
│                                              │  or provider) │   │
│                                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Source File Index

### Production Code (Email-Related)

| File | Lines | Role |
|------|-------|------|
| `config/settings/production.py` | 63 | SMTP backend configuration |
| `config/settings/development.py` | 27 | Conditional SMTP/console backend |
| `config/settings/test.py` | 131 | In-memory email backend |
| `config/settings/base.py:351-363` | — | Celery beat schedule for timeout/alert tasks |
| `config/validators.py` | 55 | Optional env var defaults |
| `infrastructure/email.py` | 12 | `EmailService` wrapper |
| `apps/authentication/services.py` | 77 | Email verification (registration) |
| `apps/authentication/views.py` | 509 | Register, resend, verify endpoints |
| `apps/purchasing/email_tasks.py` | 228 | `send_email_with_retry` Celery task + escalation trigger |
| `apps/purchasing/services.py` | — | `approve_po()` — no email trigger |
| `apps/purchasing/timeout_tasks.py` | 119 | Supplier timeout detection + escalation |
| `apps/purchasing/templates/purchasing/po_email.txt` | 14 | PO email template |
| `apps/monitoring/notifications.py` | 86 | `send_alert_email()` |
| `apps/monitoring/alerts.py` | 248 | Alert evaluation → email notification |
| `apps/monitoring/tasks.py` | 154 | Celery tasks including alert evaluation |
| `apps/notifications/service.py` | 157 | Escalation notification creation + email |
| `ai/agents/tools/email_send.py` | 80 | `EmailSendTool` (disconnected from agent) |

### Infrastructure

| File | Role |
|------|------|
| `docker-compose.yml` | No mail service; AlertManager configured |
| `monitoring/alertmanager/alertmanager.yml` | Email receivers using env var interpolation |
| `.env` | `EMAIL_HOST=localhost`, `EMAIL_PORT=25`, no auth |
| `.env.docker` | Same as `.env` |
| `.env.example` | All email vars documented |

### Test Files (Email-Related)

| File | Tests |
|------|-------|
| `tests/unit/test_email_retry.py` | Retry logic, escalation, SMTP error handling |
| `tests/unit/test_email_tasks_extended.py` | Extended email task tests |
| `tests/unit/test_escalation_notifications.py` | Escalation notification creation + email |
| `tests/unit/test_monitoring_notifications.py` | Alert email send success/failure |
| `tests/unit/test_monitoring_alerts_extended.py` | Alert evaluation with email |
| `tests/unit/test_external_mocks.py` | External mock with email backend |
