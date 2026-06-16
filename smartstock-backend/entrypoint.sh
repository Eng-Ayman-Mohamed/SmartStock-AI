#!/bin/sh
set -e

until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-smartstock}"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
