# SmartStock AI — Backend Deployment Guide

This backend is a Django 5 + DRF + Celery stack, designed to run on Railway with PostgreSQL and Redis (external or plugin).

---

## 1. Service Inventory

| Railway service  | Source                          | Start command (pinned in `railway.toml`)                          | Purpose                          |
| ---------------- | ------------------------------- | ----------------------------------------------------------------- | -------------------------------- |
| `smartstock-api` | `smartstock-backend/Dockerfile` | `migrate` + `gunicorn ...`                                        | Public HTTP API                  |
| `smartstock-worker` | same image, `railway.worker.toml` | `celery -A config worker --loglevel=info --concurrency=2`         | Async / background tasks         |
| **Postgres**     | Railway plugin (or external Neon) | —                                                              | Primary database                 |
| **Redis**        | Railway Redis plugin            | —                                                                 | Celery broker + result backend   |

Both services use the **same** Dockerfile, **same** env vars, and **same** image — only the `startCommand` differs. Use a separate `railway.toml` per service so each picks up its own command.

> **Both `railway.toml` and `railway.worker.toml` must point to the same `Dockerfile`.** The `Config Path` field on the Railway service tells Railway which one to read.

---

## 2. Environment Variables

The only truly required vars are marked **●**. Everything else has baked-in defaults and can be skipped.

| Variable | Web | Worker | Notes |
|---|---|---|---|
| `DATABASE_URL` | — | — | **Auto-injected** by Railway Postgres plugin |
| `REDIS_URL` | ● | ● | Your external Redis URL |
| `DJANGO_SECRET_KEY` | ● | ● | `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | — | — | Defaults to `False` in production |
| `ALLOWED_HOSTS` | — | — | Defaults to `localhost,127.0.0.1` — set `.up.railway.app,<your-domain>` if you need it |
| `CORS_ALLOWED_ORIGINS` | — | — | Defaults to `http://localhost:5173` — set your Vercel URL for prod |
| `CSRF_TRUSTED_ORIGINS` | — | — | Defaults to `https://smart-stock-dev.vercel.app` — override if different |
| `OPENAI_API_KEY` | ● | ● | Required for AI features |
| `COHERE_API_KEY` | ● | ● | Required for RAG reranking |
| `LANGFUSE_PUBLIC_KEY` | — | — | Optional — Langfuse disabled if empty |
| `LANGFUSE_SECRET_KEY` | — | — | Optional — Langfuse disabled if empty |
| `LANGFUSE_HOST` | — | — | Defaults to `https://cloud.langfuse.com` |
| `CLOUDINARY_URL` | — | — | Optional — image upload disabled if empty |
| `EMAIL_HOST` | — | — | Only needed if sending email (PO notifications, etc.) |
| `EMAIL_HOST_USER` | — | — | Only needed if sending email |
| `EMAIL_HOST_PASSWORD` | — | — | Only needed if sending email |
| `DEFAULT_FROM_EMAIL` | — | — | Defaults to `noreply@smartstock.ai` |
| `ESCALATION_RECIPIENT_EMAILS` | — | — | Optional — escalation disabled if empty |

**Auto-injected** (do not set): `PORT`, `DATABASE_URL`, `RAILWAY_*` metadata.

### Minimum set for a working deploy

```bash
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
ALLOWED_HOSTS=.up.railway.app
REDIS_URL=redis://default:...@pets-wood-knowledge-68404.db.redis.io:10987
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

That's **6 variables** plus whatever Railway auto-injects.

---

## 3. First-Time Deploy Checklist

1. **Generate and commit migrations locally:**
   ```bash
   cd smartstock-backend
   python manage.py makemigrations
   git add -f apps/*/migrations/*.py
   git commit -m "chore: initial migrations for production"
   git push
   ```
   The `migrate` step inside the web service's `startCommand` will then build the schema on first boot.

2. **In Railway, create a new project** from this GitHub repo.

3. **Add the PostgreSQL plugin** (or paste a Neon `DATABASE_URL` as a variable).

4. **Set your external Redis URL** as a variable (no Redis plugin needed if using external).

5. **Add the web service:**
   - Repo: `Eng-Ayman-Mohamed/SmartStock-AI`
   - **Root Directory** = `smartstock-backend`
   - **Config Path** = `railway.toml`
   - Set the **minimum env vars** from §2 above (6 vars).

6. **Add the worker service:**
   - Same repo, same root directory
   - **Config Path** = `railway.worker.toml`
   - Set the same vars — works with the same minimum set.

7. **Enable auto-deploy:** Railway deploys automatically on push to `main`. Set it in the Railway dashboard per service (Settings → Auto Deploy).

8. **Create a superuser** via the Railway shell on the web service:
   ```bash
   python manage.py createsuperuser
   ```

9. **Smoke test:** `curl https://<service>.up.railway.app/api/health/` should return `{"database": "connected", "redis": "connected"}`.

---

## 4. Local Development

### Postgres
Use a local Postgres or your Neon dev branch. Set `DATABASE_URL` in `.env` to the connection string.

### Redis
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Run the stack
```bash
# Web
python manage.py runserver

# Worker (separate terminal, in the .venv)
DJANGO_SETTINGS_MODULE=config.settings.development celery -A config worker -l info
```

`.env` already wires `REDIS_URL=redis://localhost:6379/0` for both the broker and the result backend.

---

## 5. Adding a New Celery Task

1. Create `apps/<app>/tasks.py`:
   ```python
   from celery import shared_task

   @shared_task(bind=True, max_retries=3)
   def my_task(self, payload):
       ...
   ```

2. In `apps/<app>/apps.py`, ensure the app config is loaded (Django auto-discovers `tasks.py`).

3. Call from a view/service:
   ```python
   my_task.delay(payload)
   ```

4. The worker (local or Railway) will pick it up. If you change the task signature, run `python manage.py migrate` is **not** needed, but redeploy the worker.

---

## 6. Common Railway Shell Operations

```bash
# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Run any one-off management command
python manage.py <command> --noinput
```

Open the shell from the Railway dashboard → service → **Shell** tab.

---

## 7. Healthcheck

The web service's `railway.toml` declares `healthcheckPath = "/api/health/"`. If gunicorn stops responding, Railway restarts the container.

The worker service has no healthcheck — it runs the Celery process until killed. Railway restarts on crash via `restartPolicyType = "ON_FAILURE"`.

---

## 8. Costs (rough estimate)

| Item                    | Typical cost (USD/month) |
| ----------------------- | ------------------------ |
| Web service (always-on) | ~$5                      |
| Worker service          | ~$5                      |
| Postgres plugin         | ~$5–10                   |
| Redis plugin            | ~$3–5                    |
| **Total**               | **~$18–25**              |

Switching to Neon as an external Postgres and disabling the Railway Postgres plugin can reduce the DB cost. Redis and the two services are usually the minimum required for a healthy Celery stack.
