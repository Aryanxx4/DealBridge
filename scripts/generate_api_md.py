"""Regenerate docs/API.md from the running app's OpenAPI schema (route table) plus hand-written notes."""

from collections import defaultdict
from pathlib import Path

import _bootstrap  # noqa: F401

from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
INTRO = '# DealBridge API\n\nBase path `/api`. JSON in and out (snake_case); ids are UUIDs; timestamps ISO-8601 UTC. Every call except `/api/health` and `/api/identity/users` sends `X-Demo-User-Id: <uuid>` (demo identity, **not authentication**). List endpoints accept `limit` (default 50, max 200) and `offset`. Long operations return `202 {"job_id"}`; poll `GET /api/jobs/{id}`. Every response carries `X-Request-Id`. Interactive OpenAPI docs: `http://localhost:8000/docs`.\n\nErrors always use `{"error": {"code", "message", "details"}}`. Ownership failures return **404** (never 403) so existence is not confirmed; wrong role returns 403 `FORBIDDEN_ROLE`.\n\nThis file lists every route registered in the running app ({n} routes), generated from its OpenAPI schema by `python scripts/generate_api_md.py`.\n\n'
TAIL = "## Sharing route roles\n\n- `GET /api/seller-orgs`, `POST /assessments/{id}/share`, `/unshare`, `GET .../shares`, `POST .../follow-ups`, `POST /follow-ups/{id}/messages`: BUYER (owner).\n- `GET /api/seller/assessments`, `GET /api/seller/assessments/{id}`, `GET /api/seller/follow-ups`, `POST /requirements/{id}/seller-response`, `POST /follow-ups/{id}/accept|reject|responses`: SELLER (organisation must hold an unrevoked share).\n- `GET /assessments/{id}/report.pdf`, `GET /assessments/{id}/report.xlsx`, `GET .../follow-ups`, `GET /follow-ups/{id}`, `POST /follow-ups/{id}/close`: BUYER owner or SELLER with a share.\n- P1: `POST /api/seller/documents` (SELLER; PDF, .md or .txt, never indexed), `POST /api/seller-responses/{id}/attachments` and `POST /api/follow-ups/{id}/attachments` (SELLER), `PATCH /api/follow-ups/{id}/owner` and `GET /api/seller/team` (SELLER), `GET /api/documents/{id}/download` (uploading seller org, or the buyer who owns the assessment it is attached to).\n\n## Stable error codes\n\n`UNKNOWN_IDENTITY` (401), `FORBIDDEN_ROLE` (403), `NOT_FOUND` (404), `VALIDATION_ERROR` (422), `NOT_A_PDF` (415), `FILE_TOO_LARGE` (413), `TOO_MANY_PAGES` (422), `ENCRYPTED_PDF` (422), `MALFORMED_PDF` (422), `DOCUMENT_NOT_EXTRACTABLE` (422), `NO_CONFIRMED_REQUIREMENTS` (422), `JOB_IN_PROGRESS` (409), `STALE_PROPOSAL` (409), `NO_ANALYSIS` (409), `CONSENT_REQUIRED` (400), `NOT_SHARED` (409), `INVALID_STATE` (409, `details.allowed_transitions`), `SELF_APPROVAL_NOT_ALLOWED` (403), `PUBLISH_INDEX_FAILED` (502), `LLM_NOT_CONFIGURED` (503), `LLM_UNAVAILABLE` (503), `LLM_OUTPUT_INVALID` (502), `VECTOR_DB_UNAVAILABLE` (503), `EMBEDDING_UNAVAILABLE` (503), `REINDEX_REQUIRED` (503), `RATE_LIMITED` (429 with `Retry-After`), `PAYLOAD_TOO_LARGE` (413, JSON over 1 MB), `INTERNAL_ERROR` (500).\n\n## Key response shapes\n\n- **Chat message** (`POST /api/chat/sessions/{id}/messages` → `{user_message, assistant_message}`): `answer_type` (OFFICIAL_VERIFIED | EXPERT_VERIFIED | MIXED_VERIFIED | GENERAL_EXPLANATION | PARTIAL | UNVERIFIED | REDIRECT | OUT_OF_SCOPE | SMALL_TALK), `content` (Markdown with [n] markers), `citations[]` (`n, collection, label, knowledge_id, chunk_id, title, heading_path, source_url, source_document, excerpt, version, last_verified_at | approved_at`; no scores for non-admins), `general_explanation_markdown`, `unverified_aspects[]`, `ticket {id, display_id, status, linked}`.\n- **Results** (`GET /api/assessments/{id}/results?version=N`): `version`, `summary {executive_summary, status_counts, blockers, next_steps, assumptions, missing_information, questions_for_seller}`, `knowledge_updated`, `changes_since_previous`, `requirements[]` with `status`, `explanation {meaning, established, unverified, next_step}`, `evidence[]` (role SUPPORTS | LIMITS | RELATED, label, excerpt, source), `guardrail_notes`, `open_ticket`, `answer_available`, `seller_responses[]`.\n- **Job** (`GET /api/jobs/{id}`): `status` (QUEUED | RUNNING | SUCCEEDED | FAILED), `progress_done/total/message`, `result`, `error_code/message`.\n"
ROLE = {
    "health": "none",
    "identity": "none / any",
    "jobs": "any (own jobs; admin all)",
    "admin-knowledge": "ADMIN",
    "chat": "any identity (own sessions only)",
    "admin-tickets": "ADMIN",
    "admin": "ADMIN",
    "assessments": "BUYER (owner)",
    "analysis": "BUYER (owner)",
    "sharing": "see 'Sharing route roles'",
    "p1": "see 'Sharing route roles'",
}
ORDER = ["health", "identity", "jobs", "assessments", "analysis", "sharing", "p1", "chat", "admin-tickets", "admin-knowledge", "admin"]


def main() -> None:
    spec = create_app(skip_startup_checks=True).openapi()
    groups = defaultdict(list)
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            body = op.get("requestBody", {}).get("content", {})
            req = next(iter(body.values()), {}).get("schema", {}) if body else {}
            name = req.get("$ref", "").split("/")[-1] or (
                "multipart file" if "multipart/form-data" in body else ("JSON object" if body else "—")
            )
            groups[(op.get("tags") or ["other"])[0]].append((path, method.upper(), name))
    total = sum(len(v) for v in groups.values())
    out = [INTRO.replace("{n}", str(total))]
    for tag in ORDER + sorted(set(groups) - set(ORDER)):
        if tag in groups:
            out += [f"## {tag}", "", f"Role: {ROLE.get(tag, '')}", "", "| Method | Path | Request body |", "|---|---|---|"]
            out += [f"| {m} | `{p}` | {r} |" for p, m, r in sorted(groups[tag])]
            out.append("")
    (ROOT / "docs" / "API.md").write_text("\n".join(out) + "\n" + TAIL)
    print(f"docs/API.md: {total} routes")


if __name__ == "__main__":
    main()
