import uuid

from app.services.vector.qdrant_store import retrievable_filter


def _payload(kid, approval, validity, text):
    return {"knowledge_id": kid, "approval_status": approval, "validity_status": validity, "text": text, "source_type": "x"}


def test_search_filter_excludes_non_active_and_non_approved(db, store, embedder):
    text = "AcmeLake supports single sign-on with SAML."
    vec = embedder.embed_documents([text])[0]
    cases = [
        ("ok", "approved", "ACTIVE"),
        ("draft", "draft", "ACTIVE"),
        ("revoked", "approved", "REVOKED"),
        ("superseded", "approved", "SUPERSEDED"),
    ]
    for coll in (store.official, store.resolved):
        store.upsert(coll, [(str(uuid.uuid4()), vec, _payload(k, a, v, text)) for k, a, v in cases])
    q = embedder.embed_query("Does AcmeLake support SSO?")
    for kind in ("OFFICIAL", "RESOLVED"):
        hits = store.search(kind, q, 10)
        assert {h.payload["knowledge_id"] for h in hits} == {"ok"}, kind
    # The filter is the single source of truth.
    must = {c.key: c.match.value for c in retrievable_filter().must}
    assert must == {"approval_status": "approved", "validity_status": "ACTIVE"}
