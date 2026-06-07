# SmartStock AI — Backend Deployment Guide

This backend is a Django 5 + DRF + Celery stack, designed to run on Railway with Neon PostgreSQL and a managed Redis plugin.

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

| Variable                  | Web service | Worker service | Source                                                      |
| ------------------------- | :---------: | :------------: | ----------------------------------------------------------- |
| `DATABASE_URL`            | auto        | auto           | Neon pooled connection string (or Railway Postgres plugin)  |
| `REDIS_URL`               | auto        | auto           | Railway Redis plugin (auto-injected)                        |
| `DJANGO_SETTINGS_MODULE`  | baked in    | baked in       | Set in Dockerfile `ENV` to `config.settings.production`     |
| `DJANGO_SECRET_KEY`       | required    | required       | Generate with `python -c "import secrets;print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG`            | required    | required       | `False`                                                     |
| `ALLOWED_HOSTS`           | required    | required       | `.up.railway.app,<your-domain>`                             |
| `CORS_ALLOWED_ORIGINS`    | required    | —              | Comma-separated; include Vercel frontend URL                |
| `CSRF_TRUSTED_ORIGINS`    | required    | —              | Comma-separated; include Vercel frontend URL                |
| `EMAIL_HOST`              | required    | —              | `smtp.sendgrid.net`                                         |
| `EMAIL_HOST_PASSWORD`     | required    | —              | SendGrid API key                                            |
| `EMAIL_HOST_USER`         | required    | —              | `apikey`                                                    |
| `EMAIL_PORT`              | required    | —              | `587`                                                       |
| `DEFAULT_FROM_EMAIL`      | required    | —              | `noreply@smartstock.ai`                                     |
| `OPENAI_API_KEY`          | optional    | optional       | Only if AI features run on this service                     |

**Auto-injected** (do not set by hand): `PORT`, `DATABASE_URL` (Postgres plugin), `REDIS_URL` (Redis plugin), `RAILWAY_*` metadata.

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

4. **Add the Redis plugin.**

5. **Add the web service:**
   - Repo: `Eng-Ayman-Mohamed/SmartStock-AI`
   - **Root Directory** = `smartstock-backend`
   - **Config Path** = `railway.toml`
   - Set the env vars from the table above.

6. **Add the worker service:**
   - Same repo, same root directory
   - **Config Path** = `railway.worker.toml`
   - Set the same env vars minus the email/CORS ones (worker doesn't serve HTTP).

7. **Create a superuser** via the Railway shell on the web service:
   ```bash
   python manage.py createsuperuser
   ```

8. **Smoke test:** `curl https://<service>.up.railway.app/admin/login/` should return 200 with Django's admin login page.

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

The web service's `railway.toml` declares `healthcheckPath = "/admin/login/"`. If gunicorn stops responding, Railway restarts the container.

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
