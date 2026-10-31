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

## 2026-10-31 23:55 IST — G1 Official knowledge ✅
**Works (verified by command output):**
- OKF v0.2 specification found (GoogleCloudPlatform/open-knowledge-format@ad30107) and followed. The DMKB fallback was not needed.
- 53 official IOMETE documentation pages fetched (HTTP 200) and 44 concept files curated: deployment 8, architecture 7, security 9, platform 9, integrations 11.
- `scripts/verify_knowledge_excerpts.py` fetched every source page and confirmed every excerpt verbatim ("All excerpts verified against the live pages."). Files were approved only after passing.
- `python scripts/ingest_okf.py --validate-only`: "Validated 44 concept files against OKF v0.2 + DealBridge rules: VALID".
- `make ingest` first run: 44 added, 89 chunks upserted. Second run: 44 unchanged, **0 chunks upserted**, epoch unchanged.
- Qdrant retrievable official points = 89 = sum of `okf_files.chunk_count` (from `scripts/sanity_search.py`).
- The sanity script returns sensible top-3 hits for five sample queries (on-premises, SSO/Okta, column access, BI tools, scaling).
- `POST /api/admin/knowledge/reindex` runs a REINDEX job to SUCCEEDED (0 upserts on an unchanged bundle). Non-admins get 403 FORBIDDEN_ROLE.
- The Admin, Knowledge, Official tab renders real values: 44 files, 89 chunks, epoch 1 (headless Chrome screenshot checked).
- `pytest`: 31 passed, including the ingestion tests (idempotent, changed file, removed file, only approved, validation errors) and `test_embedding_model_mismatch_blocks_serving` and `test_search_filter_excludes_non_active_and_non_approved`.

**Missing / notes:**
- Gaps are recorded in docs/KNOWLEDGE_GAPS.md: no fetched page covers air-gapped installs or names any compliance certification.

## 2026-11-01 00:05 IST — G2 Grounded chatbot ✅ (real-LLM checks pending the key)
**Works (verified by command output):**
- Qwen client over the OpenAI-compatible API. Structured output uses a forced function call (`enable_thinking=false`), Pydantic validation, one validation retry, tenacity retries, then 503 `LLM_UNAVAILABLE`. A FakeLLM is used for tests only.
- Pipeline: classify → route (small talk, out of scope, requirement redirect) → retrieve both collections with the mandatory filter and threshold → generate → deterministic verbatim quote verification (retry once with feedback, then discard) → explicit-certification rule → faithfulness check → decide → persist with retrieval trace.
- Tickets: redaction, document-embedding duplicate check, LLM same-intent check, link (occurrence count +1, priority HIGH at 3) or create, and the context excerpt.
- `pytest`: 45 passed. This includes the RAG tests (answerable with verified citations, fabricated quote discarded, unanswerable creates a ticket, certification needs explicit evidence, general labelled general, infrastructure failure creates no ticket for both the LLM and Qdrant, dedupe links, dedupe respects qualifiers, partial raises a ticket only on click, unfaithful becomes unverified, small talk and redirect), `test_buyer_cannot_use_other_buyers_chat_session`, and `test_every_suggested_question_gets_a_cited_answer` against the real 44-file bundle.
- Calibration: `scripts/calibrate_threshold.py` table recorded in DECISIONS.md. RETRIEVAL_MIN_SCORE=0.60 and RESOLVED_REUSE_MIN_SCORE=0.70 are set in .env.example and config.
- Without a key: `POST /api/chat/sessions/{id}/messages` returns 503 `LLM_NOT_CONFIGURED`, and the user message is still saved (curl output). The chat UI shows a warning alert.
- Chat UI: sessions, suggested questions, cited answers with [n] buttons, sources accordion, partial/unverified/ticket cards and the privacy footer. Typecheck, lint and build pass, and the empty state was checked in a headless Chrome screenshot.

**Pending (needs LLM_API_KEY):** the manual G2 check that a real question returns cited, quote-verified evidence and that an unanswerable question returns the unverified message plus a ticket.
