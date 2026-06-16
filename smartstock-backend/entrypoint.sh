#!/bin/sh
set -e

until pg_isready -h db -U smartstock; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

python manage.py migrate --noinput

exec "$@"
