#!/bin/sh
# Runs on every container start. Both steps are idempotent (see CLAUDE.md's "Running
# the app" / scripts/seed.py's docstring), so re-running them on every `docker compose
# up` is safe and keeps the container self-sufficient — no separate manual setup step.
set -e

alembic upgrade head
python scripts/seed.py

exec python -m uvicorn permissions_server.main:app --host 0.0.0.0 --port 8000 --reload
