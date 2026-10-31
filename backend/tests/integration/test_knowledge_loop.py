from sqlalchemy import select

from app.core.config import get_settings
from app.core.errors import VectorDBUnavailable
from app.models.chat import Ticket
from app.models.knowledge import KnowledgeRecord
from app.prompts.answer import AnswerDraft, ProductClaim
from app.prompts.classify import Classification
from app.prompts.faithfulness import FaithfulnessResult
from app.services.embeddings.embedder import get_embedder

from .conftest import as_user, chunks_in

ANSWER = "This internal standard is not covered in the available product documentation. A formal mapping exercise with the vendor's security team is required."
NORMALISED = "Does AcmeLake comply with the internal security standard FBS-114?"


def _unanswered(client, fake_llm, who="priya", question="Does AcmeLake comply with the FinBank Internal Security Standard FBS-114?"):
    sid = client.post("/api/chat/sessions", json={}, headers=as_user(who)).json()["id"]
    fake_llm.push(
        Classification,
        Classification(
            intent="PRODUCT_SPECIFIC",
            standalone_question=question,
            category="security",
            mentions_certification=True,
            certification_terms=["FBS-114"],
        ),
    )
    fake_llm.push(AnswerDraft, AnswerDraft(answerability="NONE"))
    m = client.post(f"/api/chat/sessions/{sid}/messages", json={"content": question}, headers=as_user(who)).json()["assistant_message"]
    assert m["answer_type"] == "UNVERIFIED" and m["ticket"]
    return m["ticket"]["id"]


def _propose(client, tid, answer=ANSWER, normalised=NORMALISED):
    admin = as_user("sam")
    assert client.post(f"/api/admin/tickets/{tid}/start-review", headers=admin).status_code == 200
    r = client.post(
        f"/api/admin/tickets/{tid}/answer",
        json={
            "normalised_question": normalised,
            "category": "security",
            "answer": answer,
            "supporting_sources": [{"title": "Security team review", "note": "internal"}],
            "privacy_confirmed": True,
        },
        headers=admin,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ANSWER_PROPOSED"


def _resolved_points(store):
    return store.scroll_all(store.resolved)


def _cite_expert(_system, messages):
    for n, body in chunks_in(messages).items():
        if "formal mapping exercise" in body:
            q = "A formal mapping exercise with the vendor's security team is required"
            return AnswerDraft(
                answerability="FULL",
                answer_markdown=f"{q} [{n}]",
                product_claims=[ProductClaim(claim=q, chunk_number=n, supporting_quote=q)],
            )
    return AnswerDraft(answerability="NONE")


def test_dynamic_knowledge_loop_end_to_end(client, fake_llm, acme_indexed, db, store):
    tid = _unanswered(client, fake_llm)
    assert _resolved_points(store) == []
    _propose(client, tid)
    assert _resolved_points(store) == []  # nothing indexed before approval
    r = client.post(f"/api/admin/tickets/{tid}/approve", headers=as_user("sam"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "PUBLISHED"
    points = _resolved_points(store)
    assert len(points) == 1 and points[0]["payload"]["validity_status"] == "ACTIVE"
    assert points[0]["payload"]["source_type"] == "expert_resolution"

    # The same question asked differently by another buyer now gets the approved answer.
    sid = client.post("/api/chat/sessions", json={}, headers=as_user("daniel")).json()["id"]
    q2 = "Is AcmeLake certified against FBS-114?"
    fake_llm.push(
        Classification,
        Classification(
            intent="PRODUCT_SPECIFIC",
            standalone_question=q2,
            category="security",
            mentions_certification=True,
            certification_terms=["FBS-114"],
        ),
    )
    fake_llm.push(AnswerDraft, _cite_expert)
    fake_llm.push(FaithfulnessResult, FaithfulnessResult(faithful=True))
    m = client.post(f"/api/chat/sessions/{sid}/messages", json={"content": q2}, headers=as_user("daniel")).json()["assistant_message"]
    assert m["answer_type"] == "EXPERT_VERIFIED", m["content"]
    assert m["citations"][0]["label"] == "Expert-verified answer"
    assert m["citations"][0]["knowledge_id"] == points[0]["id"]
    assert m["ticket"] is None

    # The original asker sees the approved answer under My questions.
    mine = client.get("/api/chat/tickets", headers=as_user("priya")).json()
    assert mine[0]["status"] == "PUBLISHED" and mine[0]["answer"]["label"] == "Expert-verified answer"
    assert "formal mapping exercise" in mine[0]["answer"]["text"]


def test_rejected_answer_is_never_indexed(client, fake_llm, acme_indexed, store):
    tid = _unanswered(client, fake_llm)
    _propose(client, tid)
    r = client.post(f"/api/admin/tickets/{tid}/reject", json={"reviewer_note": "Not accurate enough"}, headers=as_user("sam"))
    assert r.json()["status"] == "REJECTED"
    assert _resolved_points(store) == []
    # Publishing a rejected ticket is an invalid transition.
    r = client.post(f"/api/admin/tickets/{tid}/publish", headers=as_user("sam"))
    assert (
        r.status_code == 409
        and r.json()["error"]["code"] == "INVALID_STATE"
        and r.json()["error"]["details"]["allowed_transitions"] == ["reopen", "close"]
    )


def test_unapproved_answer_is_never_indexed(client, fake_llm, acme_indexed, store, db):
    tid = _unanswered(client, fake_llm)
    _propose(client, tid)
    assert _resolved_points(store) == []
    assert db.scalar(select(KnowledgeRecord)) is None
    # Approval requires ANSWER_PROPOSED; an OPEN ticket cannot be approved.
    tid2 = _unanswered(client, fake_llm, "daniel", "Is AcmeLake FIPS 140-3 validated?")
    r = client.post(f"/api/admin/tickets/{tid2}/approve", headers=as_user("sam"))
    assert r.status_code == 409


def test_answer_requires_privacy_confirmation_and_min_length(client, fake_llm, acme_indexed):
    tid = _unanswered(client, fake_llm)
    client.post(f"/api/admin/tickets/{tid}/start-review", headers=as_user("sam"))
    base = {"normalised_question": NORMALISED, "category": "security", "answer": ANSWER}
    assert (
        client.post(f"/api/admin/tickets/{tid}/answer", json=base | {"privacy_confirmed": False}, headers=as_user("sam")).status_code == 422
    )
    assert (
        client.post(
            f"/api/admin/tickets/{tid}/answer", json=base | {"answer": "too short", "privacy_confirmed": True}, headers=as_user("sam")
        ).status_code
        == 422
    )


def test_self_approval_can_be_disallowed(client, fake_llm, acme_indexed, monkeypatch):
    tid = _unanswered(client, fake_llm)
    _propose(client, tid)
    monkeypatch.setattr(get_settings(), "ALLOW_SELF_APPROVAL", False)
    r = client.post(f"/api/admin/tickets/{tid}/approve", headers=as_user("sam"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELF_APPROVAL_NOT_ALLOWED"


def test_non_admin_cannot_use_ticket_workflow(client, fake_llm, acme_indexed):
    tid = _unanswered(client, fake_llm)
    for who in ("priya", "meera"):
        assert client.get("/api/admin/tickets", headers=as_user(who)).status_code == 403
        assert client.post(f"/api/admin/tickets/{tid}/start-review", headers=as_user(who)).status_code == 403


def _publish(client, fake_llm, **kw):
    tid = _unanswered(client, fake_llm, **kw)
    _propose(client, tid)
    assert client.post(f"/api/admin/tickets/{tid}/approve", headers=as_user("sam")).json()["status"] == "PUBLISHED"
    return tid


def _resolved_hits(store, question):
    return store.search("RESOLVED", get_embedder().embed_query(question), 10)


def test_revoked_knowledge_is_excluded_from_retrieval(client, fake_llm, acme_indexed, db, store):
    _publish(client, fake_llm)
    rec = db.scalar(select(KnowledgeRecord))
    assert len(_resolved_hits(store, NORMALISED)) == 1
    r = client.post(f"/api/admin/knowledge/{rec.id}/revoke", json={"reason": "Standard was withdrawn"}, headers=as_user("sam"))
    assert r.status_code == 200 and r.json()["validity"] == "REVOKED"
    assert _resolved_hits(store, NORMALISED) == []
    pts = _resolved_points(store)
    assert len(pts) == 1 and pts[0]["payload"]["validity_status"] == "REVOKED"  # kept for audit, filtered out


def test_superseded_version_is_excluded_and_new_version_retrieved(client, fake_llm, acme_indexed, db, store):
    _publish(client, fake_llm)
    v1 = db.scalar(select(KnowledgeRecord))
    new_answer = ANSWER + " The vendor's security team publishes the mapping on request."
    r = client.post(
        f"/api/admin/knowledge/{v1.id}/supersede", json={"answer": new_answer, "privacy_confirmed": True}, headers=as_user("sam")
    )
    assert r.status_code == 200 and r.json()["version"] == 2
    hits = _resolved_hits(store, NORMALISED)
    assert [h.payload["version"] for h in hits] == [2]
    assert hits[0].payload["answer"] == new_answer
    db.expire_all()
    assert db.get(KnowledgeRecord, v1.id).validity == "SUPERSEDED"


def test_publish_failure_keeps_ticket_approved_and_retry_succeeds(client, fake_llm, acme_indexed, db, store, monkeypatch):
    tid = _unanswered(client, fake_llm)
    _propose(client, tid)
    real_upsert = store.upsert

    def broken(name, points):
        if name == store.resolved:
            raise VectorDBUnavailable()
        return real_upsert(name, points)

    monkeypatch.setattr(store, "upsert", broken)
    r = client.post(f"/api/admin/tickets/{tid}/approve", headers=as_user("sam"))
    assert r.status_code == 502 and r.json()["error"]["code"] == "PUBLISH_INDEX_FAILED"
    db.expire_all()
    t = db.get(Ticket, tid)
    assert t.status == "APPROVED" and t.publish_error
    assert db.scalar(select(KnowledgeRecord)).index_status == "FAILED"
    assert _resolved_points(store) == []

    monkeypatch.setattr(store, "upsert", real_upsert)
    for _ in range(2):  # retry is idempotent
        r = client.post(f"/api/admin/tickets/{tid}/publish", headers=as_user("sam"))
        assert r.status_code == 200 and r.json()["status"] == "PUBLISHED"
    assert len(_resolved_points(store)) == 1
    assert len(db.scalars(select(KnowledgeRecord)).all()) == 1


def test_official_and_resolved_collections_remain_separate(client, fake_llm, acme_indexed, store):
    _publish(client, fake_llm)
    official = store.scroll_all(store.official)
    resolved = _resolved_points(store)
    assert official and resolved
    assert {p["payload"]["source_type"] for p in official} == {"official"}
    assert {p["payload"]["source_type"] for p in resolved} == {"expert_resolution"}
    assert not ({p["id"] for p in official} & {p["id"] for p in resolved})


def test_published_payload_contains_no_private_buyer_data(client, fake_llm, acme_indexed, db, store):
    tid = _unanswered(
        client, fake_llm, question="FinBank needs to know: does AcmeLake comply with FBS-114? Contact priya.nair@finbank.example"
    )
    t = db.get(Ticket, tid)
    assert "FinBank" not in t.normalised_question and "priya.nair@finbank.example" not in t.normalised_question
    assert all("finbank.example" not in m["content"] for m in t.context_excerpt)
    _propose(client, tid)
    client.post(f"/api/admin/tickets/{tid}/approve", headers=as_user("sam"))
    payload = _resolved_points(store)[0]["payload"]
    blob = repr(payload).lower()
    assert "finbank" not in blob and "priya" not in blob and "@" not in blob
    assert not {"assessment_id", "requirement_id", "document", "buyer"} & set(payload)
