#!/bin/sh
set -e

# If running as Celery worker/beat, skip DB setup (no HTTP server needed)
if echo "$@" | grep -qE '^celery'; then
  exec "$@"
fi

# Skip pg_isready for external databases (Neon, Supabase, etc.)
if [ -z "$DATABASE_URL" ] || echo "$DATABASE_URL" | grep -qE '@(localhost|db)(:|/)'; then
  until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-smartstock}"; do
    echo "Waiting for PostgreSQL..."
    sleep 2
  done
fi

python manage.py migrate --noinput

# Only run collectstatic in production (dev uses Django's DEBUG static serving)
# Run in background so gunicorn starts immediately — Railway health checks
# need the process listening within seconds, and collectstatic can take 30s+.
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
  python manage.py collectstatic --noinput &
  COLLECTSTATIC_PID=$!
  echo "collectstatic running in background (pid: $COLLECTSTATIC_PID)"
fi

exec "$@"
