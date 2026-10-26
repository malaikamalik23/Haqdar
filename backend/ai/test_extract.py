"""Tests for Module K4b (key-field extraction)."""

from ai import extract

BILL_EN = """IESCO - Islamabad Electric Supply Company
Bill Date: 05-11-2026
Amount Payable: Rs 18,500
Due Date: 20-11-2026
Please pay the amount before the due date to avoid a late payment surcharge."""

FBR_EN = """Federal Board of Revenue
Office of the Commissioner Inland Revenue
Dated: 2 October 2026
Notice under section 114(4)
You are required to furnish your return of income for tax year 2025 not later than 30 October 2026."""

ROMAN = "LESCO bill: aap ka bill 7,250 rupay hai. Aakhri tareekh 25-11-2026 tak bill jama karwa dein."

URDU = """آئیسکو
بل کی رقم: 18,500 روپے
آخری تاریخ: 20 نومبر 2026
براہِ کرم آخری تاریخ سے پہلے بل ادا کریں۔"""


def test_english_bill():
    f = extract.extract_fields(BILL_EN)
    assert f["sender"] == "IESCO"
    assert f["date"] == "05-11-2026"
    assert f["deadline"] == "20-11-2026"
    assert f["amount"] == "18,500"
    assert f["demand"].lower().startswith("please pay")


def test_fbr_notice():
    f = extract.extract_fields(FBR_EN)
    assert f["sender"] == "FBR"
    assert f["date"] == "2 October 2026"
    assert f["deadline"] == "30 October 2026"
    assert "furnish" in f["demand"]


def test_roman_urdu():
    f = extract.extract_fields(ROMAN)
    assert f["sender"] == "LESCO"
    assert f["amount"] == "7,250"
    assert f["deadline"] == "25-11-2026"
    assert "jama" in f["demand"]


def test_urdu():
    f = extract.extract_fields(URDU)
    assert f["sender"] == "IESCO"
    assert f["amount"] == "18,500"
    assert f["deadline"] == "20 نومبر 2026"
    assert "ادا" in f["demand"]


def test_contract_shape_and_empty_text():
    f = extract.extract_fields("")
    assert f == {"sender": "", "date": "", "deadline": "", "amount": "", "demand": ""}


def test_unknown_sender_from_label():
    assert extract.find_sender("From: Housing Society Office\nPay dues") == "Housing Society Office"


def test_prefers_payable_amount_over_other_numbers():
    text = "Previous balance Rs 1,000\nUnits 450\nTotal amount payable: Rs 9,800"
    assert extract.find_amount(text) == "9,800"


def test_very_long_text_is_cut():
    assert extract.extract_fields("x" * 100_000)["sender"] == ""


# Real Tesseract output for eval/ocr_samples/notice5_clean.png (Urdu Nastaliq, urd+eng).
# OCR lost the sender and mangled "رقم"/"روپے", and reversed the date (RTL).
REAL_URDU_OCR = "fk رق :18,500 رہ\nآخری :2026-11-20\n“Pb ke fle"


def test_recovers_fields_from_real_damaged_urdu_ocr():
    f = extract.extract_fields(REAL_URDU_OCR)
    assert f["amount"] == "18,500"
    assert f["deadline"] == "20-11-2026"


def test_year_first_date_is_normalised():
    assert extract.normalize_date("2026-11-20") == "20-11-2026"
    assert extract.normalize_date("20-11-2026") == "20-11-2026"


def test_money_shape_does_not_grab_dates_or_plain_numbers():
    assert extract.find_amount("Units 450, date 20-11-2026") == ""


# ---------- Urdu display ----------

def test_urdu_digits():
    assert extract.to_urdu_digits("18,500") == "۱۸,۵۰۰"


def test_numeric_date_to_urdu():
    assert extract.date_ur("20-11-2026") == "۲۰ نومبر ۲۰۲۶"
    assert extract.date_ur("05/01/26") == "۵ جنوری ۲۰۲۶"


def test_english_word_date_to_urdu():
    assert extract.date_ur("30 October 2026") == "۳۰ اکتوبر ۲۰۲۶"
    assert extract.date_ur("November 20, 2026") == "۲۰ نومبر ۲۰۲۶"


def test_bad_date_keeps_text_with_urdu_digits():
    assert extract.date_ur("31-13-2026") == "۳۱-۱۳-۲۰۲۶"


def test_fields_ur_for_english_bill():
    out = {k: v.strip(extract.RLM) for k, v in extract.fields_ur(extract.extract_fields(BILL_EN)).items()}
    assert out == {"sender_ur": "آئیسکو (IESCO)", "date_ur": "۵ نومبر ۲۰۲۶",
                   "deadline_ur": "۲۰ نومبر ۲۰۲۶", "amount_ur": "۱۸,۵۰۰ روپے"}


def test_fields_ur_empty():
    assert extract.fields_ur({}) == {"sender_ur": "", "date_ur": "", "deadline_ur": "", "amount_ur": ""}


def test_urdu_values_are_wrapped_in_rtl_marks():
    out = extract.fields_ur({"deadline": "20-11-2026"})
    assert out["deadline_ur"] == extract.RLM + "۲۰ نومبر ۲۰۲۶" + extract.RLM
    assert out["amount_ur"] == ""  # empty stays empty, no stray marks
