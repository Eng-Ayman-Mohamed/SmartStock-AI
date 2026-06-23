#!/bin/sh
set -e

# Skip pg_isready for external databases (Neon, Supabase, etc.)
if [ -z "$DATABASE_URL" ] || echo "$DATABASE_URL" | grep -qE '@(localhost|db)(:|/)'; then
  until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-smartstock}"; do
    echo "Waiting for PostgreSQL..."
    sleep 2
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
