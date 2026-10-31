#!/bin/sh
# Container entrypoint: wait for the database, apply migrations, seed demo data, start the server.
set -e

# Retry migrate so a slow-starting or sleeping database does not crash the container.
tries=0
until python manage.py migrate --noinput; do
  tries=$((tries + 1))
  if [ "$tries" -ge 10 ]; then
    echo "Database still not reachable after $tries attempts - giving up."
    exit 1
  fi
  echo "Database not ready yet, retrying in 3s ($tries/10)..."
  sleep 3
done

python manage.py seed_data

# On Render the port is injected via $PORT; fall back to 8000 elsewhere.
if [ "$1" = "gunicorn" ] && [ -n "$PORT" ]; then
  exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2 --access-logfile -
fi

exec "$@"
