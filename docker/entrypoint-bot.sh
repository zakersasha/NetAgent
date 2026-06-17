#!/bin/sh
set -e

alembic upgrade head

python - <<'PY'
import os

from netagent_db.seed import run_seed
from netagent_db.session import create_session_factory

database_url = os.environ["DATABASE_URL"]
session_factory = create_session_factory(database_url)
with session_factory() as session:
    run_seed(session)
PY

exec python -m bot.app
