# DealBridge API

Base path `/api`. JSON in and out (snake_case); ids are UUIDs; timestamps ISO-8601 UTC. Every call except `/api/health` and `/api/identity/users` sends `X-Demo-User-Id: <uuid>` (demo identity, **not authentication**). List endpoints accept `limit` (default 50, max 200) and `offset`. Long operations return `202 {"job_id"}`; poll `GET /api/jobs/{id}`. Every response carries `X-Request-Id`. Interactive OpenAPI docs: `http://localhost:8000/docs`.

Errors always use `{"error": {"code", "message", "details"}}`. Ownership failures return **404** (never 403) so existence is not confirmed; wrong role returns 403 `FORBIDDEN_ROLE`.

This file lists every route registered in the running app (78 routes), generated from its OpenAPI schema by `python scripts/generate_api_md.py`.


## health

Role: none

| Method | Path | Request body |
|---|---|---|
| GET | `/api/health` | — |

## identity

Role: none / any

| Method | Path | Request body |
|---|---|---|
| GET | `/api/identity/me` | — |
| GET | `/api/identity/users` | — |

## jobs

Role: any (own jobs; admin all)

| Method | Path | Request body |
|---|---|---|
| GET | `/api/jobs/{job_id}` | — |

## assessments

Role: BUYER (owner)

| Method | Path | Request body |
|---|---|---|
| GET | `/api/assessments` | — |
| POST | `/api/assessments` | AssessmentCreate |
| GET | `/api/assessments/{assessment_id}` | — |
| PATCH | `/api/assessments/{assessment_id}` | AssessmentPatch |
| POST | `/api/assessments/{assessment_id}/change-proposals/{proposal_id}/apply` | ApplyProposalIn |
| POST | `/api/assessments/{assessment_id}/change-proposals/{proposal_id}/dismiss` | — |
| GET | `/api/assessments/{assessment_id}/documents` | — |
| POST | `/api/assessments/{assessment_id}/documents` | Body_upload_document_api_assessments__assessment_id__documents_post |
| POST | `/api/assessments/{assessment_id}/form` | JSON object |
| GET | `/api/assessments/{assessment_id}/intake-chat` | — |
| POST | `/api/assessments/{assessment_id}/intake-chat/messages` | IntakeMessageIn |
| GET | `/api/assessments/{assessment_id}/requirements` | — |
| POST | `/api/assessments/{assessment_id}/requirements` | RequirementCreate |
| POST | `/api/assessments/{assessment_id}/requirements/confirm-all` | — |
| POST | `/api/assessments/{assessment_id}/requirements/extract` | ExtractRequest |
| DELETE | `/api/requirements/{requirement_id}` | — |
| PATCH | `/api/requirements/{requirement_id}` | RequirementPatch |
| POST | `/api/requirements/{requirement_id}/confirm` | — |
| GET | `/api/requirements/{requirement_id}/history` | — |
| POST | `/api/requirements/{requirement_id}/restore` | — |
| POST | `/api/requirements/{requirement_id}/waive-clarification` | — |

## analysis

Role: BUYER (owner)

| Method | Path | Request body |
|---|---|---|
| POST | `/api/assessments/{assessment_id}/analyze` | — |
| GET | `/api/assessments/{assessment_id}/pending-changes` | — |
| GET | `/api/assessments/{assessment_id}/results` | — |
| GET | `/api/assessments/{assessment_id}/versions` | — |
| GET | `/api/assessments/{assessment_id}/versions/{a_no}/compare/{b_no}` | — |

## sharing

Role: see 'Sharing route roles'

| Method | Path | Request body |
|---|---|---|
| GET | `/api/assessments/{assessment_id}/follow-ups` | — |
| POST | `/api/assessments/{assessment_id}/follow-ups` | FollowUpIn |
| GET | `/api/assessments/{assessment_id}/report.pdf` | — |
| POST | `/api/assessments/{assessment_id}/share` | ShareIn |
| GET | `/api/assessments/{assessment_id}/shares` | — |
| POST | `/api/assessments/{assessment_id}/unshare` | UnshareIn |
| GET | `/api/follow-ups/{follow_up_id}` | — |
| POST | `/api/follow-ups/{follow_up_id}/accept` | — |
| POST | `/api/follow-ups/{follow_up_id}/close` | — |
| POST | `/api/follow-ups/{follow_up_id}/messages` | MessageIn |
| POST | `/api/follow-ups/{follow_up_id}/reject` | ReasonIn |
| POST | `/api/follow-ups/{follow_up_id}/responses` | MessageIn |
| POST | `/api/requirements/{requirement_id}/seller-response` | SellerResponseIn |
| GET | `/api/seller-orgs` | — |
| GET | `/api/seller/assessments` | — |
| GET | `/api/seller/assessments/{assessment_id}` | — |
| GET | `/api/seller/follow-ups` | — |

## p1

Role: see 'Sharing route roles'

| Method | Path | Request body |
|---|---|---|
| GET | `/api/assessments/{assessment_id}/report.xlsx` | — |
| GET | `/api/documents/{document_id}/download` | — |
| POST | `/api/follow-ups/{follow_up_id}/attachments` | AttachIn |
| PATCH | `/api/follow-ups/{follow_up_id}/owner` | OwnerIn |
| POST | `/api/seller-responses/{response_id}/attachments` | AttachIn |
| POST | `/api/seller/documents` | Body_upload_seller_document_api_seller_documents_post |
| GET | `/api/seller/team` | — |

## chat

Role: any identity (own sessions only)

| Method | Path | Request body |
|---|---|---|
| POST | `/api/chat/messages/{message_id}/raise-ticket` | — |
| GET | `/api/chat/sessions` | — |
| POST | `/api/chat/sessions` | SessionCreate |
| GET | `/api/chat/sessions/{session_id}` | — |
| POST | `/api/chat/sessions/{session_id}/messages` | MessageCreate |
| GET | `/api/chat/suggested-questions` | — |
| GET | `/api/chat/tickets` | — |

## admin-tickets

Role: ADMIN

| Method | Path | Request body |
|---|---|---|
| GET | `/api/admin/tickets` | — |
| GET | `/api/admin/tickets/{ticket_id}` | — |
| POST | `/api/admin/tickets/{ticket_id}/answer` | AnswerIn |
| POST | `/api/admin/tickets/{ticket_id}/approve` | — |
| POST | `/api/admin/tickets/{ticket_id}/close` | CloseIn |
| POST | `/api/admin/tickets/{ticket_id}/publish` | — |
| POST | `/api/admin/tickets/{ticket_id}/reject` | NoteIn |
| POST | `/api/admin/tickets/{ticket_id}/reopen` | — |
| POST | `/api/admin/tickets/{ticket_id}/request-revision` | NoteIn |
| POST | `/api/admin/tickets/{ticket_id}/start-review` | — |

## admin-knowledge

Role: ADMIN

| Method | Path | Request body |
|---|---|---|
| GET | `/api/admin/knowledge` | — |
| POST | `/api/admin/knowledge/reindex` | — |
| GET | `/api/admin/knowledge/status` | — |
| POST | `/api/admin/knowledge/{record_id}/revoke` | RevokeIn |
| POST | `/api/admin/knowledge/{record_id}/supersede` | SupersedeIn |

## admin

Role: ADMIN

| Method | Path | Request body |
|---|---|---|
| GET | `/api/admin/audit` | — |
| GET | `/api/admin/dashboard` | — |

## Sharing route roles

- `GET /api/seller-orgs`, `POST /assessments/{id}/share`, `/unshare`, `GET .../shares`, `POST .../follow-ups`, `POST /follow-ups/{id}/messages`: BUYER (owner).
- `GET /api/seller/assessments`, `GET /api/seller/assessments/{id}`, `GET /api/seller/follow-ups`, `POST /requirements/{id}/seller-response`, `POST /follow-ups/{id}/accept|reject|responses`: SELLER (organisation must hold an unrevoked share).
- `GET /assessments/{id}/report.pdf`, `GET /assessments/{id}/report.xlsx`, `GET .../follow-ups`, `GET /follow-ups/{id}`, `POST /follow-ups/{id}/close`: BUYER owner or SELLER with a share.
- P1: `POST /api/seller/documents` (SELLER; PDF, .md or .txt, never indexed), `POST /api/seller-responses/{id}/attachments` and `POST /api/follow-ups/{id}/attachments` (SELLER), `PATCH /api/follow-ups/{id}/owner` and `GET /api/seller/team` (SELLER), `GET /api/documents/{id}/download` (uploading seller org, or the buyer who owns the assessment it is attached to).

## Stable error codes

`UNKNOWN_IDENTITY` (401), `FORBIDDEN_ROLE` (403), `NOT_FOUND` (404), `VALIDATION_ERROR` (422), `NOT_A_PDF` (415), `FILE_TOO_LARGE` (413), `TOO_MANY_PAGES` (422), `ENCRYPTED_PDF` (422), `MALFORMED_PDF` (422), `DOCUMENT_NOT_EXTRACTABLE` (422), `NO_CONFIRMED_REQUIREMENTS` (422), `JOB_IN_PROGRESS` (409), `STALE_PROPOSAL` (409), `NO_ANALYSIS` (409), `CONSENT_REQUIRED` (400), `NOT_SHARED` (409), `INVALID_STATE` (409, `details.allowed_transitions`), `SELF_APPROVAL_NOT_ALLOWED` (403), `PUBLISH_INDEX_FAILED` (502), `LLM_NOT_CONFIGURED` (503), `LLM_UNAVAILABLE` (503), `LLM_OUTPUT_INVALID` (502), `VECTOR_DB_UNAVAILABLE` (503), `EMBEDDING_UNAVAILABLE` (503), `REINDEX_REQUIRED` (503), `RATE_LIMITED` (429 with `Retry-After`), `PAYLOAD_TOO_LARGE` (413, JSON over 1 MB), `INTERNAL_ERROR` (500).

## Key response shapes

- **Chat message** (`POST /api/chat/sessions/{id}/messages` → `{user_message, assistant_message}`): `answer_type` (OFFICIAL_VERIFIED | EXPERT_VERIFIED | MIXED_VERIFIED | GENERAL_EXPLANATION | PARTIAL | UNVERIFIED | REDIRECT | OUT_OF_SCOPE | SMALL_TALK), `content` (Markdown with [n] markers), `citations[]` (`n, collection, label, knowledge_id, chunk_id, title, heading_path, source_url, source_document, excerpt, version, last_verified_at | approved_at`; no scores for non-admins), `general_explanation_markdown`, `unverified_aspects[]`, `ticket {id, display_id, status, linked}`.
- **Results** (`GET /api/assessments/{id}/results?version=N`): `version`, `summary {executive_summary, status_counts, blockers, next_steps, assumptions, missing_information, questions_for_seller}`, `knowledge_updated`, `changes_since_previous`, `requirements[]` with `status`, `explanation {meaning, established, unverified, next_step}`, `evidence[]` (role SUPPORTS | LIMITS | RELATED, label, excerpt, source), `guardrail_notes`, `open_ticket`, `answer_available`, `seller_responses[]`.
- **Job** (`GET /api/jobs/{id}`): `status` (QUEUED | RUNNING | SUCCEEDED | FAILED), `progress_done/total/message`, `result`, `error_code/message`.
