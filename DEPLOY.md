# Production Deployment Guide — SmartStock AI

## Overview

SmartStock AI runs on **Render** (backend) and **Vercel** (frontend) with the following production architecture:

```
Vercel (frontend)
  └── https://smartstock-ai.vercel.app

Render (backend stack)
  ├── Web Service    — Django + gunicorn
  ├── Worker         — Celery background tasks
  ├── Beat           — Celery scheduled tasks
  ├── PostgreSQL     — Managed database (with pgvector)
  └── Redis          — Managed cache/broker
```

---

## 1. Render Deployment

### Option A: Blueprint (Recommended)

1. Push this repository to GitHub
2. In the Render Dashboard, click **New → Blueprint**
3. Point it at the root `render.yaml` file in this repository
4. Render will create all services automatically
5. Set the **secret env vars** (those marked `sync: false`) in each service's dashboard:
   - `OPENAI_API_KEY`
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
   - `COHERE_API_KEY`
   - `EMAIL_HOST_PASSWORD` (SendGrid)
6. Enable pgvector — see [Section 3](#3-enable-pgvector)

### Option B: Manual Setup

Follow the manual setup in the Render dashboard for each service type.

---

## 2. Frontend Deployment (Vercel)

1. Connect the repository to Vercel
2. Set the root directory to `smartstock-frontend`
3. Framework preset: **Vite**
4. Environment variables:
   ```
   VITE_API_URL=https://smartstock-api.onrender.com/api
   ```
5. Deployments trigger automatically on push to `main`

---

## 3. Enable pgvector

Render's managed PostgreSQL does **not** have pgvector pre-installed. You must enable it after the database is created.

### Steps:

1. **Open Render Shell** for your PostgreSQL service, or connect via `psql`:
   ```bash
   psql <your-render-database-url>
   ```

2. **Run the extension creation**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Verify**:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
   You should see a row for the `vector` extension.

### Alternative: Post-deploy hook

The Docker entrypoint (`entrypoint.sh`) runs `CREATE EXTENSION IF NOT EXISTS vector` automatically on every deploy. If the Render PostgreSQL plan supports pgvector (all paid plans do), this will succeed silently. On the free tier, it will log a warning and continue.

> **Note:** Render's free PostgreSQL tier may not support extensions. Upgrade to at least the **Starter** plan for pgvector support.

---

## 4. Environment Variables

### Required (Web + Worker + Beat services)

| Variable | Source | Description |
|----------|--------|-------------|
| `DJANGO_SECRET_KEY` | Auto-generated | Django secret key |
| `DJANGO_SETTINGS_MODULE` | Fixed: `config.settings.production` | Settings module |
| `DJANGO_DEBUG` | Fixed: `False` | Disable debug mode |
| `DATABASE_URL` | From managed PostgreSQL | PostgreSQL connection string |
| `REDIS_URL` | From managed Redis | Redis connection string |
| `CELERY_BROKER_URL` | Same as `REDIS_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | Same as `REDIS_URL` | Celery result backend |
| `OPENAI_API_KEY` | Manual | OpenAI API key |
| `LANGFUSE_PUBLIC_KEY` | Manual | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Manual | Langfuse secret key |
| `COHERE_API_KEY` | Manual | Cohere API key for embeddings |
| `CORS_ALLOWED_ORIGINS` | Set in render.yaml | Comma-separated allowed origins |
| `CSRF_TRUSTED_ORIGINS` | Set in render.yaml | Comma-separated CSRF origins |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_HOST` | `smtp.sendgrid.net` | SMTP server |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | `apikey` | SMTP username |
| `EMAIL_HOST_PASSWORD` | — | SendGrid API key |
| `DEFAULT_FROM_EMAIL` | `noreply@smartstock.ai` | Sender address |
| `ALLOWED_HOSTS` | Auto-configured | Comma-separated hostnames |
| `DJANGO_LOG_LEVEL` | `WARNING` | Python logging level |

---

## 5. HTTPS & Security

Production settings (`config/settings/production.py`) enforce:

- **HTTPS redirect**: All HTTP requests → 301 to HTTPS
- **HSTS**: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- **Secure cookies**: Session, CSRF, and JWT refresh cookies marked `Secure`, `HttpOnly`, `SameSite=Strict`
- **Security headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`
- **No debug output**: `DEBUG=False`, generic error messages only (no stack traces)

---

## 6. Smoke Test

Run after every deployment:

```bash
./scripts/smoke-test.sh https://smartstock-api.onrender.com
```

Checks:
1. `GET /api/health/` → 200 with `database: connected`, `redis: connected`
2. `GET http://...` → redirects to HTTPS
3. `GET /api/docs/` → 200 (Swagger UI)
4. `POST /api/auth/login/` → 400/401 (endpoint validates credentials)
5. Security headers present (HSTS, X-Content-Type-Options)

---

## 7. Celery Workers

### Worker Service
- **Type**: Worker (not Web)
- **Command**: `celery -A config worker --loglevel=info --concurrency=2`
- **Plan**: Starter or higher (same as web service)

### Beat Service
- **Type**: Worker (not Web)
- **Command**: `celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Plan**: Starter or higher
- Must be a **separate** service from the worker

Both services require the same environment variables as the web service (DATABASE_URL, REDIS_URL, API keys).

---

## 8. Post-Deployment Verification

After deploying, verify all services are live:

```bash
# Health check
curl https://smartstock-api.onrender.com/api/health/
# Expected: {"status":"ok","database":"connected","redis":"connected"}

# API docs
curl -so /dev/null -w "%{http_code}" https://smartstock-api.onrender.com/api/docs/
# Expected: 200

# pgvector (connect to database and run)
SELECT * FROM pg_extension WHERE extname = 'vector';
# Expected: one row
```

---

## 9. Troubleshooting

### "pgvector extension not available"
- Render's free PostgreSQL tier doesn't support extensions
- Upgrade to the **Starter** plan or higher
- The entrypoint handles this gracefully — the app will still work, just without vector search

### Celery worker not connecting
- Verify `CELERY_BROKER_URL` matches `REDIS_URL`
- Check Redis service is running in the Render dashboard
- Worker logs: Render Dashboard → smartstock-celery → Logs

### CORS errors on frontend
- Add your Vercel URL to `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
- Format: comma-separated, e.g. `https://smartstock-ai.vercel.app,https://smart-stock-dev.vercel.app`

### 502 Bad Gateway
- Check web service logs for startup errors
- Ensure all required env vars are set (app won't start if any are missing)
- The entrypoint waits for PostgreSQL before starting — allow 40-60 seconds for cold start
