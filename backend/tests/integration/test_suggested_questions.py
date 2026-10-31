"""Every suggested question must be answerable from the curated IOMETE bundle (real embeddings, real Qdrant)."""

from app.core.config import get_settings
from app.prompts.answer import AnswerDraft, ProductClaim
from app.prompts.classify import Classification
from app.prompts.faithfulness import FaithfulnessResult
from app.services.ingestion.okf_ingest import IngestOptions, ingest_bundle
from app.services.rag.suggested import SUGGESTED_QUESTIONS
from app.services.retrieval.search import retrieve

from .conftest import as_user, chunks_in, first_sentence

EXPECTED = {
    SUGGESTED_QUESTIONS[0]: {"iomete.deployment.on-premises", "iomete.deployment.options"},
    SUGGESTED_QUESTIONS[1]: {"iomete.security.authentication", "iomete.security.ldap"},
    SUGGESTED_QUESTIONS[2]: {"iomete.security.access-policies", "iomete.security.row-level-filter", "iomete.security.data-masking"},
    SUGGESTED_QUESTIONS[3]: {"iomete.architecture.lakehouse", "iomete.architecture.storage", "iomete.architecture.compute-clusters"},
    SUGGESTED_QUESTIONS[4]: {
        "iomete.integrations.tableau",
        "iomete.integrations.power-bi",
        "iomete.integrations.metabase",
        "iomete.integrations.superset",
    },
    SUGGESTED_QUESTIONS[5]: {"iomete.architecture.time-travel", "iomete.architecture.iceberg"},
}


def _echo_top_chunk(_system, messages):
    chunks = chunks_in(messages)
    n = min(chunks)
    quote = first_sentence(chunks[n])
    return AnswerDraft(
        answerability="FULL",
        answer_markdown=f"{quote} [{n}]",
        product_claims=[ProductClaim(claim=quote, chunk_number=n, supporting_quote=quote)],
    )


def test_every_suggested_question_gets_a_cited_answer(client, fake_llm, db, store, embedder):
    res = ingest_bundle(db, IngestOptions(triggered_by="test"), bundle=get_settings().bundle_dir, store=store, embedder=embedder)
    assert res.added == 44
    assert set(EXPECTED) == set(SUGGESTED_QUESTIONS)
    sid = client.post("/api/chat/sessions", json={}, headers=as_user("priya")).json()["id"]
    for q in SUGGESTED_QUESTIONS:
        retrieved, _ = retrieve(q)
        top3 = {c["knowledge_id"] for c in retrieved.kept[:3]}
        assert top3 & EXPECTED[q], (q, top3)
        fake_llm.push(Classification, Classification(intent="PRODUCT_SPECIFIC", standalone_question=q))
        fake_llm.push(AnswerDraft, _echo_top_chunk)
        fake_llm.push(FaithfulnessResult, FaithfulnessResult(faithful=True))
        m = client.post(f"/api/chat/sessions/{sid}/messages", json={"content": q}, headers=as_user("priya")).json()["assistant_message"]
        assert m["answer_type"] == "OFFICIAL_VERIFIED", (q, m["content"])
        assert m["citations"] and m["citations"][0]["source_url"].startswith("https://iomete.com/resources/")
