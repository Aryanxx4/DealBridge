from app.prompts.judge import EvidenceItem, RequirementJudgement
from app.services.assessment.guardrails import DEFAULT_MISSING, DEFAULT_NEXT_STEP, apply_guardrails

CHUNKS = {
    1: {"text": "AcmeLake supports single sign-on through SAML 2.0 and OpenID Connect identity providers."},
    2: {"text": "AcmeLake can mask sensitive columns dynamically at query time for selected groups."},
    3: {"text": "AcmeLake does not support deployment without internet access; an online licence check is required."},
    4: {"text": "AcmeLake can run fully offline after installation from a local image registry."},
}


def J(status, evidence=(), **kw):
    base = {"meaning": "m", "established": "e", "unverified": "u"}
    return RequirementJudgement(status=status, evidence=list(evidence), **(base | kw))


def E(n, quote, role="SUPPORTS"):
    return EvidenceItem(chunk_number=n, quote=quote, role=role)


SSO = E(1, "supports single sign-on through SAML 2.0")
MASK = E(2, "can mask sensitive columns dynamically at query time")


def run(j, text="Single sign-on with SAML is required.", category="SECURITY_ACCESS_CONTROL", waived=False):
    return apply_guardrails(j, CHUNKS, text, category, waived)


def test_guardrails_supported_without_evidence_becomes_unknown():
    g = run(J("SUPPORTED"))
    assert g.status == "UNKNOWN" and g.missing_information == [DEFAULT_MISSING]
    # A fabricated quote is dropped (G1) and does not rescue the status.
    g = run(J("SUPPORTED", [E(1, "AcmeLake supports Kerberos for every single user")]))
    assert g.status == "UNKNOWN" and g.evidence == [] and any("verbatim" in n for n in g.notes)
    # Only RELATED evidence: downgraded to Needs validation with a default next step (G2 + G5).
    g = run(J("SUPPORTED", [E(1, "supports single sign-on through SAML 2.0", "RELATED")]))
    assert g.status == "NEEDS_VALIDATION" and g.next_step == DEFAULT_NEXT_STEP


def test_supported_with_verified_evidence_stays_supported():
    g = run(J("SUPPORTED", [SSO]))
    assert g.status == "SUPPORTED" and g.evidence == [SSO] and g.notes == []


def test_guardrails_not_supported_requires_limits_evidence():
    g = run(J("NOT_SUPPORTED", [SSO]), text="Must run without internet access.", category="DEPLOYMENT_INFRASTRUCTURE")
    assert g.status == "UNKNOWN"
    g = run(
        J("NOT_SUPPORTED", [E(3, "does not support deployment without internet access", "LIMITS")]),
        text="Must run without internet access.",
        category="DEPLOYMENT_INFRASTRUCTURE",
    )
    assert g.status == "NOT_SUPPORTED"


def test_guardrails_certification_requires_explicit_term():
    text = "The platform must be SOC 2 certified and support SSO."
    g = run(J("SUPPORTED", [SSO], key_terms=["SOC 2"]), text=text, category="SECURITY_ACCESS_CONTROL")
    assert g.status == "UNKNOWN" and any("SOC 2" in n for n in g.notes)
    # Key terms that are not in the requirement text are ignored.
    g = run(J("SUPPORTED", [SSO], key_terms=["ISO 27001"]))
    assert g.status == "SUPPORTED" and g.key_terms == []
    # A non-certification product term missing from evidence -> Needs validation.
    g = run(J("SUPPORTED", [SSO], key_terms=["Okta"]), text="SSO via Okta is required.")
    assert g.status == "NEEDS_VALIDATION"
    # Compliance category is strict even for non-standard terms.
    g = run(J("SUPPORTED", [SSO], key_terms=["Okta"]), text="SSO via Okta is required.", category="COMPLIANCE_GOVERNANCE")
    assert g.status == "UNKNOWN"
    # Internal standard codes count as standards.
    g = run(J("SUPPORTED", [SSO], key_terms=["FBS-114"]), text="Must comply with FBS-114.")
    assert g.status == "UNKNOWN"


def test_guardrails_conflict_forces_needs_validation():
    ev = [
        E(4, "can run fully offline after installation", "SUPPORTS"),
        E(3, "does not support deployment without internet access", "LIMITS"),
    ]
    g = run(J("SUPPORTED", ev), text="Must run without internet access.", category="DEPLOYMENT_INFRASTRUCTURE")
    assert g.status == "NEEDS_VALIDATION" and g.has_conflict and g.conflict_description and len(g.evidence) == 2
    assert [e.role for e in g.evidence] == ["SUPPORTS", "LIMITS"]
    g = run(J("SUPPORTED", [SSO], conflict=True, conflict_description="Expert answer disagrees."))
    assert g.status == "NEEDS_VALIDATION" and g.conflict_description == "Expert answer disagrees."


def test_guardrails_partial_requires_both_parts():
    g = run(J("PARTIALLY_SUPPORTED", [SSO], supported_part="SAML SSO", unestablished_part=""))
    assert g.status == "NEEDS_VALIDATION"
    g = run(J("PARTIALLY_SUPPORTED", [], supported_part="SAML SSO", unestablished_part="MFA"))
    assert g.status == "NEEDS_VALIDATION"
    g = run(J("PARTIALLY_SUPPORTED", [SSO], supported_part="SAML SSO", unestablished_part="MFA"))
    assert g.status == "PARTIALLY_SUPPORTED"


def test_guardrails_vague_requirement_never_supported():
    g = run(J("SUPPORTED", [MASK]), text="Data must be protected appropriately.", waived=True)
    assert g.status == "NEEDS_VALIDATION" and g.next_step == DEFAULT_NEXT_STEP


def test_unknown_and_needs_validation_get_defaults():
    g = run(J("UNKNOWN"))
    assert g.missing_information == [DEFAULT_MISSING]
    g = run(J("NEEDS_VALIDATION", [SSO], next_step="Test SAML with your IdP."))
    assert g.next_step == "Test SAML with your IdP."
