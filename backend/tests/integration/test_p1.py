import io

from openpyxl import load_workbook

from app.services.seed import demo_id

from .conftest import as_user
from .test_analysis import _analyze, _setup

PRIYA, MEERA, ARJUN, DANIEL = as_user("priya"), as_user("meera"), as_user("arjun"), as_user("daniel")
SELLER_ORG = str(demo_id("org:iomete-sales"))


def _shared(client, fake_llm):
    aid, ids = _setup(client)
    _analyze(client, fake_llm, aid)
    client.post(f"/api/assessments/{aid}/share", json={"seller_org_id": SELLER_ORG, "confirm": True}, headers=PRIYA)
    return aid, ids


def test_excel_export_has_requirements_and_evidence_sheets(client, fake_llm, acme_indexed):
    aid, ids = _shared(client, fake_llm)
    for who in (PRIYA, MEERA):
        r = client.get(f"/api/assessments/{aid}/report.xlsx", headers=who)
        assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
        wb = load_workbook(io.BytesIO(r.content))
        assert wb.sheetnames == ["Requirements", "Evidence", "About"]
        req_ids = [row[0].value for row in wb["Requirements"].iter_rows(min_row=2)]
        assert req_ids == ["REQ-001", "REQ-002", "REQ-003"]
        statuses = {row[0].value: row[4].value for row in wb["Requirements"].iter_rows(min_row=2)}
        assert statuses["REQ-001"] == "Supported" and statuses["REQ-003"] == "Unknown"
        assert {row[1].value for row in wb["Evidence"].iter_rows(min_row=2)} == {"SUPPORTS"}
    assert client.get(f"/api/assessments/{aid}/report.xlsx", headers=DANIEL).status_code == 404


def test_excel_neutralises_formula_injection(client, fake_llm, acme_indexed):
    aid = client.post("/api/assessments", json={"title": "Formula test"}, headers=PRIYA).json()["id"]
    client.post(
        f"/api/assessments/{aid}/requirements", json={"normalized_text": '=HYPERLINK("http://evil") single sign-on via SAML'}, headers=PRIYA
    )
    _analyze(client, fake_llm, aid)
    wb = load_workbook(io.BytesIO(client.get(f"/api/assessments/{aid}/report.xlsx", headers=PRIYA).content))
    assert wb["Requirements"]["B2"].value.startswith("'=")


def test_follow_up_owner_assignment(client, fake_llm, acme_indexed):
    aid, _ = _shared(client, fake_llm)
    fid = client.post(
        f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Owner test"}, headers=PRIYA
    ).json()["id"]
    arjun_id = str(demo_id("user:arjun"))
    r = client.patch(f"/api/follow-ups/{fid}/owner", json={"owner_user_id": arjun_id}, headers=MEERA)
    assert r.status_code == 200 and r.json()["assigned_owner"] == "Arjun Rao" and r.json()["status"] == "REQUESTED"
    # Only sellers in the same organisation can own it; buyers cannot assign.
    assert (
        client.patch(f"/api/follow-ups/{fid}/owner", json={"owner_user_id": str(demo_id("user:priya"))}, headers=MEERA).status_code == 422
    )
    assert client.patch(f"/api/follow-ups/{fid}/owner", json={"owner_user_id": arjun_id}, headers=PRIYA).status_code == 403
    client.post(f"/api/follow-ups/{fid}/close", headers=PRIYA)
    assert (
        client.patch(f"/api/follow-ups/{fid}/owner", json={"owner_user_id": None}, headers=MEERA).json()["error"]["code"] == "INVALID_STATE"
    )
    assert [u["display_name"] for u in client.get("/api/seller/team", headers=MEERA).json()] == ["Arjun Rao", "Meera Kapoor"]


def test_seller_documents_are_private_and_never_indexed(client, fake_llm, acme_indexed, store):
    aid, ids = _shared(client, fake_llm)
    official_before, resolved_before = store.count(store.official), store.count(store.resolved)
    up = client.post(
        "/api/seller/documents",
        files={"file": ("fedramp-note.md", io.BytesIO(b"# Note\nSeller-provided statement."), "text/markdown")},
        headers=MEERA,
    )
    assert up.status_code == 201 and up.json()["label"] == "Seller-provided document (not official knowledge)"
    doc_id = up.json()["id"]
    resp = client.post(
        f"/api/requirements/{ids['REQ-003']}/seller-response",
        json={"version_no": 1, "body": "See attached note.", "assertion": "NONE"},
        headers=MEERA,
    ).json()
    r = client.post(f"/api/seller-responses/{resp['id']}/attachments", json={"document_ids": [doc_id]}, headers=MEERA)
    assert r.status_code == 200 and r.json()["attachment_document_ids"] == [doc_id]
    # The owning buyer sees it labelled and can download it; another buyer cannot; the uploader's org can.
    res = client.get(f"/api/assessments/{aid}/results", headers=PRIYA).json()
    att = next(x for x in res["requirements"] if x["display_id"] == "REQ-003")["seller_responses"][0]["attachments"][0]
    assert att["label"] == "Seller-provided document (not official knowledge)"
    assert client.get(f"/api/documents/{doc_id}/download", headers=PRIYA).content == b"# Note\nSeller-provided statement."
    assert client.get(f"/api/documents/{doc_id}/download", headers=DANIEL).status_code == 404
    assert client.get(f"/api/documents/{doc_id}/download", headers=ARJUN).status_code == 200
    # Never embedded or indexed.
    assert (store.count(store.official), store.count(store.resolved)) == (official_before, resolved_before)


def test_seller_document_attached_to_follow_up(client, fake_llm, acme_indexed):
    aid, _ = _shared(client, fake_llm)
    fid = client.post(f"/api/assessments/{aid}/follow-ups", json={"seller_org_id": SELLER_ORG, "subject": "Docs"}, headers=PRIYA).json()[
        "id"
    ]
    pdf = b"%PDF-1.4\n%fake but only stored, never parsed\n%%EOF"
    doc = client.post("/api/seller/documents", files={"file": ("brief.pdf", io.BytesIO(pdf), "application/pdf")}, headers=MEERA).json()
    f = client.post(f"/api/follow-ups/{fid}/attachments", json={"document_ids": [doc["id"]]}, headers=MEERA).json()
    assert f["messages"][-1]["attachments"][0]["filename"] == "brief.pdf"
    assert client.get(f"/api/documents/{doc['id']}/download", headers=PRIYA).status_code == 200


def test_seller_document_type_validation(client):
    bad = client.post("/api/seller/documents", files={"file": ("x.exe", io.BytesIO(b"MZ..."), "application/octet-stream")}, headers=MEERA)
    assert bad.status_code == 415
    fake_pdf = client.post("/api/seller/documents", files={"file": ("x.pdf", io.BytesIO(b"<html>"), "application/pdf")}, headers=MEERA)
    assert fake_pdf.status_code == 415
    assert (
        client.post("/api/seller/documents", files={"file": ("x.md", io.BytesIO(b"hi"), "text/markdown")}, headers=PRIYA).status_code == 403
    )
