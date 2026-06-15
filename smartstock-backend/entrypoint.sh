#!/bin/sh
set -e

until pg_isready -d "$DATABASE_URL"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

python manage.py migrate --noinput

exec "$@"
