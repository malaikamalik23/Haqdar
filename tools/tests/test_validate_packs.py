import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate_packs as vp  # noqa: E402

DOMAINS = ["fbr.gov.pk", "nepra.org.pk"]

GOOD = {
    "id": "fbr-notice",
    "title_ur": "ایف بی آر کا نوٹس",
    "title_en": "An FBR notice",
    "office": "FBR Taxpayer Facilitation Centre",
    "documents_needed": ["CNIC copy"],
    "steps": [
        {"id": "s1", "text_ur": "نوٹس غور سے پڑھیں۔", "text_en": "Read the notice carefully.", "source_id": "src1"},
        {"id": "s2", "text_ur": "جواب جمع کرائیں۔", "text_en": "Submit your reply.", "source_id": "src1"},
    ],
    "sources": [{"id": "src1", "url": "https://www.fbr.gov.pk/guide", "quote": "A short exact excerpt."}],
}


def check(**changes):
    data = copy.deepcopy(GOOD)
    data.update(changes)
    return vp.validate_pack(data, DOMAINS, "fbr-notice.yaml")


def test_a_correct_pack_is_valid():
    errors, warnings = check()
    assert errors == [] and warnings == []


def test_step_citing_an_unknown_source_is_rejected():
    steps = copy.deepcopy(GOOD["steps"])
    steps[0]["source_id"] = "nope"
    errors, _ = check(steps=steps)
    assert any("not listed under sources" in e for e in errors)


def test_http_links_are_rejected():
    errors, _ = check(sources=[{**GOOD["sources"][0], "url": "http://www.fbr.gov.pk/guide"}])
    assert any("https" in e for e in errors)


def test_unofficial_and_lookalike_domains_are_rejected():
    for url in ("https://example.com/x", "https://fbr.gov.pk.evil.com/x", "https://evilfbr.gov.pk/x"):
        errors, _ = check(sources=[{**GOOD["sources"][0], "url": url}])
        assert any("official_domains" in e for e in errors), url


def test_official_subdomains_are_accepted():
    errors, _ = check(sources=[{**GOOD["sources"][0], "url": "https://iris.fbr.gov.pk/login"}])
    assert errors == []


def test_long_quotes_are_rejected():
    errors, _ = check(sources=[{**GOOD["sources"][0], "quote": "x" * 301}])
    assert any("quote" in e for e in errors)


def test_missing_text_in_either_language_is_rejected():
    steps = copy.deepcopy(GOOD["steps"])
    steps[1]["text_en"] = ""
    errors, _ = check(steps=steps)
    assert any("text_en" in e for e in errors)


def test_duplicate_ids_are_rejected():
    steps = copy.deepcopy(GOOD["steps"])
    steps[1]["id"] = "s1"
    assert any("duplicate step id" in e for e in check(steps=steps)[0])
    sources = [GOOD["sources"][0], GOOD["sources"][0]]
    assert any("duplicate source id" in e for e in check(sources=sources)[0])


def test_id_must_match_the_file_name_and_be_a_slug():
    errors, _ = check(id="other-name")
    assert any("must match the file name" in e for e in errors)
    errors, _ = check(id="Bad Name")
    assert any("lowercase" in e for e in errors)

def test_underscores_are_allowed_in_ids():
    errors, _ = vp.validate_pack({**GOOD, "id": "fbr_notice"}, DOMAINS, "fbr_notice.yaml")
    assert errors == []

def test_office_and_titles_are_required():
    errors, _ = check(office="", title_en=" ")
    assert any("office" in e for e in errors) and any("title_en" in e for e in errors)


def test_unused_source_is_only_a_warning():
    extra = GOOD["sources"] + [{"id": "src2", "url": "https://www.fbr.gov.pk/b", "quote": "Another excerpt."}]
    errors, warnings = check(sources=extra)
    assert errors == [] and any("never cited" in w for w in warnings)


def test_non_mapping_file_is_rejected():
    assert vp.validate_pack(["not", "a", "pack"], DOMAINS)[0]


def test_main_passes_with_no_packs_and_fails_on_a_bad_pack(tmp_path):
    assert vp.main(["x", str(tmp_path)]) == 0
    (tmp_path / "broken.yaml").write_text("id: broken\n", encoding="utf-8")
    assert vp.main(["x", str(tmp_path)]) == 1