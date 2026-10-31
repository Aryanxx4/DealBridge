# Final report

Date: 2026-11-01. Repository: `hackCbs9`. All results below come from commands run in this repository against real PostgreSQL 16, Qdrant v1.20.0 and the local `BAAI/bge-small-en-v1.5` embedding model. LLM-dependent behaviour is verified with a scripted FakeLLM, because **no Qwen API key has been provided yet**.

## What works
Legend: ✅ verified by the named test or observation · ⏳ implemented and tested with a scripted LLM, live LLM run pending the key.

### Requirement assessment (REQUIREMENTS §11)
| Criterion | | Evidence |
|---|---|---|
| Buyer can create an assessment | ✅ | `test_intake.py` (all tests create one); observed via the API on 2026-11-01 |
| Buyer can upload a text-based PDF | ✅ | `test_pdf_text_extraction`; observed (FinBank_Requirements.pdf, OK, 3 pages) |
| Buyer can provide requirements through chat | ⏳ | `test_intake_chat_air_gapped_to_hybrid`, `test_stale_proposal_is_rejected` |
| Buyer can use the guided form | ⏳ | `test_form_resubmission_replaces_only_changed_fields` |
| System extracts multiple requirements | ⏳ | `test_pdf_extraction_job_verifies_quotes_and_pages`, `test_dedupe_skips_duplicates`; the real demo PDF yield (at least 7) is pending the key |
| Buyer can edit extracted requirements | ✅ | `test_requirement_edit_marks_assessment_stale_and_logs_revision`, `test_original_text_is_immutable` |
| Assessment uses confirmed requirements | ✅ | `test_unconfirmed_requirements_are_excluded`, `test_analyze_requires_confirmed_requirements` |
| Every assessed requirement has one defined status | ✅ | DB CHECK constraint plus `test_assessment_job_creates_new_version_and_keeps_previous` |
| Supported claims show evidence references | ✅ | `test_guardrails_supported_without_evidence_becomes_unknown` (G2), evidence asserted in `test_assessment_job_creates_new_version_and_keeps_previous` |
| Unknown claims are not fabricated | ✅ | guardrails G1–G3 and G6 tests; no-candidates path gives UNKNOWN without an LLM call |
| Buyer can change a requirement and rerun | ✅ | `test_edit_after_analysis_marks_stale_and_reanalysis_creates_version_2` |
| Previous assessment version remains accessible | ✅ | same test (version 1 text unchanged), `test_version_compare_reports_changes` |
| PDF report can be downloaded | ✅ | `test_report_pdf_contains_disclaimer_and_all_requirement_ids`, `test_report_status_is_text_not_only_color`, `test_report_renders_non_latin_text` |

### Seller workflow
| Criterion | | Evidence |
|---|---|---|
| Seller sees only buyer-shared assessments | ✅ | `test_seller_sees_only_shared_assessments`, `test_unshared_versions_are_hidden` |
| Seller can inspect requirements and evidence | ✅ | `test_seller_sees_only_shared_assessments` (seller view payload) |
| Seller can respond to a requirement or follow-up | ✅ | `test_seller_response_does_not_change_requirement_or_status`, `test_follow_up_state_machine` |
| Seller cannot silently modify buyer requirements | ✅ | `test_seller_cannot_modify_requirements` (403) |
| Buyer can request a follow-up | ✅ | `test_follow_up_state_machine`, `test_follow_up_requires_share` |

### RAG chatbot
| Criterion | | Evidence |
|---|---|---|
| User can ask a natural-language product question | ⏳ | `test_rag_answerable_returns_verified_citations` |
| System searches official knowledge | ✅ | `test_every_suggested_question_gets_a_cited_answer` (real bundle, real embeddings) |
| System searches approved resolved-query knowledge | ✅ | `test_dynamic_knowledge_loop_end_to_end` |
| Answer includes source citations | ✅ | `test_rag_answerable_returns_verified_citations` (label, URL, verbatim excerpt, no score) |
| Weak or no evidence does not produce a confident invented answer | ✅ | `test_rag_unanswerable_creates_ticket_not_answer`, `test_rag_fabricated_quote_is_discarded_after_retry`, `test_unfaithful_answer_becomes_unverified`, `test_rag_certification_question_requires_explicit_evidence` |
| Unanswered question can create a ticket | ✅ | same tests; `test_partial_answer_raises_ticket_only_when_clicked` |
| Similar approved answer can be reused | ✅ | `test_dynamic_knowledge_loop_end_to_end` (EXPERT_VERIFIED on a reworded question) |
| Similar open ticket can be detected | ✅ | `test_ticket_dedupe_links_and_increments_count`, `test_ticket_dedupe_respects_differing_qualifiers` |

### Dynamic knowledge lifecycle
| Criterion | | Evidence |
|---|---|---|
| Admin can view tickets | ✅ | `test_non_admin_cannot_use_ticket_workflow` plus dashboard and detail endpoints |
| Admin can submit a proposed answer | ✅ | `_propose` in `test_knowledge_loop.py`, `test_answer_requires_privacy_confirmation_and_min_length` |
| Answer requires approval before indexing | ✅ | `test_unapproved_answer_is_never_indexed` |
| Approved answer is embedded and stored in Qdrant | ✅ | `test_dynamic_knowledge_loop_end_to_end` |
| Future query can retrieve the new answer | ✅ | same test |
| Rejected answer is not indexed | ✅ | `test_rejected_answer_is_never_indexed` |
| Updated or revoked knowledge can be excluded from retrieval | ✅ | `test_revoked_knowledge_is_excluded_from_retrieval`, `test_superseded_version_is_excluded_and_new_version_retrieved` |
| Official and resolved-query collections remain separate | ✅ | `test_official_and_resolved_collections_remain_separate` |

### Privacy
| Criterion | | Evidence |
|---|---|---|
| Buyer assessment is private by default | ✅ | `test_buyer_cannot_read_other_buyers_assessment`, `test_buyer_cannot_read_other_buyers_results`; observed (Daniel gets 404) |
| Seller access requires explicit sharing | ✅ | `test_share_requires_explicit_consent`, `test_unshare_removes_seller_access_immediately` |
| Private buyer data is not automatically added to global knowledge | ✅ | `test_published_payload_contains_no_private_buyer_data` |
| API secrets are not exposed in frontend code | ✅ | `test_no_secrets_in_frontend_bundle`, `make check-secrets` |

### Definition of done (build prompt §20)
1. REQUIREMENTS §11: all rows above are ✅ or ⏳. ⏳ means implemented and tested with a scripted LLM, but not yet run with the real model.
2. Buyer flow end to end: covered by tests. **The manual UI run with the real LLM is pending the key.**
3. Seller flow: ✅ (tests).
4. Chatbot answer, ticket, approval and expert-verified repeat: ✅ (`test_dynamic_knowledge_loop_end_to_end`, real Qdrant and embeddings, scripted LLM). Live LLM run pending.
5. Rejected, unapproved, revoked and superseded answers are never retrievable: ✅.
6. `make test` and `make check-secrets` pass: ✅. **Clean clone verified on 2026-11-01:** `git clone` into a fresh directory, `cp .env.example .env`, `make up`, `make backend-install`, `make frontend-install`, `make migrate`, `make init-vector`, `make ingest` (0 upserts, idempotent), `make seed`, `make test` (111 passed, 1 skipped: the bundle-secrets test skips because `dist/` is built after the backend tests on a fresh clone), then `make check-secrets` (passed). Exit code 0. The only shortcut was reusing the downloaded embedding model via `FASTEMBED_CACHE_DIR`.
7. Full DEMO_SCRIPT run: **not done.** Steps 1, 9 and 13 were observed. The others need the LLM key (marked in the script).
8. No unverifiable IOMETE claims (R8), and no unrun commands in docs (R10): ✅. Every knowledge excerpt was verified against the live page by `scripts/verify_knowledge_excerpts.py`.

## What is incomplete
- No real-LLM run yet. Pending: live chat answers, PDF extraction of the demo PDF (at least 7 requirements with one clarification), real judge statuses on the FinBank requirements, the full demo script, and `make test-llm` (prompt-injection eval).
- Deployment to GitHub and Vercel: not done yet (see "Needs the user").

## P1 (G8) items built
| Item | Evidence |
|---|---|
| Seller document upload (PDF, .md, .txt), attach to response or follow-up, labelled "Seller-provided document (not official knowledge)", never indexed | `test_seller_documents_are_private_and_never_indexed`, `test_seller_document_attached_to_follow_up`, `test_seller_document_type_validation` |
| Internal owner assignment for follow-ups | `test_follow_up_owner_assignment` |
| Excel export (Requirements, Evidence and About sheets; formula-injection safe) | `test_excel_export_has_requirements_and_evidence_sheets`, `test_excel_neutralises_formula_injection` |
| Richer version comparison UI ("show changed only" toggle with counts) | frontend typecheck, lint and build |
| Dashboard filters (ticket category plus status) | `GET /api/admin/tickets?category=` and frontend build |

## How to run
These commands were verified in this repository:
```bash
cp .env.example .env
make up && make backend-install && make frontend-install
make migrate && make init-vector && make ingest && make seed
make dev-backend    # :8000
make dev-frontend   # :5173
make test && make check-secrets
make reset-demo     # before a demo
```

## Known limitations
- Demo identities only (no authentication); ownership checks, not tenant isolation. Rate limiting is in-process.
- No OCR: scanned PDFs are detected and refused with the exact message. No malware scanning, no encryption at rest, no retention policy.
- Retrieval similarity cannot distinguish on-topic but undocumented questions (see calibration). Groundedness relies on quote verification, guardrails and the faithfulness check, which reduce but cannot eliminate model error.
- The curated knowledge covers 44 documentation topics. Gaps are listed in `docs/KNOWLEDGE_GAPS.md` (for example air-gapped installs and certifications).

## OKF outcome
The specification was found: **Open Knowledge Format v0.2** (GoogleCloudPlatform/open-knowledge-format, `SPEC.md` @ `ad30107c31c06aec8a7d5636e0d1058118604e6f`). The bundle conforms to §11. The spec repo has no official validator, so the §11 rules are implemented in `scripts/ingest_okf.py --validate-only` (result: VALID, 44 files). See `knowledge/official/OKF_CONFORMANCE.md`.

## Knowledge coverage
44 approved concepts from 53 fetched pages: deployment 8, architecture 7, security 9, platform 9, integrations 11. 89 chunks indexed. Every source excerpt was verified verbatim against the live page. Gaps: `docs/KNOWLEDGE_GAPS.md`. Sources: `docs/knowledge-sources.md`.

## Calibration results
`RETRIEVAL_MIN_SCORE=0.60` (recall@6 97%, false-accept 47%; no threshold met both targets, so this is the best trade-off). `RESOLVED_REUSE_MIN_SCORE=0.70` (8/9 paraphrases flagged as reuse candidates). `TICKET_DUP_MIN_SCORE=0.85` kept, and the LLM same-intent check is mandatory. Full tables: `docs/DECISIONS.md`.

## Test results and coverage
`make test`: **118 passed, 1 deselected** (the real-LLM eval), then frontend typecheck, lint and build pass. Coverage of `app/services` from `pytest --cov=app`: 88% before the LLM-client unit tests were added. Highlights: guardrails 100%, analyze 100%, publish 99%, chunker 99%, judge 98%, retrieval/search 98%, rag/pipeline 93%, pdf_report 94%, okf_ingest 86%. `ingestion/html_text.py` is curation tooling exercised by `scripts/verify_knowledge_excerpts.py`, not by pytest.

## Needs the user
1. **Qwen API key.** Put it in `.env` as `LLM_API_KEY=...` and restart `make dev-backend`. Do not paste it into chat. Defaults are `LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`, `LLM_MODEL=qwen3.8-max` and `LLM_FAST_MODEL=qwen3.8-flash`. Change them if your account uses a different region or models. Then run: the demo script (`demo/DEMO_SCRIPT.md`, recording the observed statuses), `make test-llm`, and the G2, G4 and G5 manual checks listed in `docs/PROGRESS.md`.
2. **Deployment.** Choose the GitHub repository visibility and provide or authorise the GitHub and Vercel accounts (the `gh` and `vercel` CLIs are not installed). Vercel can host the frontend. The backend (FastAPI, PostgreSQL, Qdrant, local embeddings) needs separate hosting.
