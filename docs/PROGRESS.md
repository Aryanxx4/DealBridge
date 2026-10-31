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

## 2026-11-01 00:30 IST — G3 Dynamic knowledge loop ✅ (manual demo with a real LLM pending the key)
**Works (verified by command output):**
- `knowledge_records` is versioned per group, with a partial unique index allowing one ACTIVE row per group. The Qdrant point id equals the record id.
- Publish is synchronous and idempotent: PENDING, then embed and upsert, then INDEXED. Ticket PUBLISHED, epoch +1 and an audit entry follow. On failure the ticket stays APPROVED with `publish_error` and returns 502 `PUBLISH_INDEX_FAILED`, and `/publish` retries safely.
- Lifecycle: supersede creates version n+1 and marks the old version SUPERSEDED in PostgreSQL and in the payload. Revoke sets REVOKED via `set_payload`; the point is kept and filtered out.
- The admin ticket state machine is enforced server-side. Invalid transitions return 409 `INVALID_STATE` with the allowed transitions. The privacy checkbox and a 40-character minimum are required. Self-approval is guarded by config.
- Global knowledge holds only a **redacted** `question_original`. This resolves the conflict between §8.5 and R6 in favour of R6.
- `pytest`: 56 passed. This includes `test_dynamic_knowledge_loop_end_to_end`, which uses real embeddings and Qdrant: a differently worded repeat question returns EXPERT_VERIFIED citing the new point, and My questions shows the answer. It also includes the rejected, unapproved, revoked, superseded, publish-failure-retry, collections-separate and payload-no-private-data tests, plus privacy, self-approval and non-admin tests.
- `scripts/reindex_knowledge.py` ran: official 89 chunks re-upserted into a recreated collection, resolved re-embedded from PostgreSQL.
- UI: admin dashboard (live counts, queue, audit), ticket detail (trace, redacted context with warning, answer editor with preview, sources, privacy checkbox, status-aware actions), resolved-knowledge tab (supersede, revoke), and My questions with chat status polling. Typecheck, lint and build pass, and the dashboard screenshot was checked.

**Pending (needs LLM_API_KEY):** the manual end-to-end demonstration through the UI. Ticket creation requires the chat pipeline.

## 2026-11-01 00:55 IST — G4 Requirement intake ✅ (real-LLM extraction check pending the key)
**Works (verified by command output):**
- Models and migration `0005_g4`: assessments, uploaded_documents, requirements (REQ-### display ids, seq never reused), append-only requirement_revisions, change_proposals. FKs deferred from earlier gates were added.
- RequirementService is the only mutation path. Every change writes a revision, bumps `requirement_set_revision`, turns ANALYZED into STALE and audits. While ANALYZING it returns 409 `JOB_IN_PROGRESS`.
- PDF upload: magic bytes and content type (415), size while streaming (413), page limit (422), encrypted (422), malformed (422), SCANNED status with the exact message, generated storage names, text-only extraction (no rendering).
- Extraction job: page-bounded windows of at most 12,000 chars with `[[PAGE n]]` markers, verbatim or rapidfuzz page location (`quote_verified`), token_sort dedupe ≥ 92, a cap of 60, and progress reporting.
- Intake chat: proposals stored PENDING. Apply only on click, with `STALE_PROPOSAL` detection. The air-gapped-to-hybrid instruction becomes a REMOVE plus an ADD (HIGH).
- Guided form: deterministic deployment and scale requirements, LLM extraction for free-text fields with per-field priority. Resubmission only touches changed or cleared fields.
- `make_demo_pdfs.py`: FinBank_Requirements.pdf (3 pages, 1,969 extractable characters) and the scanned copy (0 characters).
- `pytest`: 75 passed. This includes all §15.3 item 1 and 2 tests plus intake, chat proposals, stale proposals, ANALYZING lock, display ids, `test_buyer_cannot_read_other_buyers_assessment` and `test_seller_cannot_modify_requirements`.
- UI: buyer dashboard with a new-assessment dialog, and the workspace Requirements tab (PDF drop zone with scanned alert and job progress, intake chat with diff proposal cards, zod guided form with priorities, review table with inline edit, selects, source tooltip with unverified warning, clarification "Keep as written", confirm, remove, restore, history drawer, add row, confirm all, sticky counts footer). Typecheck, lint and build pass, and a screenshot with real uploaded documents was checked.

**Pending (needs LLM_API_KEY):** the G4 check that the demo PDF yields at least seven requirements, with one flagged for clarification.

## 2026-11-01 01:25 IST — G5 Assessment engine ✅ (real-LLM manual run pending the key)
**Works (verified by command output):**
- Migration `0006_g5`: immutable assessment_versions, requirement_assessments and evidence_references (with role).
- Per-requirement retrieval: two queries (the text, and the category label plus text), both collections with the mandatory filter, merged by chunk with the best score, threshold 0.60, top 8. No candidates gives UNKNOWN without an LLM call.
- Judge prompt (judge.v1) with the five statuses defined as in REQUIREMENTS §4.4. Deterministic guardrails G1–G8, each downgrade recorded in `guardrail_notes`.
- ANALYZE job: ThreadPoolExecutor(4) with progress "Assessing REQ-00n (n of N)", blockers (CRITICAL/HIGH and NOT_SUPPORTED/PARTIALLY_SUPPORTED/UNKNOWN), deduplicated aggregates, and an LLM summary from structured results only. No fit percentage. On failure: no version, previous status restored.
- Versions and comparison (ADDED, REMOVED, TEXT_CHANGED, PRIORITY_CHANGED, STATUS_CHANGED, UNCHANGED), pending changes, changes since the previous version, the knowledge-updated flag, open_ticket and answer_available per requirement.
- `pytest`: 90 passed. This includes all six §15.3 item-4 guardrail tests, the item-3 quote rules, and the item-10 tests (new version keeps the previous one, edit marks STALE and the re-run creates version 2, failure creates no version, comparison).
- UI: Run/Re-run with an excluded-count warning and a disabled explanation, job progress, the Results tab (version selector, stale/pending/knowledge banners, summary with five status tiles, blockers, next steps, filters and search, a detail sheet with evidence cards, guardrail notes, conflict alert, seller-response section and "Ask the product team"), and the Versions tab with comparison. Typecheck, lint and build pass.
- Demo scanned PDF shrunk to 136 KB (JPEG pages).

**Pending (needs LLM_API_KEY):** a manual run on the demo requirements to observe real statuses.

## 2026-11-01 01:55 IST — G6 Report, sharing, seller ✅
**Works (verified by command output):**
- Migration `0007_g6`: assessment_shares (version-bound, revocable), seller_responses, follow_up_requests and follow_up_messages (append-only).
- PDF report: ReportLab Platypus, A4, DejaVu Sans (bundled with its licence), every section of §10.10 in order, statuses printed as text plus a colour chip, "page X of Y" footer, the exact disclaimer, the `DealBridge_Assessment_<slug>_v<N>_<YYYYMMDD>.pdf` attachment name, and an audit entry. Buyer tickets are included only in the buyer's copy. A layout render was checked visually.
- Sharing: explicit consent (400 `CONSENT_REQUIRED`), 409 `NO_ANALYSIS`, version-bound shares, revoke (immediate loss of access including follow-ups), and a shares list.
- Seller view: only versions shared with the seller's organisation. It contains no uploaded files, chats, tickets or raw form. Seller responses are attributed, stored separately, never change requirements or statuses, and appear in buyer results and the report as "Seller statement — not verified by product documentation".
- Follow-ups: the full §10.13 state machine, `NOT_SHARED` without a share, and CLOSED threads are read-only.
- `pytest`: 102 passed. This includes every §15.3 item-9 and item-11 test, plus unshared versions hidden, non-Latin report text, and cross-buyer isolation.
- UI: results actions (download PDF, share dialog with sees/never-sees lists and a consent checkbox), the buyer "Share and follow-ups" tab (status, revoke, request a follow-up with a share-first path, threads), and the seller workspace (shared list, follow-up queue, read-only assessment with status filter tiles, a detail sheet with the response form and helper text, report download, follow-up threads). No edit controls on the seller side. Typecheck, lint and build pass.

## 2026-11-01 02:30 IST — G7 Polish and verification ✅ (real-LLM items pending the key)
**Works (verified by command output):**
- `make backend-install`, `make frontend-install`, `make reset-demo` (refuses without `--yes`; truncates app tables, recreates the resolved collection, keeps 89 official points) all ran.
- `make test`: **112 passed, 1 deselected** (the real-LLM eval), then typecheck, lint and build pass. `make check-secrets`: passed (60 dist files plus tracked files).
- QwenClient unit tests with a stubbed OpenAI client cover the forced tool payload (`enable_thinking=false`), the fast or main model choice, the validation retry, the temperature and json_object fallbacks, transient-error retries, and auth error mapping.
- `tests/eval/test_prompt_injection.py` (marker `llm`) collects and skips without a key.
- 768 px check: no page-level horizontal scroll; tables scroll inside their cards; the header was tightened.
- Docs: README implementation guide (status, architecture, setup, run, env table, OKF, calibration, tests, troubleshooting, limitations), docs/API.md (71 routes, generated from the running app's OpenAPI), demo/DEMO_SCRIPT.md (observed vs pending, honestly marked), docs/FINAL_REPORT.md.
- Demo steps observed without the LLM: the scanned-PDF message (exact), text PDF OK, extraction returning 503 `LLM_NOT_CONFIGURED`, and Daniel getting 404 on FinBank's assessment.

**Missing:** the full demo script with the real LLM, `make test-llm`, G8 (P1) items, and GitHub/Vercel deployment.

## 2026-11-01 03:05 IST — Clean clone and G8 (P1) ✅
- **Clean clone:** `git clone`, then the README setup commands, then `make test` (111 passed, 1 skipped as expected on a fresh clone), then `make check-secrets` (passed). EXIT=0.
- **G8 built and tested:** seller documents (upload, attach to response or follow-up, download only by the uploading org or the owning buyer, never indexed), follow-up owner assignment, Excel export (formula-injection safe), the version-compare "changed only" toggle, and the admin ticket category filter. 6 new integration tests pass.
- `make test`: **118 passed, 1 deselected**, then typecheck, lint and build pass. `make check-secrets` passes. docs/API.md regenerated (78 routes) by `scripts/generate_api_md.py`.
