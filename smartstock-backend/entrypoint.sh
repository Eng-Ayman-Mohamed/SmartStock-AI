#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# If DATABASE_URL is set, extract individual vars for pg_isready
# Render provides DATABASE_URL; local Docker Compose provides individual vars.
# ---------------------------------------------------------------------------
if [ -n "$DATABASE_URL" ] && [ -z "$DB_HOST" ]; then
  # Parse postgres://USER:PASS@HOST:PORT/NAME from DATABASE_URL
  DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):\([0-9]*\)/.*|\1|p')
  DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):\([0-9]*\)/.*|\2|p')
  DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
  DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
fi

# ---------------------------------------------------------------------------
# Wait for PostgreSQL to accept connections
# ---------------------------------------------------------------------------
if [ -n "$DB_HOST" ]; then
  until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-smartstock}" 2>/dev/null; do
    echo "Waiting for PostgreSQL at ${DB_HOST:-localhost}:${DB_PORT:-5432}..."
    sleep 2
  done
fi

# ---------------------------------------------------------------------------
# Run migrations
# ---------------------------------------------------------------------------
python manage.py migrate --noinput

# ---------------------------------------------------------------------------
# Enable pgvector extension (idempotent — safe to run repeatedly)
# ---------------------------------------------------------------------------
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
    print('pgvector extension ensured')
" 2>/dev/null || echo "pgvector extension skipped (not PostgreSQL or extension not available)"

# ---------------------------------------------------------------------------
# Collect static files
# ---------------------------------------------------------------------------
python manage.py collectstatic --noinput 2>/dev/null || true

# ---------------------------------------------------------------------------
# Start gunicorn
# ---------------------------------------------------------------------------
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
