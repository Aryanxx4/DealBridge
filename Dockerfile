# Single-container build: the FastAPI backend also serves the built React app (STATIC_DIR).
# Used for hosting (e.g. Render). Local development still uses `make dev-backend` / `make dev-frontend`.

# ---- 1. Build the frontend ----
FROM node:22-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# Same-origin API: the backend serves both the app and /api.
ENV VITE_API_BASE_URL=/api
RUN npm run build

# ---- 2. Backend runtime ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/ backend/
COPY scripts/ scripts/
COPY knowledge/ knowledge/
COPY demo/ demo/
COPY --from=frontend /app/frontend/dist frontend/dist

# Download the embedding model at build time so startup does not depend on Hugging Face.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='/app/.cache/fastembed')"

ENV APP_ENV=production \
    STATIC_DIR=./frontend/dist \
    FASTEMBED_CACHE_DIR=./.cache/fastembed \
    LOG_LEVEL=INFO \
    PORT=8000

RUN chmod +x scripts/start.sh && useradd --create-home --uid 10001 app && mkdir -p uploads && chown -R app /app
USER app
EXPOSE 8000
CMD ["scripts/start.sh"]
