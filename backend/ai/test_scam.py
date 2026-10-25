"""Tests for Module K5 (scam-language score)."""

import pytest

from ai import scam

SCAM_THRESHOLD = 0.7  # the value security.notice_check uses


@pytest.mark.parametrize("text", [
    "URGENT! Your connection will be disconnected today. Pay immediately via Easypaisa or police will arrest you.",
    "fori 5000 rupay jazzcash par bhejein warna aaj bijli kaat di jayegi",
    "فوری طور پر ایزی پیسہ پر رقم بھیجیں ورنہ پولیس کارروائی ہوگی۔",
    "Congratulations you won a prize! Send your OTP and CNIC to claim now.",
])
def test_scam_texts_score_high(text):
    assert scam.score_language(text)["score"] >= SCAM_THRESHOLD


@pytest.mark.parametrize("text", [
    "Your electricity bill is Rs 3,200. The due date is 20 November. Pay at any bank.",
    "agar bill ghalat hai to sub division office mein shikayat karein",
    "آپ کا بل 3200 روپے ہے۔ آخری تاریخ 20 نومبر ہے۔",
])
def test_normal_texts_score_low(text):
    assert scam.score_language(text)["score"] < 0.5


def test_official_style_disconnection_notice_is_not_flagged_alone():
    # Real notices can mention disconnection; one category alone must stay below 0.7.
    text = "Unpaid bills may result in disconnection as per rules. Please pay by the due date at any bank."
    assert scam.score_language(text)["score"] < SCAM_THRESHOLD


def test_signals_explain_the_score():
    out = scam.score_language("Send your OTP immediately")
    joined = " ".join(out["signals"])
    assert "PIN, OTP" in joined and "immediately" in joined.lower()


def test_contract_shape():
    out = scam.score_language("hello")
    assert set(out) == {"score", "signals"}
    assert 0.0 <= out["score"] <= 1.0 and isinstance(out["signals"], list)


def test_empty_text():
    assert scam.score_language("") == {"score": 0.0, "signals": []}


def test_rule_score_combines():
    assert scam.rule_score([]) == 0.0
    one = scam.rule_score(["urgency"])
    two = scam.rule_score(["urgency", "threat"])
    assert 0 < one < two < 1


def test_works_with_notice_check():
    from security.notice_check import check_notice
    text = "fori payment karein warna bijli kaat di jayegi, easypaisa par bhejein"
    verdict = check_notice(text, [], scam.score_language(text)["score"])
    assert verdict["label"] == "suspicious"
