#!/bin/sh
# Container entrypoint: apply migrations, seed demo data, then start the server.
set -e

python manage.py migrate --noinput
python manage.py seed_data

# On Render the port is injected via $PORT; fall back to 8000 elsewhere.
if [ "$1" = "gunicorn" ] && [ -n "$PORT" ]; then
  exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2 --access-logfile -
fi

exec "$@"
