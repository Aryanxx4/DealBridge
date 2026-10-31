import io
from pathlib import Path

import pymupdf
from sqlalchemy import select

from app.core.config import get_settings
from app.models.assessment import Assessment, RequirementRevision
from app.prompts.extract_pdf import ExtractedRequirement, ExtractionResult
from app.prompts.intake_chat import IntakeTurn, ProposedOp
from app.services.ingestion.pdf_reader import SCANNED_MESSAGE

from .conftest import as_user

DEMO = Path(__file__).resolve().parents[3] / "demo"
PRIYA = as_user("priya")


def _assessment(client, who="priya", title="FinBank evaluation"):
    r = client.post(
        "/api/assessments", json={"title": title, "context": {"organisation_name": "FinBank", "industry": "Banking"}}, headers=as_user(who)
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _upload(client, aid, data: bytes, name="req.pdf", ctype="application/pdf", who="priya"):
    return client.post(f"/api/assessments/{aid}/documents", files={"file": (name, io.BytesIO(data), ctype)}, headers=as_user(who))


def _add(client, aid, text, **kw):
    r = client.post(f"/api/assessments/{aid}/requirements", json={"normalized_text": text, **kw}, headers=PRIYA)
    assert r.status_code == 201, r.text
    return r.json()


# ---- PDF upload ------------------------------------------------------------------------------
def test_pdf_text_extraction(client, db):
    aid = _assessment(client)
    r = _upload(client, aid, (DEMO / "FinBank_Requirements.pdf").read_bytes(), "FinBank_Requirements.pdf")
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["extraction_status"] == "OK" and d["page_count"] == 3 and len(d["sha256"]) == 64
    from app.models.assessment import UploadedDocument

    doc = db.get(UploadedDocument, d["id"])
    assert "on-premises" in doc.pages[1]["text"] and doc.pages[1]["page"] == 2
    # Stored under a generated name, never the original filename.
    assert Path(doc.stored_path).name == f"{d['id']}.pdf" and "FinBank_Requirements" not in doc.stored_path


def test_pdf_scanned_is_flagged(client):
    aid = _assessment(client)
    r = _upload(client, aid, (DEMO / "FinBank_Requirements_scanned.pdf").read_bytes())
    assert r.status_code == 201 and r.json()["extraction_status"] == "SCANNED"
    assert r.json()["extraction_message"] == SCANNED_MESSAGE
    r = client.post(f"/api/assessments/{aid}/requirements/extract", json={"document_id": r.json()["id"]}, headers=PRIYA)
    assert r.status_code == 422 and r.json()["error"]["code"] == "DOCUMENT_NOT_EXTRACTABLE"


def test_pdf_malformed_rejected(client):
    aid = _assessment(client)
    r = _upload(client, aid, b"%PDF-1.7\n this is not really a pdf \n%%EOF")
    assert r.status_code == 422 and r.json()["error"]["code"] == "MALFORMED_PDF"


def test_pdf_encrypted_rejected(client, tmp_path):
    src = pymupdf.open(DEMO / "FinBank_Requirements.pdf")
    out = tmp_path / "enc.pdf"
    src.save(out, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret")
    aid = _assessment(client)
    r = _upload(client, aid, out.read_bytes())
    assert r.status_code == 422 and r.json()["error"]["code"] == "ENCRYPTED_PDF"


def test_pdf_size_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "MAX_UPLOAD_MB", 1)
    aid = _assessment(client)
    r = _upload(client, aid, b"%PDF-1.7\n" + b"0" * (1024 * 1024 + 10))
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_pdf_too_many_pages(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "MAX_PDF_PAGES", 2)
    aid = _assessment(client)
    r = _upload(client, aid, (DEMO / "FinBank_Requirements.pdf").read_bytes())
    assert r.status_code == 422 and r.json()["error"]["code"] == "TOO_MANY_PAGES"


def test_pdf_wrong_type_rejected_by_magic_bytes(client):
    aid = _assessment(client)
    r = _upload(client, aid, b"<html><script>alert(1)</script></html>", "evil.pdf", "application/pdf")
    assert r.status_code == 415 and r.json()["error"]["code"] == "NOT_A_PDF"
    r = _upload(client, aid, (DEMO / "FinBank_Requirements.pdf").read_bytes(), "x.pdf", "text/plain")
    assert r.status_code == 415


# ---- requirement service ---------------------------------------------------------------------
def test_requirement_edit_marks_assessment_stale_and_logs_revision(client, db):
    aid = _assessment(client)
    req = _add(client, aid, "The platform must run on-premises.")
    a = db.get(Assessment, aid)
    a.status = "ANALYZED"
    db.commit()
    rev_before = a.requirement_set_revision
    r = client.patch(
        f"/api/requirements/{req['id']}",
        json={"normalized_text": "The platform must run on-premises in two data centres.", "priority": "HIGH"},
        headers=PRIYA,
    )
    assert r.status_code == 200 and r.json()["buyer_confirmed"] is True
    db.expire_all()
    a = db.get(Assessment, aid)
    assert a.status == "STALE" and a.requirement_set_revision == rev_before + 1
    revs = db.scalars(
        select(RequirementRevision).where(RequirementRevision.requirement_id == req["id"]).order_by(RequirementRevision.revision_no)
    ).all()
    assert [v.change_type for v in revs] == ["CREATED", "EDITED"]
    assert revs[1].changes["normalized_text"]["before"] == "The platform must run on-premises." and revs[1].origin == "UI"
    hist = client.get(f"/api/requirements/{req['id']}/history", headers=PRIYA).json()
    assert hist[1]["change_type"] == "EDITED" and hist[1]["actor"] == "Priya Nair"


def test_original_text_is_immutable(client):
    aid = _assessment(client)
    req = _add(client, aid, "Data must stay in our infrastructure.")
    r = client.patch(f"/api/requirements/{req['id']}", json={"original_text": "Something else"}, headers=PRIYA)
    assert r.status_code == 422
    assert (
        client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()[0]["original_text"]
        == "Data must stay in our infrastructure."
    )


def _extract_with(client, fake_llm, aid, items):
    doc = _upload(client, aid, (DEMO / "FinBank_Requirements.pdf").read_bytes()).json()
    fake_llm.push(ExtractionResult, ExtractionResult(requirements=items))
    r = client.post(f"/api/assessments/{aid}/requirements/extract", json={"document_id": doc["id"]}, headers=PRIYA)
    assert r.status_code == 202, r.text
    job = client.get(f"/api/jobs/{r.json()['job_id']}", headers=PRIYA).json()
    assert job["status"] == "SUCCEEDED", job
    return job["result"]


def test_needs_clarification_blocks_confirmation_until_waived(client, fake_llm):
    aid = _assessment(client)
    vague = ExtractedRequirement(
        original_text="The solution must be compliant with all applicable banking regulations.",
        normalized_text="The solution must be compliant with all applicable banking regulations.",
        category="COMPLIANCE_GOVERNANCE",
        priority="HIGH",
        priority_basis="must",
        needs_clarification=True,
        clarifying_question="Which regulations or certifications do you mean?",
        page=2,
    )
    _extract_with(client, fake_llm, aid, [vague])
    req = client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()[0]
    assert req["needs_clarification"] and not req["buyer_confirmed"]
    r = client.post(f"/api/requirements/{req['id']}/confirm", headers=PRIYA)
    assert r.status_code == 422 and r.json()["error"]["details"]["clarifying_question"]
    # Confirm-all skips it.
    assert client.post(f"/api/assessments/{aid}/requirements/confirm-all", headers=PRIYA).json()["confirmed"] == []
    assert client.post(f"/api/requirements/{req['id']}/waive-clarification", headers=PRIYA).json()["clarification_waived"] is True
    assert client.post(f"/api/requirements/{req['id']}/confirm", headers=PRIYA).json()["buyer_confirmed"] is True


def test_pdf_extraction_job_verifies_quotes_and_pages(client, fake_llm, db):
    aid = _assessment(client)
    real = ExtractedRequirement(
        original_text="The platform must be deployable on-premises in FinBank's own data centres.",
        normalized_text="The platform must be deployable on-premises in FinBank's data centres.",
        category="DEPLOYMENT_INFRASTRUCTURE",
        priority="HIGH",
        priority_basis="must",
        page=1,
    )
    invented = ExtractedRequirement(
        original_text="The platform must offer quantum-safe encryption for all tables.",
        normalized_text="Quantum-safe encryption for all tables.",
        category="SECURITY_ACCESS_CONTROL",
        page=2,
    )
    result = _extract_with(client, fake_llm, aid, [real, invented])
    assert result == {
        "created": 2,
        "duplicates_skipped": 0,
        "needs_clarification_count": 0,
        "truncated": False,
        "document_id": result["document_id"],
    }
    reqs = {r["display_id"]: r for r in client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()}
    assert (
        reqs["REQ-001"]["source_reference"]["page"] == 2 and reqs["REQ-001"]["source_reference"]["quote_verified"] is True
    )  # corrected page
    assert reqs["REQ-002"]["source_reference"]["quote_verified"] is False
    assert all(r["source_type"] == "PDF" and not r["buyer_confirmed"] for r in reqs.values())


def test_dedupe_skips_duplicates(client, fake_llm):
    aid = _assessment(client)
    _add(client, aid, "All customer data must remain within FinBank-controlled infrastructure.")
    dup = ExtractedRequirement(
        original_text="All customer data must remain within FinBank-controlled infrastructure at all times.",
        normalized_text="All customer data must remain within FinBank controlled infrastructure.",
        category="DATA_SOVEREIGNTY_RESIDENCY",
    )
    new = ExtractedRequirement(
        original_text="Access control must be granular, role-based and enforceable down to individual columns.",
        normalized_text="Role-based access control enforceable down to individual columns.",
        category="SECURITY_ACCESS_CONTROL",
    )
    repeat = new.model_copy(update={"normalized_text": "Role based access control enforceable down to individual columns"})
    result = _extract_with(client, fake_llm, aid, [dup, new, repeat])
    assert result["created"] == 1 and result["duplicates_skipped"] == 2


def test_form_resubmission_replaces_only_changed_fields(client, fake_llm, db):
    aid = _assessment(client)
    form = {
        "organisation_name": "FinBank",
        "use_case": "Consolidate regulatory reporting.",
        "deployment_preference": "ON_PREMISES",
        "data_scale": "About 400 TB",
        "security_access": "Column-level access control for analysts.",
        "priorities": {"deployment_preference": "HIGH"},
    }
    fake_llm.push(
        ExtractionResult,
        ExtractionResult(
            requirements=[
                ExtractedRequirement(
                    original_text="Consolidate regulatory reporting.",
                    normalized_text="Support consolidated regulatory reporting.",
                    category="FUNCTIONAL_CAPABILITY",
                )
            ]
        ),
    )
    fake_llm.push(
        ExtractionResult,
        ExtractionResult(
            requirements=[
                ExtractedRequirement(
                    original_text="Column-level access control for analysts.",
                    normalized_text="Column-level access control for analysts.",
                    category="SECURITY_ACCESS_CONTROL",
                )
            ]
        ),
    )
    r = client.post(f"/api/assessments/{aid}/form", json=form, headers=PRIYA)
    assert r.status_code == 200 and r.json()["created"] == 4, r.text
    reqs = client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()
    dep = next(x for x in reqs if x["source_reference"]["field_key"] == "deployment_preference")
    assert dep["normalized_text"] == "Deployment preference: on-premises." and dep["priority"] == "HIGH" and not dep["buyer_confirmed"]
    sec_id = next(x["id"] for x in reqs if x["source_reference"]["field_key"] == "security_access")

    # Resubmit: deployment changed, data scale cleared, others unchanged (no LLM calls for unchanged fields).
    form2 = form | {"deployment_preference": "HYBRID", "data_scale": ""}
    r = client.post(f"/api/assessments/{aid}/form", json=form2, headers=PRIYA)
    assert r.json() == {"created": 1, "removed": 2, "changed_fields": ["deployment_preference", "data_scale"]}
    reqs = client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()
    texts = [x["normalized_text"] for x in reqs]
    assert "Deployment preference: hybrid (on-premises and cloud)." in texts and not any("Data volume" in t for t in texts)
    assert sec_id in [x["id"] for x in reqs]  # unchanged field kept its requirement
    removed = client.get(f"/api/assessments/{aid}/requirements?include_removed=true", headers=PRIYA).json()
    assert sum(x["is_removed"] for x in removed) == 2
    assert db.get(Assessment, aid).context["organisation_name"] == "FinBank"


def test_intake_chat_air_gapped_to_hybrid(client, fake_llm):
    aid = _assessment(client)
    ag = _add(client, aid, "The platform must support an air-gapped deployment.", category="DEPLOYMENT_INFRASTRUCTURE", priority="HIGH")
    msg = "We no longer require air-gapped deployment, but hybrid deployment is now mandatory"
    fake_llm.push(
        IntakeTurn,
        IntakeTurn(
            assistant_message="I'll remove the air-gapped requirement and add hybrid deployment as mandatory.",
            proposed_ops=[
                ProposedOp(op="REMOVE", target_display_id=ag["display_id"], source_quote="We no longer require air-gapped deployment"),
                ProposedOp(
                    op="ADD",
                    normalized_text="The platform must support hybrid deployment.",
                    category="DEPLOYMENT_INFRASTRUCTURE",
                    priority="HIGH",
                    priority_basis="mandatory",
                    source_quote="hybrid deployment is now mandatory",
                ),
                ProposedOp(op="UPDATE", target_display_id="REQ-999", normalized_text="ghost", source_quote="x"),  # unknown target: dropped
            ],
        ),
    )
    r = client.post(f"/api/assessments/{aid}/intake-chat/messages", json={"content": msg}, headers=PRIYA)
    assert r.status_code == 200, r.text
    prop = r.json()["proposal"]
    assert [o["op"] for o in prop["ops"]] == ["REMOVE", "ADD"]
    # Nothing changes until the buyer applies.
    assert len(client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()) == 1
    r = client.post(f"/api/assessments/{aid}/change-proposals/{prop['id']}/apply", json={"selected_op_indexes": [0, 1]}, headers=PRIYA)
    assert r.status_code == 200, r.text
    assert [c["op"] for c in r.json()["changed"]] == ["REMOVE", "ADD"]
    reqs = client.get(f"/api/assessments/{aid}/requirements", headers=PRIYA).json()
    assert len(reqs) == 1 and reqs[0]["normalized_text"] == "The platform must support hybrid deployment."
    assert reqs[0]["priority"] == "HIGH" and reqs[0]["buyer_confirmed"] and reqs[0]["source_type"] == "CHAT"
    assert client.post(f"/api/assessments/{aid}/change-proposals/{prop['id']}/apply", json={}, headers=PRIYA).status_code == 409


def test_stale_proposal_is_rejected(client, fake_llm):
    aid = _assessment(client)
    req = _add(client, aid, "The platform must support an air-gapped deployment.")
    fake_llm.push(
        IntakeTurn,
        IntakeTurn(
            assistant_message="Removing it.",
            proposed_ops=[ProposedOp(op="REMOVE", target_display_id=req["display_id"], source_quote="remove air-gapped")],
        ),
    )
    prop = client.post(f"/api/assessments/{aid}/intake-chat/messages", json={"content": "remove air-gapped"}, headers=PRIYA).json()[
        "proposal"
    ]
    client.patch(f"/api/requirements/{req['id']}", json={"normalized_text": "Air-gapped deployment is preferred."}, headers=PRIYA)
    r = client.post(f"/api/assessments/{aid}/change-proposals/{prop['id']}/apply", json={}, headers=PRIYA)
    assert r.status_code == 409 and r.json()["error"]["code"] == "STALE_PROPOSAL"


def test_mutations_blocked_while_analyzing(client, db):
    aid = _assessment(client)
    req = _add(client, aid, "The platform must run on-premises.")
    a = db.get(Assessment, aid)
    a.status = "ANALYZING"
    db.commit()
    r = client.patch(f"/api/requirements/{req['id']}", json={"priority": "LOW"}, headers=PRIYA)
    assert r.status_code == 409 and r.json()["error"]["code"] == "JOB_IN_PROGRESS"


def test_display_ids_are_never_reused(client, db):
    aid = _assessment(client)
    first = _add(client, aid, "Requirement number one.")
    client.delete(f"/api/requirements/{first['id']}", headers=PRIYA)
    second = _add(client, aid, "Requirement number two.")
    assert first["display_id"] == "REQ-001" and second["display_id"] == "REQ-002"
    restored = client.post(f"/api/requirements/{first['id']}/restore", headers=PRIYA).json()
    assert restored["is_removed"] is False and restored["display_id"] == "REQ-001"


def test_buyer_cannot_read_other_buyers_assessment(client):
    aid = _assessment(client)
    req = _add(client, aid, "The platform must run on-premises.")
    other = as_user("daniel")
    assert client.get(f"/api/assessments/{aid}", headers=other).status_code == 404
    assert client.get(f"/api/assessments/{aid}/requirements", headers=other).status_code == 404
    assert client.patch(f"/api/requirements/{req['id']}", json={"priority": "LOW"}, headers=other).status_code == 404
    assert client.get("/api/assessments", headers=other).json() == []


def test_seller_cannot_modify_requirements(client):
    aid = _assessment(client)
    req = _add(client, aid, "The platform must run on-premises.")
    meera = as_user("meera")
    r = client.patch(f"/api/requirements/{req['id']}", json={"priority": "LOW"}, headers=meera)
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert client.delete(f"/api/requirements/{req['id']}", headers=meera).status_code == 403
    assert (
        client.post(f"/api/assessments/{aid}/requirements", json={"normalized_text": "Seller added this."}, headers=meera).status_code
        == 403
    )
