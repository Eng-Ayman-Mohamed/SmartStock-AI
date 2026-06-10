#!/bin/sh
set -e

until pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

python manage.py migrate --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
