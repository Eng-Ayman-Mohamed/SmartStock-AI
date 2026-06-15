# SmartStock AI — AGENTS.md

## Project structure

Monorepo with two siblings: `smartstock-backend/` (Django 5 + DRF) and `smartstock-frontend/` (React 19 + Vite 8).

## Architecture (enforced)

Clean Architecture layers — never skip a layer:
```
Views → Services → Repositories → DB
```
- Views validate input via serializers, then call Services. No DB queries in views.
- Services contain business logic, call Repositories.
- Repositories extend `BaseRepository`, touch the ORM only.
- AI layer (`ai/`) is isolated — no direct imports from `apps/`. Goes through service interfaces.
- Domain layer (`core/`) imports nothing from `apps/` or `ai/`.

## Essential commands

### Backend
```bash
cd smartstock-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd smartstock-frontend
npm install
cp .env.example .env.local
npm run dev            # serves on :5173, proxies /api → localhost:8000
npm run build          # tsc -b && vite build
npm run lint           # eslint .
```

### Docker (full stack)
```bash
docker compose up --build
```
Services: postgres (pgvector/pg16), redis, backend (port 8000), celery, celery-beat, frontend (port 3000).

## Config quirks

- **Settings split**: `config/settings/base.py` ← `development.py` / `production.py`. The Dockerfile and Railway use `production`.
- **Ruff for linting** in backend — config at `ruff.toml` (line-length=100, ignore E501).
- **CI workflow** at `.github/workflows/ci.yml` — runs lint, tests (pytest with `config.settings.test`), and OpenAPI validation.
- **No pre-commit hooks** configured.
- **Migrations are tracked in git** — run `python manage.py makemigrations` after model changes and commit the generated files.
- **Frontend ESLint** at `eslint.config.js` — run via `npm run lint`.

## Testing

```bash
cd smartstock-backend
# no pytest config files found — may need DJANGO_SETTINGS_MODULE set
DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest tests/
```
- Tests live in `smartstock-backend/tests/` split into `unit/`, `integration/`, and `golden_dataset/`.
- Golden dataset: 30 annotated NL queries run in CI on merge to main.

## Key conventions from docs

- **Token in memory, never localStorage** — Zustand auth store holds JWT; refresh via HttpOnly cookie.
- **Standard response envelope**: `{"status": "success", "data": ..., "meta": {...}}` on success, `{"status": "error", "error": "Type", "message": "...", "code": NNN}` on error.
- **Domain exceptions** in `core/exceptions.py` → global exception handler maps to HTTP codes.
- **Design system**: Custom Tailwind tokens (brand-50..900, green-50..900, amber, red, purple, gray). See `design-system-prompt.md` for exact hex values.

## Deployment

- **Backend**: Railway (`railway.toml` + `railway.worker.toml`). Start command runs `migrate --noinput` then gunicorn.
- **Frontend**: Vercel (implied by `.env.example` comments).
- **Health check**: `GET /api/health/` returns `{"database": "connected", "redis": "connected"}`.
