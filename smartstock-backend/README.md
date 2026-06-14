# SmartStock AI — Backend

Django 5 + DRF backend powering SmartStock AI: an AI-driven inventory management and forecasting platform for warehouse operations.

## Prerequisites

- Python 3.12
- PostgreSQL 16+ (with [pgvector](https://github.com/pgvector/pgvector) extension)
- Redis 7+
- OpenAI API key
- Cohere API key (for RAG reranking)
- Node.js (only if running the monorepo frontend)

## Quick Start — Local Development

```bash
cd smartstock-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values (at minimum: DJANGO_SECRET_KEY, OPENAI_API_KEY, COHERE_API_KEY, DATABASE_URL, REDIS_URL)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start the API server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A config worker --loglevel=info

# Start Celery beat (separate terminal, optional)
celery -A config beat --loglevel=info
```

The API is available at `http://localhost:8000/api/`.
Swagger docs at `http://localhost:8000/api/schema/swagger-ui/`.

## Quick Start — Docker

```bash
cd smartstock-backend

# Build and run
docker compose up --build
```

Services started:
- **Backend API** — port 8000
- **Celery worker** — background tasks
- **PostgreSQL** — port 5432 (with pgvector)
- **Redis** — port 6379

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | — | Cryptographic signing key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection URL |
| `REDIS_URL` | Yes | `redis://localhost:6379/1` | Redis for cache and Celery |
| `OPENAI_API_KEY` | Yes | — | GPT-4o, embeddings, Whisper |
| `COHERE_API_KEY` | Yes | — | RAG reranking |
| `DJANGO_DEBUG` | No | `True` | Debug mode toggle |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173` | Frontend origins |
| `CSRF_TRUSTED_ORIGINS` | No | `https://smart-stock-dev.vercel.app` | CSRF trusted origins |
| `CELERY_BROKER_URL` | No | Falls back to `REDIS_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | No | Falls back to `REDIS_URL` | Celery result backend |
| `CLOUDINARY_URL` | No | — | Cloudinary for document uploads |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse observability |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse observability |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse server URL |
| `LANGFUSE_DAILY_TOKEN_BUDGET` | No | `1000000` | Token spend cap for alerts |
| `EMAIL_HOST` | No | — | SMTP host (production email) |
| `EMAIL_PORT` | No | `587` | SMTP port |
| `EMAIL_HOST_USER` | No | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | No | — | SMTP password |
| `DEFAULT_FROM_EMAIL` | No | `noreply@smartstock.ai` | Sender address |
| `ESCALATION_RECIPIENT_EMAILS` | No | — | Comma-separated alert recipients |
| `CI` | No | — | Skip env validation when set |

See `.env.example` for the full commented template.

## Available Commands

```bash
# Lint
ruff check .

# Format
ruff format .

# Run tests
pytest                           # uses SQLite in-memory by default
DATABASE_URL=postgres://... pytest  # run tests against real Postgres

# Management commands
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser
python manage.py seed_data        # populate test data
```

## Project Structure

```
smartstock-backend/
├── config/                 # Django project settings
│   ├── settings/
│   │   ├── base.py         # Shared settings (all env vars consumed here)
│   │   ├── development.py  # Local dev overrides
│   │   ├── production.py   # Railway / prod overrides
│   │   └── test.py         # Test settings (SQLite fallback)
│   ├── celery.py           # Celery app configuration
│   ├── urls.py             # Root URL router
│   ├── validators.py       # Env var validation
│   └── exception_handler.py
├── apps/
│   ├── authentication/     # JWT auth, custom user model
│   ├── inventory/          # Products, SKUs, stock levels, suppliers
│   ├── forecasting/        # Prophet-based demand forecasting
│   ├── purchasing/         # Purchase orders, workflow engine
│   ├── ingestion/          # Document upload, RAG query
│   ├── audit/              # Audit logging middleware
│   ├── monitoring/         # Prometheus metrics, alerting
│   ├── notifications/      # Email + dashboard notifications
│   └── health/             # Readiness / liveness probes
├── ai/
│   ├── llm/                # NL query chain, intent classifier, prompts
│   ├── rag/                # Hybrid search (pgvector + FTS), ingestion
│   ├── agents/             # LangChain agents (forecasting, purchasing, decision)
│   ├── multimodal/         # Whisper transcription, GPT-4o vision
│   ├── evaluation/         # AI evaluation metrics
│   └── observability/      # Langfuse tracing integration
├── core/                   # Shared base classes, validators, throttles
├── infrastructure/         # Email, cache, storage adapters
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── golden_dataset/     # Golden dataset evaluation
├── Dockerfile
├── entrypoint.sh           # Waits for Postgres, runs migrations
├── requirements.txt
├── ruff.toml
├── pytest.ini
├── railway.toml            # Web service config
├── railway.worker.toml     # Celery worker config
└── DEPLOY.md               # Detailed Railway deployment guide
```

## Architecture

Clean Architecture layers — never skip a layer:
```
Views → Services → Repositories → DB
```
- **Views** validate input via serializers, then call Services. No DB queries in views.
- **Services** contain business logic, call Repositories.
- **Repositories** extend `BaseRepository`, touch the ORM only.
- **AI layer** (`ai/`) is isolated — no direct imports from `apps/`. Goes through service interfaces.
- **Domain layer** (`core/`) imports nothing from `apps/` or `ai/`.

## Testing

```bash
# Unit + integration tests (SQLite in-memory, no external services needed)
pytest

# With coverage
pytest --cov=. --cov-report=html

# Against real Postgres (CI)
DATABASE_URL=postgres://... pytest
```

- Tests use `config.settings.test` which disables Redis cache, Celery (eager mode), and Cloudinary.
- Golden dataset: 30 annotated NL queries run in CI on merge to main.

## Deployment

This service deploys to **Railway** using two services from the same Docker image:

| Service | Config File | Start Command |
|---|---|---|
| `smartstock-api` | `railway.toml` | `migrate` + `gunicorn` |
| `smartstock-worker` | `railway.worker.toml` | `celery worker` |

See [`DEPLOY.md`](DEPLOY.md) for the full deployment checklist including:
- First-time setup
- Required environment variables (minimum 6 vars)
- Railway shell operations
- Healthcheck configuration
- Cost estimates

**Health check:** `GET /api/health/` returns `{"database": "connected", "redis": "connected"}`.

## Troubleshooting

| Problem | Solution |
|---|---|
| `Missing required environment variables` | Ensure `DJANGO_SECRET_KEY`, `OPENAI_API_KEY`, `COHERE_API_KEY`, `DATABASE_URL`, `REDIS_URL` are set |
| `OPENAI_API_KEY is missing` | Add your OpenAI key to `.env` |
| `COHERE_API_KEY is not set` | Add your Cohere key to `.env` (RAG reranking degrades gracefully) |
| `Redis Connection refused` | Start Redis: `docker run -d -p 6379:6379 redis:7-alpine` |
| `pgvector extension not found` | Install pgvector on your Postgres instance |
| Celery tasks not running | Ensure `celery -A config worker` is running separately |
| CORS errors in browser | Set `CORS_ALLOWED_ORIGINS` to your frontend URL |
| Cookie not set over HTTPS | Ensure `DJANGO_DEBUG=False` in production |
