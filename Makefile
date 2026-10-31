# DealBridge developer commands. Run from the repository root.
PY      := backend/.venv/bin/python
PYTEST  := backend/.venv/bin/pytest
COMPOSE := docker compose

.PHONY: up down backend-install frontend-install migrate init-vector ingest seed dev-backend dev-frontend test test-backend test-frontend reset-demo check-secrets

up:
	$(COMPOSE) up -d
	@echo "Waiting for postgres and qdrant to become healthy..."
	@for i in $$(seq 1 60); do \
	  pg=$$(docker inspect -f '{{.State.Health.Status}}' $$($(COMPOSE) ps -q postgres) 2>/dev/null); \
	  qd=$$(docker inspect -f '{{.State.Health.Status}}' $$($(COMPOSE) ps -q qdrant) 2>/dev/null); \
	  if [ "$$pg" = "healthy" ] && [ "$$qd" = "healthy" ]; then echo "postgres: $$pg, qdrant: $$qd"; exit 0; fi; \
	  sleep 2; \
	done; echo "Services did not become healthy (postgres: $$pg, qdrant: $$qd)"; exit 1

down:
	$(COMPOSE) down

backend-install:
	test -d backend/.venv || python3.12 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt

frontend-install:
	cd frontend && npm ci

migrate:
	cd backend && .venv/bin/alembic upgrade head

init-vector:
	$(PY) scripts/init_vector.py

ingest:
	$(PY) scripts/ingest_okf.py

seed:
	$(PY) scripts/seed_demo.py

dev-backend:
	cd backend && .venv/bin/uvicorn app.main:app_factory --factory --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest -q

test-frontend:
	cd frontend && npm run typecheck && npm run lint && npm run build

reset-demo:
	$(PY) scripts/reset_demo.py --yes

check-secrets:
	$(PY) scripts/check_no_secrets_in_bundle.py
