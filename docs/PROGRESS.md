# Progress

## 2026-10-31 23:40 IST — G0 Foundations ✅
**Works (verified by command output):**
- Toolchain: Python 3.12 (Homebrew; system python3 is 3.9.6), Node v22.16.0, npm 10.9.2, git 2.50.1, Docker 29.9.2 on Colima, Docker Compose 5.6.1.
- `make up`: postgres and qdrant both reported `healthy`.
- `make migrate`: Alembic revision `0001_g0` applied.
- `make init-vector`: both collections present, payload indexes ensured, idempotent on re-run.
- `make seed`: 4 organisations and 5 users on the first run; 0 created on re-run (idempotent).
- `GET /api/health`: postgres ok, qdrant ok, embedding model ok (BAAI/bge-small-en-v1.5 loaded), reindex_required false. LLM is `configured: false` because no `LLM_API_KEY` has been provided yet.
- `GET /api/identity/users` returns the 5 demo identities.
- `GET /api/identity/me` without the header returns 401 `UNKNOWN_IDENTITY` in the error envelope, with `X-Request-Id` and `X-Content-Type-Options: nosniff` headers.
- `pytest tests/unit`: 11 passed (settings, identity, embedder method check).
- Frontend: `npm run typecheck`, `npm run lint` and `npm run build` all pass. The shell has a role switcher, the permanent demo banner, a health indicator and the landing page.

**Missing / notes:**
- PostgreSQL is published on host port 5433, because a pre-existing local PostgreSQL owns 5432.
- LLM-dependent features await the owner's Qwen key.
