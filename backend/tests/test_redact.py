from security.redact import redact


def test_redacts_identifiers():
    t = "CNIC 35202-1234567-1, phone 0300-1234567, mail a@b.com, PK36SCBL0000001123456702"
    out, m = redact(t)
    for secret in ["35202-1234567-1", "0300-1234567", "a@b.com", "PK36SCBL0000001123456702"]:
        assert secret not in out
    assert len(m) == 4


def test_keeps_deadlines_and_amounts():
    out, _ = redact("Pay Rs 5000 by 30 November 2026")
    assert "5000" in out and "30 November 2026" in out


def test_redacts_labelled_reference_numbers_only():
    out, _ = redact("Consumer No: 12345678901234, Reference No 4521-A9, amount Rs 5000")
    assert "12345678901234" not in out
    assert "4521-A9" not in out
    assert "5000" in out


def test_label_without_digits_is_kept():
    out, _ = redact("Account holder will be notified")
    assert out == "Account holder will be notified"


def test_same_value_gets_same_placeholder():
    out, m = redact("Call 0300-1234567 or again 0300-1234567")
    assert out.count("[PHONE_1]") == 2
    assert len(m) == 1


def test_phone_with_country_code():
    out, _ = redact("WhatsApp +92 300 1234567 please")
    assert "1234567" not in out