import io
from pathlib import Path

import pymupdf
from sqlalchemy import select

from app.models.assessment import Requirement, RequirementAssessment
from app.services.reports.pdf_report import DISCLAIMER
from app.services.seed import demo_id

from .conftest import as_user
from .test_analysis import _analyze, _setup

PRIYA, MEERA, DANIEL = as_user("priya"), as_user("meera"), as_user("daniel")
SELLER_ORG = str(demo_id("org:iomete-sales"))
DEMO = Path(__file__).resolve().parents[3] / "demo"


def _analysed(client, fake_llm):
    aid, ids = _setup(client)
    assert _analyze(client, fake_llm, aid)["status"] == "SUCCEEDED"
    return aid, ids


def _share(client, aid, **kw):
    return client.post(f"/api/assessments/{aid}/share", json={"seller_org_id": SELLER_ORG, "confirm": True} | kw, headers=PRIYA)


def _pdf_text(content: bytes) -> str:
    doc = pymupdf.open(stream=content, filetype="pdf")
    return "\n".join(p.get_text("text") for p in doc)


def test_report_pdf_contains_disclaimer_and_all_requirement_ids(client, fake_llm, acme_indexed):
    aid, ids = _analysed(client, fake_llm)
    r = client.get(f"/api/assessments/{aid}/report.pdf", headers=PRIYA)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith('attachment; filename="DealBridge_Assessment_Acme-evaluation_v1_')
    text = " ".join(_pdf_text(r.content).split())
    assert " ".join(DISCLAIMER.split()) in text
    for display_id in ids:
        assert display_id in text
    assert "page 1 of" in text and "version 1" in text
    for section in (
        "Executive summary",
        "Buyer context",
        "Requirements overview",
        "Requirement details",
        "Questions for the seller",
        "Recommended next steps",
    ):
        assert section in text
    # No report before an analysis exists.
    empty = client.post("/api/assessments", json={"title": "Empty one"}, headers=PRIYA).json()["id"]
    assert client.get(f"/api/assessments/{empty}/report.pdf", headers=PRIYA).json()["error"]["code"] == "NO_ANALYSIS"


def test_report_status_is_text_not_only_color(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    text = _pdf_text(client.get(f"/api/assessments/{aid}/report.pdf", headers=PRIYA).content)
    assert "Supported" in text and "Unknown" in text
    assert "Status: Supported" in " ".join(text.split()) and "Status: Unknown" in " ".join(text.split())


def test_report_renders_non_latin_text(client, fake_llm, acme_indexed):
    aid = client.post("/api/assessments", json={"title": "Évaluation Ünïcode 数据"}, headers=PRIYA).json()["id"]
    client.post(
        f"/api/assessments/{aid}/requirements",
        json={"normalized_text": "Users must sign in with single sign-on via SAML — résumé ✓.", "category": "SECURITY_ACCESS_CONTROL"},
        headers=PRIYA,
    )
    _analyze(client, fake_llm, aid)
    text = _pdf_text(client.get(f"/api/assessments/{aid}/report.pdf", headers=PRIYA).content)
    assert "Évaluation Ünïcode" in text and "résumé" in text


def test_share_requires_explicit_consent(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    r = client.post(f"/api/assessments/{aid}/share", json={"seller_org_id": SELLER_ORG}, headers=PRIYA)
    assert r.status_code == 400 and r.json()["error"]["code"] == "CONSENT_REQUIRED"
    assert client.get("/api/seller/assessments", headers=MEERA).json() == []
    unanalysed = client.post("/api/assessments", json={"title": "Not run"}, headers=PRIYA).json()["id"]
    assert _share(client, unanalysed).json()["error"]["code"] == "NO_ANALYSIS"
    assert _share(client, aid).status_code == 200


def test_seller_sees_only_shared_assessments(client, fake_llm, acme_indexed):
    shared, _ = _analysed(client, fake_llm)
    private, _ = _analysed(client, fake_llm)
    _share(client, shared)
    lst = client.get("/api/seller/assessments", headers=MEERA).json()
    assert [x["id"] for x in lst] == [shared]
    assert lst[0]["buyer_org"] == "FinBank" and lst[0]["shared_version"] == 1
    assert client.get(f"/api/seller/assessments/{private}", headers=MEERA).status_code == 404
    view = client.get(f"/api/seller/assessments/{shared}", headers=MEERA).json()
    assert len(view["requirements"]) == 3 and view["shared_versions"] == [1]
    assert all(r["open_ticket"] is None for r in view["requirements"])
    # Another seller user in the same organisation sees it too; buyers never use seller routes.
    assert client.get("/api/seller/assessments", headers=as_user("arjun")).json()[0]["id"] == shared
    assert client.get("/api/seller/assessments", headers=PRIYA).status_code == 403


def test_unshared_versions_are_hidden(client, fake_llm, acme_indexed):
    aid, ids = _analysed(client, fake_llm)
    _share(client, aid)
    client.patch(f"/api/requirements/{ids['REQ-001']}", json={"priority": "LOW"}, headers=PRIYA)
    _analyze(client, fake_llm, aid)  # version 2 is not shared
    assert client.get(f"/api/seller/assessments/{aid}?version=2", headers=MEERA).status_code == 404
    assert client.get(f"/api/assessments/{aid}/report.pdf?version=2", headers=MEERA).status_code == 404
    assert client.get(f"/api/assessments/{aid}/report.pdf?version=1", headers=MEERA).status_code == 200


def test_unshare_removes_seller_access_immediately(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    _share(client, aid)
    fu = client.post(
        f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Please clarify SSO"}, headers=PRIYA
    ).json()
    assert client.get(f"/api/follow-ups/{fu['id']}", headers=MEERA).status_code == 200
    assert client.post(f"/api/assessments/{aid}/unshare", json={"seller_org_id": SELLER_ORG}, headers=PRIYA).json()["revoked"] == 1
    assert client.get(f"/api/seller/assessments/{aid}", headers=MEERA).status_code == 404
    assert client.get(f"/api/assessments/{aid}/report.pdf", headers=MEERA).status_code == 404
    assert client.get(f"/api/follow-ups/{fu['id']}", headers=MEERA).status_code == 404
    assert client.get("/api/seller/follow-ups", headers=MEERA).json() == []
    shares = client.get(f"/api/assessments/{aid}/shares", headers=PRIYA).json()
    assert shares[0]["active"] is False and shares[0]["revoked_at"]


def test_seller_response_does_not_change_requirement_or_status(client, fake_llm, acme_indexed, db):
    aid, ids = _analysed(client, fake_llm)
    _share(client, aid)
    rid = ids["REQ-003"]
    before_req = db.get(Requirement, rid)
    before = (before_req.normalized_text, before_req.priority, before_req.buyer_confirmed)
    r = client.post(
        f"/api/requirements/{rid}/seller-response",
        json={"version_no": 1, "body": "We are FedRAMP authorized.", "assertion": "CONFIRMS_SUPPORT"},
        headers=MEERA,
    )
    assert r.status_code == 201
    db.expire_all()
    after_req = db.get(Requirement, rid)
    assert (after_req.normalized_text, after_req.priority, after_req.buyer_confirmed) == before
    assert db.scalar(select(RequirementAssessment.status).where(RequirementAssessment.requirement_id == rid)) == "UNKNOWN"
    res = client.get(f"/api/assessments/{aid}/results", headers=PRIYA).json()
    item = next(x for x in res["requirements"] if x["requirement_id"] == rid)
    assert item["status"] == "UNKNOWN" and item["seller_responses"][0]["seller_name"] == "Meera Kapoor"
    assert item["seller_responses"][0]["assertion"] == "CONFIRMS_SUPPORT"
    # Not shared with this seller org? Responses are refused; buyers cannot use the seller endpoint.
    assert client.post(f"/api/requirements/{rid}/seller-response", json={"version_no": 1, "body": "x"}, headers=PRIYA).status_code == 403
    text = _pdf_text(client.get(f"/api/assessments/{aid}/report.pdf", headers=PRIYA).content)
    assert "Seller statement — not verified by product documentation" in " ".join(text.split())


def test_seller_cannot_see_uploaded_files_or_chats(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    client.post(
        f"/api/assessments/{aid}/documents",
        files={"file": ("FinBank.pdf", io.BytesIO((DEMO / "FinBank_Requirements.pdf").read_bytes()), "application/pdf")},
        headers=PRIYA,
    )
    _share(client, aid)
    for path in (
        f"/api/assessments/{aid}/documents",
        f"/api/assessments/{aid}/intake-chat",
        f"/api/assessments/{aid}/requirements",
        f"/api/assessments/{aid}/results",
        f"/api/assessments/{aid}",
    ):
        assert client.get(path, headers=MEERA).status_code == 403, path
    view = client.get(f"/api/seller/assessments/{aid}", headers=MEERA).json()
    blob = str(view)
    assert "FinBank.pdf" not in blob and "intake_form" not in blob and "stored_path" not in blob
    assert set(view["assessment"]["context"]) <= {"organisation_name", "industry", "use_case"}


def test_buyer_cannot_see_other_buyers_shares_or_reports(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    assert client.get(f"/api/assessments/{aid}/report.pdf", headers=DANIEL).status_code == 404
    assert (
        client.post(f"/api/assessments/{aid}/share", json={"seller_org_id": SELLER_ORG, "confirm": True}, headers=DANIEL).status_code == 404
    )


def test_follow_up_requires_share(client, fake_llm, acme_indexed):
    aid, _ = _analysed(client, fake_llm)
    r = client.post(f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Need details"}, headers=PRIYA)
    assert r.status_code == 409 and r.json()["error"]["code"] == "NOT_SHARED"


def test_follow_up_state_machine(client, fake_llm, acme_indexed):
    aid, ids = _analysed(client, fake_llm)
    _share(client, aid)
    fu = client.post(
        f"/api/assessments/{aid}/follow-ups",
        json={
            "seller_org_id": SELLER_ORG,
            "subject": "FedRAMP evidence",
            "message": "Can you send evidence?",
            "related_requirement_ids": [ids["REQ-003"]],
        },
        headers=PRIYA,
    ).json()
    fid = fu["id"]
    assert fu["status"] == "REQUESTED" and fu["messages"][0]["author"] == "Priya Nair"
    # Buyer cannot accept; seller responds directly from REQUESTED (implies acceptance).
    assert client.post(f"/api/follow-ups/{fid}/accept", headers=PRIYA).status_code == 403
    r = client.post(f"/api/follow-ups/{fid}/responses", json={"body": "We'll share the package under NDA."}, headers=MEERA).json()
    assert r["status"] == "RESPONDED" and r["seller_decision"] == "ACCEPTED"
    assert client.post(f"/api/follow-ups/{fid}/accept", headers=MEERA).json()["error"]["code"] == "INVALID_STATE"
    # Buyer adds information: RESPONDED -> IN_PROGRESS.
    r = client.post(f"/api/follow-ups/{fid}/messages", json={"body": "NDA attached separately."}, headers=PRIYA).json()
    assert r["status"] == "IN_PROGRESS" and len(r["messages"]) == 3
    r = client.post(f"/api/follow-ups/{fid}/close", headers=MEERA).json()
    assert r["status"] == "CLOSED" and r["allowed_actions"] == []
    assert (
        client.post(f"/api/follow-ups/{fid}/messages", json={"body": "one more"}, headers=PRIYA).json()["error"]["code"] == "INVALID_STATE"
    )
    # Accept then reject paths on a second thread.
    f2 = client.post(f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Second"}, headers=PRIYA).json()[
        "id"
    ]
    assert client.post(f"/api/follow-ups/{f2}/accept", headers=MEERA).json()["status"] == "IN_PROGRESS"
    assert client.post(f"/api/follow-ups/{f2}/reject", json={"reason": "Not now"}, headers=MEERA).json()["error"]["code"] == "INVALID_STATE"
    f3 = client.post(f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Third"}, headers=PRIYA).json()[
        "id"
    ]
    r = client.post(f"/api/follow-ups/{f3}/reject", json={"reason": "Out of scope for this deal"}, headers=MEERA).json()
    assert r["status"] == "CLOSED" and r["seller_decision"] == "REJECTED"
    queue = client.get("/api/seller/follow-ups", headers=MEERA).json()
    assert {q["id"] for q in queue} == {fid, f2, f3}
    assert client.get(f"/api/follow-ups/{fid}", headers=DANIEL).status_code == 404
