from sqlalchemy import func, select

from app.core.errors import LLMUnavailable
from app.models.chat import Message, Ticket
from app.prompts.answer import AnswerDraft, ProductClaim
from app.prompts.classify import Classification
from app.prompts.faithfulness import FaithfulnessResult
from app.prompts.ticket_dup import TicketDupResult
from app.services.vector.qdrant_store import QdrantStore, set_store

from .conftest import as_user, chunks_in


def _session(client, who="priya"):
    r = client.post("/api/chat/sessions", json={}, headers=as_user(who))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _ask(client, sid, q, who="priya"):
    return client.post(f"/api/chat/sessions/{sid}/messages", json={"content": q}, headers=as_user(who))


def _product(q, **kw):
    return Classification(intent="PRODUCT_SPECIFIC", standalone_question=q, category=kw.pop("category", "security"), **kw)


def _claim_from(fragment, answerability="FULL"):
    """Scripted generator: cite the retrieved chunk that contains `fragment`, quoting it verbatim."""

    def respond(_system, messages):
        for n, body in chunks_in(messages).items():
            if fragment.lower() in " ".join(body.split()).lower():
                return AnswerDraft(
                    answerability=answerability,
                    answer_markdown=f"Yes. {fragment} [{n}]",
                    product_claims=[ProductClaim(claim="x", chunk_number=n, supporting_quote=fragment)],
                )
        return AnswerDraft(answerability="NONE")

    return respond


def test_rag_answerable_returns_verified_citations(client, fake_llm, acme_indexed):
    sid = _session(client)
    quote = "AcmeLake supports single sign-on through SAML 2.0 and OpenID Connect identity providers"
    fake_llm.push(Classification, _product("Does AcmeLake support single sign-on with SAML?"))
    fake_llm.push(AnswerDraft, _claim_from(quote))
    fake_llm.push(FaithfulnessResult, FaithfulnessResult(faithful=True))
    r = _ask(client, sid, "Does it support SSO with SAML?")
    assert r.status_code == 200, r.text
    m = r.json()["assistant_message"]
    assert m["answer_type"] == "OFFICIAL_VERIFIED"
    assert m["ticket"] is None and len(m["citations"]) == 1
    c = m["citations"][0]
    assert c["label"] == "Official documentation" and c["knowledge_id"] == "acmelake.security.sso"
    assert c["excerpt"] == quote and c["source_url"].startswith("https://docs.acmelake.example/")
    assert "relevance_score" not in c  # scores are never shown to buyers (R3)


def test_rag_fabricated_quote_is_discarded_after_retry(client, fake_llm, acme_indexed, db):
    sid = _session(client)
    bad = AnswerDraft(
        answerability="FULL",
        answer_markdown="It supports Kerberos [1]",
        product_claims=[
            ProductClaim(claim="kerberos", chunk_number=1, supporting_quote="AcmeLake supports Kerberos for every user account")
        ],
    )
    fake_llm.push(Classification, _product("Does AcmeLake support Kerberos?"))
    fake_llm.push(AnswerDraft, bad, bad)
    r = _ask(client, sid, "Does AcmeLake support Kerberos?")
    m = r.json()["assistant_message"]
    assert m["answer_type"] == "UNVERIFIED" and m["citations"] == [] and m["ticket"]["display_id"].startswith("TCK-")
    assert db.get(Ticket, m["ticket"]["id"]).reason == "WEAK_EVIDENCE"


def test_rag_unanswerable_creates_ticket_not_answer(client, fake_llm, acme_indexed, db):
    sid = _session(client)
    fake_llm.push(Classification, _product("What is the AcmeLake annual license price per core?", category="OTHER"))
    fake_llm.push(AnswerDraft, AnswerDraft(answerability="NONE"))
    r = _ask(client, sid, "What does AcmeLake cost per core per year?")
    m = r.json()["assistant_message"]
    assert m["answer_type"] == "UNVERIFIED" and m["citations"] == []
    assert m["ticket"]["status"] == "OPEN" and m["ticket"]["display_id"] in m["content"]
    assert "couldn't verify" in m["content"]
    t = db.get(Ticket, m["ticket"]["id"])
    assert t.original_question == "What does AcmeLake cost per core per year?"
    assert t.normalised_question == "What is the AcmeLake annual license price per core?"
    assert t.status == "OPEN" and t.retrieval_trace["hits"] is not None


def test_rag_certification_question_requires_explicit_evidence(client, fake_llm, acme_indexed):
    sid = _session(client)
    fake_llm.push(
        Classification,
        _product("Is AcmeLake SOC 2 certified for its SSO feature?", mentions_certification=True, certification_terms=["SOC 2"]),
    )
    # A real, verifiable quote about SSO, but no chunk names SOC 2.
    fake_llm.push(AnswerDraft, _claim_from("AcmeLake supports single sign-on through SAML 2.0"))
    r = _ask(client, sid, "Is AcmeLake SOC 2 certified for SSO?")
    m = r.json()["assistant_message"]
    assert m["answer_type"] == "UNVERIFIED" and m["ticket"] is not None and m["citations"] == []


def test_rag_general_question_is_labelled_general(client, fake_llm, acme_indexed, db):
    sid = _session(client)
    fake_llm.push(
        Classification, Classification(intent="GENERAL_EDUCATIONAL", standalone_question="What is a data lakehouse?", category="concepts")
    )
    fake_llm.push(
        AnswerDraft,
        AnswerDraft(answerability="NONE", general_explanation_markdown="A lakehouse combines a data lake with warehouse features."),
    )
    r = _ask(client, sid, "What is a lakehouse?")
    m = r.json()["assistant_message"]
    assert m["answer_type"] == "GENERAL_EXPLANATION" and m["citations"] == [] and m["ticket"] is None
    assert "lakehouse" in m["content"].lower()
    assert db.scalar(select(func.count(Ticket.id))) == 0


def test_rag_infrastructure_failure_creates_no_ticket(client, fake_llm, acme_indexed, db, store):
    sid = _session(client)
    fake_llm.push(Classification, LLMUnavailable())
    r = _ask(client, sid, "Does AcmeLake support SSO?")
    assert r.status_code == 503 and r.json()["error"]["code"] == "LLM_UNAVAILABLE"
    # Vector database outage.
    set_store(QdrantStore("http://127.0.0.1:1", None, store.official, store.resolved, 384))
    try:
        fake_llm.push(Classification, _product("Does AcmeLake support SSO?"))
        r = _ask(client, sid, "Does AcmeLake support SSO?")
        assert r.status_code == 503 and r.json()["error"]["code"] == "VECTOR_DB_UNAVAILABLE"
    finally:
        set_store(store)
    assert db.scalar(select(func.count(Ticket.id))) == 0
    users = db.scalars(select(Message).where(Message.conversation_id == sid, Message.role == "USER")).all()
    assert len(users) == 2  # the user's messages are still saved


def test_ticket_dedupe_links_and_increments_count(client, fake_llm, acme_indexed, db):
    q = "Is AcmeLake FedRAMP authorized?"
    for who, wording in (("priya", "Is AcmeLake FedRAMP authorized?"), ("daniel", "does acmelake have fedramp authorization")):
        sid = _session(client, who)
        fake_llm.push(Classification, _product(q, mentions_certification=True, certification_terms=["FedRAMP"]))
        fake_llm.push(AnswerDraft, AnswerDraft(answerability="NONE"))
        if who == "daniel":
            fake_llm.push(TicketDupResult, TicketDupResult(same_intent=True, differing_qualifiers=[]))
        m = _ask(client, sid, wording, who).json()["assistant_message"]
        assert m["answer_type"] == "UNVERIFIED"
    tickets = db.scalars(select(Ticket)).all()
    assert len(tickets) == 1 and tickets[0].occurrence_count == 2
    assert m["ticket"]["linked"] is True and "already with the product team" in m["content"]


def test_ticket_dedupe_respects_differing_qualifiers(client, fake_llm, acme_indexed, db):
    questions = ["Can AcmeLake run on-premises on Kubernetes 1.30?", "Can AcmeLake run on-premises on Kubernetes 1.24?"]
    for i, q in enumerate(questions):
        sid = _session(client)
        fake_llm.push(Classification, _product(q, category="deployment"))
        fake_llm.push(AnswerDraft, AnswerDraft(answerability="NONE"))
        if i == 1:
            fake_llm.push(TicketDupResult, TicketDupResult(same_intent=False, differing_qualifiers=["Kubernetes version 1.30 vs 1.24"]))
        _ask(client, sid, q)
    assert db.scalar(select(func.count(Ticket.id))) == 2


def test_partial_answer_raises_ticket_only_when_clicked(client, fake_llm, acme_indexed, db):
    sid = _session(client)
    quote = "AcmeLake can mask sensitive columns dynamically at query time"
    fake_llm.push(Classification, _product("Can AcmeLake mask columns and encrypt backups?"))
    draft = _claim_from(quote, "PARTIAL")

    def partial(system, messages):
        d = draft(system, messages)
        return d.model_copy(update={"unverified_aspects": ["Backup encryption"]})

    fake_llm.push(AnswerDraft, partial)
    fake_llm.push(FaithfulnessResult, FaithfulnessResult(faithful=True))
    m = _ask(client, sid, "Can AcmeLake mask columns and encrypt backups?").json()["assistant_message"]
    assert m["answer_type"] == "PARTIAL" and m["unverified_aspects"] == ["Backup encryption"] and m["ticket"] is None
    assert db.scalar(select(func.count(Ticket.id))) == 0
    r = client.post(f"/api/chat/messages/{m['id']}/raise-ticket", headers=as_user("priya"))
    assert r.status_code == 200 and r.json()["ticket"]["display_id"].startswith("TCK-")
    assert db.scalar(select(Ticket.reason)) == "PARTIAL"


def test_unfaithful_answer_becomes_unverified(client, fake_llm, acme_indexed):
    sid = _session(client)
    fake_llm.push(Classification, _product("Does AcmeLake support SSO?"))
    fake_llm.push(AnswerDraft, _claim_from("AcmeLake supports single sign-on through SAML 2.0"))
    fake_llm.push(FaithfulnessResult, FaithfulnessResult(faithful=False, unsupported_statements=["claims MFA"]))
    m = _ask(client, sid, "Does AcmeLake support SSO?").json()["assistant_message"]
    assert m["answer_type"] == "UNVERIFIED" and m["ticket"] is not None


def test_small_talk_and_requirement_redirect_create_no_ticket(client, fake_llm, acme_indexed, db):
    sid = _session(client)
    fake_llm.push(Classification, Classification(intent="SMALL_TALK", standalone_question="hi"))
    assert _ask(client, sid, "hi!").json()["assistant_message"]["answer_type"] == "SMALL_TALK"
    fake_llm.push(Classification, Classification(intent="REQUIREMENT_STATEMENT", standalone_question="We need on-prem"))
    m = _ask(client, sid, "We need an on-prem deployment").json()["assistant_message"]
    assert m["answer_type"] == "REDIRECT" and m["action"]["type"] == "OPEN_ASSESSMENT"
    assert db.scalar(select(func.count(Ticket.id))) == 0


def test_buyer_cannot_use_other_buyers_chat_session(client, fake_llm):
    sid = _session(client, "priya")
    assert client.get(f"/api/chat/sessions/{sid}", headers=as_user("daniel")).status_code == 404
    r = client.post(f"/api/chat/sessions/{sid}/messages", json={"content": "hello"}, headers=as_user("daniel"))
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/chat/sessions", headers=as_user("daniel")).json() == []


def test_question_length_limit(client):
    sid = _session(client)
    r = client.post(f"/api/chat/sessions/{sid}/messages", json={"content": "x" * 2001}, headers=as_user("priya"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
