#!/bin/sh
# Container start: bring the database and knowledge base up to date, then serve.
# Every step is idempotent, so this is safe on every restart.
set -e
cd /app

echo "[start] applying database migrations"
(cd backend && alembic upgrade head)

echo "[start] creating vector collections (if missing)"
python scripts/init_vector.py

echo "[start] ingesting the official knowledge bundle (unchanged files are skipped)"
python scripts/ingest_okf.py

echo "[start] seeding demo identities"
python scripts/seed_demo.py

echo "[start] serving on port ${PORT:-8000}"
cd backend
exec uvicorn app.main:app_factory --factory --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --proxy-headers --forwarded-allow-ips='*'
