#!/bin/sh
set -e

echo "[entrypoint] Waiting for database and applying migrations..."

attempt=0
max_attempts=30
until alembic upgrade head; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "[entrypoint] alembic upgrade head failed after ${max_attempts} attempts"
    exit 1
  fi
  echo "[entrypoint] Database not ready, retry in 2s (${attempt}/${max_attempts})..."
  sleep 2
done

echo "[entrypoint] Migrations applied."

python - <<'PY'
import os

from netagent_db.seed import run_seed
from netagent_db.session import create_session_factory

database_url = os.environ["DATABASE_URL"]
session_factory = create_session_factory(database_url)
with session_factory() as session:
    run_seed(session)
PY

echo "[entrypoint] Seed done. Starting: $*"

if [ $# -eq 0 ]; then
  set -- python -m bot.app
fi

exec "$@"
