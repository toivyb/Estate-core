#!/usr/bin/env sh
set -e

echo "Waiting for Postgres at $DATABASE_URL ..."
# Basic wait loop (no extra deps)
max_retries=60
i=0
until python - <<'PY'
import os, sys, psycopg2, urllib.parse
url=os.environ["DATABASE_URL"]
# Accept both postgresql:// and postgresql+psycopg2://
if url.startswith("postgresql+psycopg2://"):
    url=url.replace("postgresql+psycopg2://","postgresql://",1)
p=urllib.parse.urlparse(url)
conn=psycopg2.connect(host=p.hostname, port=p.port or 5432, user=p.username, password=p.password, dbname=p.path.lstrip("/"))
conn.close()
PY
do
  i=$((i+1))
  if [ "$i" -ge "$max_retries" ]; then
    echo "Postgres not ready after $max_retries tries. Exiting."
    exit 1
  fi
  echo "Postgres not ready yet... ($i/$max_retries). Sleeping 2s."
  sleep 2
done

echo "DB is reachable. Running migrations..."
# If you use Flask-Migrate via Alembic:
flask db upgrade || alembic upgrade head || true

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 wsgi:app
