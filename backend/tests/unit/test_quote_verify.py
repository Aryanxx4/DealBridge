from app.services.retrieval.quote_verify import contains_term, normalize, verify_quote

CHUNK = "> AcmeLake supports **single sign-on** through SAML 2.0 and OpenID Connect identity providers.\n\nSource: x"


def test_quote_verification_rules():
    # substring after normalisation (case, emphasis, blockquote marker, whitespace, quotes)
    assert verify_quote(CHUNK, '"acmelake supports single   sign-on through SAML 2.0"')
    # not a substring
    assert not verify_quote(CHUNK, "AcmeLake supports Kerberos authentication for all users")
    # minimum length 20 characters
    assert not verify_quote(CHUNK, "SAML 2.0")
    assert verify_quote(CHUNK, "through SAML 2.0 and OpenID")


def test_normalize_unifies_dashes_and_zero_width():
    assert normalize("on​-premises – cloud") == normalize("on-premises - cloud")


def test_contains_term_is_word_bounded():
    assert contains_term("We hold SOC 2 Type II", "soc 2")
    assert not contains_term("ISO 270011", "ISO 27001")
