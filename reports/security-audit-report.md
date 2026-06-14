# SmartStock AI — Security Audit Report

**Date:** June 14, 2026  
**Auditor:** Security Engineer (Automated)  
**Scope:** Full-stack (Django 5 + DRF backend, React 19 + Vite frontend)  
**Methodology:** Static analysis, configuration review, OWASP Top 10 mapping

---

## Executive Summary

SmartStock AI implements a solid security baseline: JWT with HttpOnly cookie refresh tokens, RBAC with role hierarchy, prompt injection filtering, and production-grade Django security middleware. However, **12 issues** were identified ranging from **Critical** to **Low** severity.

| Severity | Count |
|----------|-------|
| Critical | 2     |
| High     | 4     |
| Medium   | 4     |
| Low      | 2     |

---

## Critical Issues

### SEC-001: Hardcoded Grafana Credentials in docker-compose.yml

**Severity:** CRITICAL  
**File:** `docker-compose.yml:208-209`  
**OWASP:** A07:2021 – Identification and Authentication Failures

```yaml
GF_SECURITY_ADMIN_USER: admin
GF_SECURITY_ADMIN_PASSWORD: smartstock
```

**Impact:** Default/hardcoded credentials for Grafana dashboard. Anyone with access to the repo or container can log in to the monitoring dashboard.

**Remediation:**
- Move credentials to `.env` file: `${GF_ADMIN_USER}` / `${GF_ADMIN_PASSWORD}`
- Use strong, unique passwords in production
- Enable Grafana LDAP/OAuth authentication for production

---

### SEC-002: Django SECRET_KEY Hardcoded Fallback

**Severity:** CRITICAL  
**File:** `config/settings/base.py:16`  
**OWASP:** A02:2021 – Cryptographic Failures

```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
```

**Impact:** If `DJANGO_SECRET_KEY` env var is not set, the insecure default is used. This allows session forgery, JWT signing bypass, and CSRF token prediction.

**Remediation:**
- Remove the default fallback entirely
- Raise `ImproperlyConfigured` if `DJANGO_SECRET_KEY` is not set
- Ensure `config/validators.py` enforces this (it lists `DJANGO_SECRET_KEY` but the base settings loads before validators run)

---

## High Issues

### SEC-003: ALLOWED_HOSTS Wildcard in .env

**Severity:** HIGH  
**File:** `.env:5`, `config/settings/base.py:20`  
**OWASP:** A05:2021 – Security Misconfiguration

```
ALLOWED_HOSTS=localhost,127.0.0.1,*
```

**Impact:** The `*` wildcard allows the application to serve requests for any hostname, enabling HTTP Host header attacks and cache poisoning.

**Remediation:**
- Remove `*` from `ALLOWED_HOSTS` in production
- Use explicit domain names only: `smart-stock-dev.vercel.app,your-domain.com`

---

### SEC-004: Redis Without Authentication

**Severity:** HIGH  
**File:** `docker-compose.yml:35`, `config/settings/base.py:222-231`  
**OWASP:** A05:2021 – Security Misconfiguration

```yaml
command: redis-server --appendonly yes
# No --requirepass flag
```

```python
'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
```

**Impact:** Redis has no password authentication. Any container on the `smartstock_net` network (or any process on the host if port 6379 is exposed) can read/write to Redis, potentially:
- Inject cache poisoning data
- Read JWT tokens if cached
- Execute Redis commands for data exfiltration

**Remediation:**
- Add `--requirepass ${REDIS_PASSWORD}` to Redis command
- Update `REDIS_URL` to include password: `redis://:${REDIS_PASSWORD}@cache:6379/0`
- Do not expose Redis port 6379 to the host in production

---

### SEC-005: Health Endpoints Exposed Without Authentication

**Severity:** HIGH  
**File:** `apps/health/views.py:32-33, 73-74`  
**OWASP:** A01:2021 – Broken Access Control

```python
class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

class ReadinessView(APIView):
    authentication_classes = []
    permission_classes = []
```

**Impact:** While health endpoints are intentionally unauthenticated for orchestrators, they leak infrastructure status (database connected/disconnected, Redis connected/disconnected). An attacker can use this to:
- Map internal infrastructure
- Detect when dependencies are down for timing attacks

**Remediation:**
- Consider adding a shared secret header for health checks in production
- Or restrict health endpoints to internal networks only via nginx/Django middleware
- At minimum, ensure these endpoints are not logged in access logs

---

### SEC-006: DEBUG Mode Controlled by Environment Variable Without Guard

**Severity:** HIGH  
**File:** `config/settings/base.py:18`  
**OWASP:** A05:2021 – Security Misconfiguration

```python
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
```

**Impact:** Default is `True`. If `DJANGO_DEBUG` is not explicitly set, the app runs in debug mode, leaking stack traces, SQL queries, and internal paths to users.

**Remediation:**
- Change default to `'False'`:
  ```python
  DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
  ```
- Add `DEBUG` to `REQUIRED_ENV_VARS` in validators

---

## Medium Issues

### SEC-007: CORS_ALLOW_CREDENTIALS True in Production

**Severity:** MEDIUM  
**File:** `config/settings/production.py:25`  
**OWASP:** A05:2021 – Security Misconfiguration

```python
CORS_ALLOW_CREDENTIALS = True
```

**Impact:** When combined with overly permissive `CORS_ALLOWED_ORIGINS`, this allows cross-origin requests with credentials (cookies), increasing CSRF and data theft risk.

**Remediation:**
- Ensure `CORS_ALLOWED_ORIGINS` is strictly limited to trusted domains
- Validate that only the frontend domain is allowed
- Consider using `CORS_ALLOW_ORIGINS` instead of `ALLOWED_ORIGINS` (naming is a Django-cors-headers convention)

---

### SEC-008: No Rate Limiting on Health/Readiness Endpoints

**Severity:** MEDIUM  
**File:** `apps/health/views.py`  
**OWASP:** A04:2021 – Insecure Design

**Impact:** Health endpoints have no throttle classes, allowing unlimited requests. An attacker can DDoS these endpoints to consume resources.

**Remediation:**
- Add throttle classes to health endpoints: `throttle_classes = [ScopedRateThrottle]`
- Or handle rate limiting at the nginx/infrastructure level

---

### SEC-009: Prompt Injection Filter Is Pattern-Based Only

**Severity:** MEDIUM  
**File:** `ai/llm/chain.py:169-204`  
**OWASP:** A03:2021 – Injection

```python
def prompt_injection_filter(query: str) -> tuple[bool, str | None]:
    patterns = [
        'ignore previous instructions',
        'ignore all instructions',
        # ... 14 patterns total
    ]
```

**Impact:** The filter uses a fixed list of 14 string patterns. Sophisticated attacks can bypass with:
- Unicode homoglyphs (e.g., "іgnore" with Cyrillic і)
- Encoding tricks (base64, URL encoding)
- Indirect injection via document ingestion
- Multi-language prompts

**Remediation:**
- Add a toxicity/classification model (e.g., OpenAI Moderation API) as a second layer
- Implement input normalization (Unicode NFKD, lowercasing)
- Add rate limiting specifically for AI endpoints
- Consider using LLM-based classifiers for injection detection

---

### SEC-010: JWT Access Token Lifetime Only 15 Minutes

**Severity:** MEDIUM (Informational)  
**File:** `config/settings/base.py:193`  
**OWASP:** A07:2021 – Identification and Authentication Failures

```python
'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
```

**Impact:** While 15 minutes is reasonable, the refresh token lifetime is 7 days (`REFRESH_TOKEN_LIFETIME: timedelta(days=7)`). If a refresh token is compromised, the attacker has 7 days of access.

**Remediation:**
- Consider reducing refresh token lifetime to 1-3 days
- Implement refresh token rotation on every use (already enabled via `ROTATE_REFRESH_TOKENS: True`)
- Add refresh token reuse detection (family-based token tracking)

---

## Low Issues

### SEC-011: Database Default Credentials

**Severity:** LOW  
**File:** `docker-compose.yml:11-12`, `.env:2`  
**OWASP:** A07:2021 – Identification and Authentication Failures

```yaml
POSTGRES_USER: ${DB_USER:-smartstock}
POSTGRES_PASSWORD: ${DB_PASSWORD:-smartstock}
```

**Impact:** Default database credentials (`smartstock/smartstock`) are used when env vars are not set. These are also present in the `.env` file which is gitignored but may exist in deployment.

**Remediation:**
- Use strong, unique database passwords in production
- Ensure `.env` is never committed to version control (currently gitignored — good)
- Use a secrets manager (Railway variables, Vault, etc.)

---

### SEC-012: Missing SECURE_HSTS_SECONDS in Production

**Severity:** LOW  
**File:** `config/settings/production.py`  
**OWASP:** A05:2021 – Security Misconfiguration

**Impact:** No HTTP Strict Transport Security (HSTS) header configured. Browsers won't enforce HTTPS automatically.

**Remediation:**
- Add to `production.py`:
  ```python
  SECURE_HSTS_SECONDS = 31536000  # 1 year
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  ```

---

## Positive Findings (What's Done Well)

| Area | Status | Details |
|------|--------|---------|
| JWT Refresh Tokens | **PASS** | HttpOnly, Secure, SameSite=Strict cookies |
| RBAC Implementation | **PASS** | 3-tier role hierarchy (viewer/manager/admin) |
| Throttling | **PASS** | Rate limits on anon (20/min), user (100/min), login (5/min), AI (10/min) |
| Django Security Middleware | **PASS** | SecurityMiddleware, CsrfViewMiddleware, XFrameOptionsMiddleware all enabled |
| CORS Configuration | **PASS** | Restrictive allowed origins in production |
| Prompt Injection Defense | **PASS** | Pattern-based filter + output validation |
| Docker Non-Root User | **PASS** | Backend runs as `appuser` (non-root) |
| Password Validators | **PASS** | Django's 4 standard validators enabled |
| Audit Logging | **PASS** | Middleware captures all requests |
| Environment Validation | **PASS** | Required env vars validated at startup |

---

## OWASP Top 10 (2021) Mapping

| # | Category | Findings |
|---|----------|----------|
| A01 | Broken Access Control | SEC-005 (Health endpoints) |
| A02 | Cryptographic Failures | SEC-002 (SECRET_KEY fallback) |
| A03 | Injection | SEC-009 (Prompt injection filter) |
| A04 | Insecure Design | SEC-008 (No rate limit on health) |
| A05 | Security Misconfiguration | SEC-003, SEC-004, SEC-006, SEC-007, SEC-012 |
| A06 | Vulnerable Components | No issues found |
| A07 | Auth Failures | SEC-001, SEC-010, SEC-011 |
| A08 | Data Integrity Failures | No issues found |
| A09 | Logging Failures | No issues found |
| A10 | SSRF | No issues found |

---

## Remediation Priority

| Priority | Issue | Effort |
|----------|-------|--------|
| 1 (Immediate) | SEC-001 (Grafana creds) | 5 min |
| 2 (Immediate) | SEC-002 (SECRET_KEY) | 10 min |
| 3 (Immediate) | SEC-006 (DEBUG default) | 2 min |
| 4 (This week) | SEC-003 (ALLOWED_HOSTS) | 5 min |
| 5 (This week) | SEC-004 (Redis auth) | 30 min |
| 6 (This week) | SEC-012 (HSTS) | 5 min |
| 7 (This sprint) | SEC-005 (Health endpoints) | 1 hour |
| 8 (This sprint) | SEC-009 (Prompt injection) | 4 hours |
| 9 (Backlog) | SEC-007 (CORS) | 15 min |
| 10 (Backlog) | SEC-008 (Health throttle) | 15 min |
| 11 (Backlog) | SEC-010 (JWT lifetime) | 30 min |
| 12 (Backlog) | SEC-011 (DB creds) | 15 min |

---

## Conclusion

SmartStock AI has a **strong security foundation** with proper JWT handling, RBAC, throttling, and Django security middleware. The critical issues are primarily **configuration problems** (hardcoded credentials, insecure defaults) rather than architectural flaws. Addressing the 2 critical and 4 high-severity issues should be the immediate priority, followed by hardening the AI/LLM layer against more sophisticated injection attacks.
