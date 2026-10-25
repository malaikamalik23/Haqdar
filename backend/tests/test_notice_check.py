from security.notice_check import check_notice, extract_links


def label(text="", links=None, score=0.0, sender=""):
    return check_notice(text, links or [], score, sender)["label"]


def test_lookalike_with_official_prefix_is_flagged():
    assert label(links=["https://fbr.gov.pk.evil.com/pay"]) == "suspicious"


def test_official_domain_and_subdomain_pass():
    assert label(links=["https://fbr.gov.pk"]) == "genuine"
    assert label(links=["https://iris.fbr.gov.pk/login"]) == "genuine"


def test_domain_that_only_ends_the_same_way_is_flagged():
    assert label(links=["https://evilfbr.gov.pk"]) == "suspicious"


def test_userinfo_trick_is_flagged():
    assert label(links=["https://fbr.gov.pk@evil.com/pay"]) == "suspicious"


def test_url_shortener_is_flagged():
    assert label(links=["https://bit.ly/abc123"]) == "suspicious"


def test_ip_address_link_is_flagged():
    assert label(links=["http://192.168.1.5/pay"]) == "suspicious"


def test_punycode_link_is_flagged():
    assert label(links=["http://xn--fbr-gov-pk.com"]) == "suspicious"


def test_wallet_payment_request_is_flagged():
    assert label(text="Send payment to our Easypaisa account") == "suspicious"


def test_high_scam_score_is_flagged():
    assert label(text="Please read.", score=0.9) == "suspicious"


def test_no_evidence_is_unclear_not_genuine():
    assert label(text="Please see the attached letter.") == "unclear"


def test_official_link_with_wallet_request_is_still_suspicious():
    assert label(text="Pay via Easypaisa", links=["https://fbr.gov.pk"]) == "suspicious"


def test_spoofed_sender_is_flagged():
    assert label(sender="notice@fbr-gov.pk") == "suspicious"


def test_official_sender_passes():
    assert label(sender="notice@fbr.gov.pk") == "genuine"


def test_links_are_found_in_text_without_trailing_punctuation():
    found = extract_links("Visit https://fbr.gov.pk/pay, or www.nadra.gov.pk.")
    assert found == ["https://fbr.gov.pk/pay", "www.nadra.gov.pk"]


def test_genuine_verdict_never_claims_proof():
    reasons = check_notice("", ["https://fbr.gov.pk"])["reasons"]
    assert "not proof" in reasons[0]