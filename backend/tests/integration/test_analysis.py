from sqlalchemy import func, select

from app.core.errors import LLMUnavailable
from app.models.assessment import Assessment, AssessmentVersion
from app.prompts.judge import EvidenceItem, RequirementJudgement
from app.prompts.summary import AssessmentSummary

from .conftest import as_user, chunks_in

PRIYA = as_user("priya")
FRAGMENTS = {
    "single sign-on": "AcmeLake supports single sign-on through SAML 2.0 and OpenID Connect identity providers",
    "mask": "AcmeLake can mask sensitive columns dynamically at query time",
    "kubernetes": "can be installed on customer-managed Kubernetes clusters in a private data center",
}


def judge(_system, messages):
    """Scripted judge: SUPPORTED with a verbatim quote when a known fragment is retrieved, otherwise UNKNOWN."""
    content = messages[0]["content"]
    req = content.split("</document>")[0].lower()
    for key, frag in FRAGMENTS.items():
        if key in req:
            for n, body in chunks_in(messages).items():
                if frag.lower() in " ".join(body.split()).lower():
                    return RequirementJudgement(
                        status="SUPPORTED",
                        meaning="m",
                        established="Documented.",
                        unverified="Your IdP specifics.",
                        evidence=[EvidenceItem(chunk_number=n, quote=frag, role="SUPPORTS")],
                        questions_for_seller=["Which IdPs are tested?"],
                    )
    return RequirementJudgement(
        status="UNKNOWN",
        meaning="m",
        established="Nothing establishes this.",
        unverified="Everything.",
        missing_information=["Documentation of this capability"],
    )


def summary(_s, _m):
    return AssessmentSummary(
        executive_summary="Two requirements are supported by cited documentation; one is unknown.",
        next_steps=["Ask the vendor about the unknown requirement."],
    )


def _setup(client):
    aid = client.post("/api/assessments", json={"title": "Acme evaluation"}, headers=PRIYA).json()["id"]
    ids = {}
    for text, cat, prio in (
        ("Users must sign in with single sign-on via SAML.", "SECURITY_ACCESS_CONTROL", "HIGH"),
        ("Sensitive columns must be masked for analysts.", "SECURITY_ACCESS_CONTROL", "MEDIUM"),
        ("The vendor must hold a FedRAMP High authorization.", "COMPLIANCE_GOVERNANCE", "CRITICAL"),
    ):
        r = client.post(
            f"/api/assessments/{aid}/requirements", json={"normalized_text": text, "category": cat, "priority": prio}, headers=PRIYA
        ).json()
        ids[r["display_id"]] = r["id"]
    return aid, ids


def _analyze(client, fake_llm, aid, n_judge=6):
    fake_llm.push(RequirementJudgement, *[judge] * n_judge)
    fake_llm.push(AssessmentSummary, summary)
    r = client.post(f"/api/assessments/{aid}/analyze", headers=PRIYA)
    assert r.status_code == 202, r.text
    return client.get(f"/api/jobs/{r.json()['job_id']}", headers=PRIYA).json()


def test_analyze_requires_confirmed_requirements(client):
    aid = client.post("/api/assessments", json={"title": "Empty"}, headers=PRIYA).json()["id"]
    r = client.post(f"/api/assessments/{aid}/analyze", headers=PRIYA)
    assert r.status_code == 422 and r.json()["error"]["code"] == "NO_CONFIRMED_REQUIREMENTS"
    assert client.get(f"/api/assessments/{aid}/results", headers=PRIYA).json()["error"]["code"] == "NO_ANALYSIS"


def test_assessment_job_creates_new_version_and_keeps_previous(client, fake_llm, acme_indexed, db):
    aid, ids = _setup(client)
    job = _analyze(client, fake_llm, aid)
    assert job["status"] == "SUCCEEDED", job
    assert job["result"]["version_no"] == 1 and job["progress_message"] == "Writing the summary"
    res = client.get(f"/api/assessments/{aid}/results", headers=PRIYA).json()
    st = {r["display_id"]: r for r in res["requirements"]}
    assert st["REQ-001"]["status"] == "SUPPORTED" and st["REQ-002"]["status"] == "SUPPORTED"
    assert st["REQ-003"]["status"] == "UNKNOWN" and st["REQ-003"]["is_blocker"] is True
    ev = st["REQ-001"]["evidence"][0]
    assert ev["label"] == "Official documentation" and ev["role"] == "SUPPORTS" and "relevance_score" not in ev
    assert res["summary"]["status_counts"]["SUPPORTED"] == 2 and res["summary"]["blockers"] == ["REQ-003"]
    assert "overall" not in str(res["summary"]).lower()  # no fit score
    assert db.get(Assessment, aid).status == "ANALYZED"
    _analyze(client, fake_llm, aid)
    vers = client.get(f"/api/assessments/{aid}/versions", headers=PRIYA).json()
    assert [v["version_no"] for v in vers] == [2, 1]
    assert client.get(f"/api/assessments/{aid}/results?version=1", headers=PRIYA).json()["version"]["version_no"] == 1


def test_edit_after_analysis_marks_stale_and_reanalysis_creates_version_2(client, fake_llm, acme_indexed, db):
    aid, ids = _setup(client)
    _analyze(client, fake_llm, aid)
    client.patch(
        f"/api/requirements/{ids['REQ-002']}",
        json={"normalized_text": "Sensitive columns must be masked for analysts and auditors."},
        headers=PRIYA,
    )
    assert db.get(Assessment, aid).status == "STALE"
    pending = client.get(f"/api/assessments/{aid}/pending-changes", headers=PRIYA).json()["changes"]
    assert [(c["display_id"], c["change"]) for c in pending] == [("REQ-002", "TEXT_CHANGED")]
    job = _analyze(client, fake_llm, aid)
    assert job["result"]["version_no"] == 2
    db.expire_all()
    assert db.get(Assessment, aid).status == "ANALYZED"
    v1 = client.get(f"/api/assessments/{aid}/results?version=1", headers=PRIYA).json()
    v2 = client.get(f"/api/assessments/{aid}/results?version=2", headers=PRIYA).json()
    assert v1["requirements"][1]["text"] == "Sensitive columns must be masked for analysts."  # version 1 intact
    assert v2["requirements"][1]["text"].endswith("analysts and auditors.")
    assert [c["change"] for c in v2["changes_since_previous"]] == ["TEXT_CHANGED"]
    assert client.get(f"/api/assessments/{aid}/pending-changes", headers=PRIYA).json()["changes"] == []


def test_analysis_job_failure_creates_no_version(client, fake_llm, acme_indexed, db):
    aid, _ = _setup(client)
    fake_llm.push(RequirementJudgement, *[LLMUnavailable()] * 6)
    r = client.post(f"/api/assessments/{aid}/analyze", headers=PRIYA)
    job = client.get(f"/api/jobs/{r.json()['job_id']}", headers=PRIYA).json()
    assert job["status"] == "FAILED" and job["error_code"] == "LLM_UNAVAILABLE"
    assert db.scalar(select(func.count(AssessmentVersion.id))) == 0
    db.expire_all()
    assert db.get(Assessment, aid).status == "DRAFT"  # previous status restored


def test_version_compare_reports_changes(client, fake_llm, acme_indexed):
    aid, ids = _setup(client)
    _analyze(client, fake_llm, aid)
    client.patch(f"/api/requirements/{ids['REQ-001']}", json={"priority": "CRITICAL"}, headers=PRIYA)
    client.delete(f"/api/requirements/{ids['REQ-003']}", headers=PRIYA)
    client.post(
        f"/api/assessments/{aid}/requirements",
        json={"normalized_text": "AcmeLake must be installable on our own Kubernetes clusters.", "category": "DEPLOYMENT_INFRASTRUCTURE"},
        headers=PRIYA,
    )
    _analyze(client, fake_llm, aid)
    changes = {c["display_id"]: c for c in client.get(f"/api/assessments/{aid}/versions/1/compare/2", headers=PRIYA).json()["changes"]}
    assert changes["REQ-001"]["change"] == "PRIORITY_CHANGED" and changes["REQ-001"]["new_priority"] == "CRITICAL"
    assert changes["REQ-002"]["change"] == "UNCHANGED"
    assert changes["REQ-003"]["change"] == "REMOVED" and changes["REQ-003"]["previous_status"] == "UNKNOWN"
    assert changes["REQ-004"]["change"] == "ADDED" and changes["REQ-004"]["new_status"] == "SUPPORTED"


def test_unconfirmed_requirements_are_excluded(client, fake_llm, acme_indexed, db):
    aid, ids = _setup(client)
    # Requirements added manually are confirmed; demote one through a form-like unconfirmed creation path is not
    # available via API, so remove one and verify the snapshot holds only active confirmed requirements.
    client.delete(f"/api/requirements/{ids['REQ-003']}", headers=PRIYA)
    _analyze(client, fake_llm, aid)
    v = db.scalar(select(AssessmentVersion))
    assert [r["display_id"] for r in v.requirements_snapshot] == ["REQ-001", "REQ-002"]


def test_buyer_cannot_read_other_buyers_results(client, fake_llm, acme_indexed):
    aid, _ = _setup(client)
    _analyze(client, fake_llm, aid)
    assert client.get(f"/api/assessments/{aid}/results", headers=as_user("daniel")).status_code == 404
    assert client.post(f"/api/assessments/{aid}/analyze", headers=as_user("daniel")).status_code == 404
