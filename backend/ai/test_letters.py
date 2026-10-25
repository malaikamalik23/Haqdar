"""Tests for Module K6 (letter generator)."""

import logging

import pytest

from ai import letters

FIELDS = {"name": "Ali Khan", "address": "Islamabad", "reference_no": "12 34567 1234567",
          "bill_month": "October 2026", "amount": "18,500", "reason": "Units too high",
          "disco": "IESCO", "subdivision": "G-9"}


@pytest.mark.parametrize("pack_id", list(letters.LETTER_FIELDS))
@pytest.mark.parametrize("lang", ["ur", "en"])
def test_every_pack_has_both_templates(pack_id, lang):
    out = letters.render_letter(pack_id, {}, lang)
    assert len(out) > 100


def test_fields_are_filled():
    out = letters.render_letter("electricity_bill_dispute", FIELDS, "en")
    for value in ("Ali Khan", "12 34567 1234567", "18,500", "IESCO"):
        assert value in out


def test_missing_fields_become_placeholders():
    out = letters.render_letter("electricity_bill_dispute", {"name": "Ali"}, "en")
    assert "[reference_no]" in out and "Ali" in out


def test_date_is_filled_automatically():
    out = letters.render_letter("electricity_bill_dispute", {}, "en")
    assert "[date]" not in out


def test_unknown_fields_ignored():
    out = letters.render_letter("electricity_bill_dispute", {**FIELDS, "evil": "SHOULD-NOT-APPEAR"}, "en")
    assert "SHOULD-NOT-APPEAR" not in out


def test_template_injection_is_neutralised():
    out = letters.render_letter("electricity_bill_dispute", {"name": "{{ 7*7 }} {% for x in y %}"}, "en")
    assert "49" not in out and "{{" not in out and "{%" not in out


def test_control_chars_and_length_limited():
    v = letters.clean_value("a\x00b" + "x" * 2000)
    assert "\x00" not in v and len(v) <= letters.MAX_FIELD_CHARS


def test_unknown_pack_raises():
    with pytest.raises(letters.LetterError):
        letters.render_letter("nope", {}, "en")


def test_bad_lang_falls_back_to_urdu():
    out = letters.render_letter("electricity_bill_dispute", FIELDS, "fr")
    assert "جناب" in out


def test_personal_fields_never_logged(caplog):
    caplog.set_level(logging.DEBUG)
    letters.render_letter("electricity_bill_dispute", FIELDS, "en")
    assert "Ali Khan" not in caplog.text and "12 34567 1234567" not in caplog.text


def test_letter_fields_list():
    assert "reference_no" in letters.letter_fields("electricity_bill_dispute")


def test_urdu_lines_carry_rtl_mark():
    out = letters.render_letter("electricity_bill_dispute", FIELDS, "ur")
    lines = [l for l in out.split("\n") if l.strip()]
    assert all(l.startswith(letters.RLM) for l in lines)


def test_english_has_no_rtl_mark():
    assert letters.RLM not in letters.render_letter("electricity_bill_dispute", FIELDS, "en")


def test_html_is_rtl_for_urdu_and_escapes_input():
    page = letters.letter_html("electricity_bill_dispute", {"name": "<script>alert(1)</script>"}, "ur")
    assert 'dir="rtl"' in page
    assert "<script>alert" not in page and "&lt;script&gt;" in page
