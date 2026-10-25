"""Tests for Module K1 (pack loader). Run with:  pytest backend/ai -v"""

import copy

import pytest

from backend.ai import pack_loader as pl


def good_pack():
    return {
        "id": "sample_pack",
        "title_ur": "نمونہ",
        "title_en": "Sample",
        "office": "Sample office",
        "documents_needed": ["CNIC copy"],
        "steps": [
            {"id": "step_1", "text_ur": "پہلا قدم", "text_en": "First step", "source_id": "src_1"},
            {"id": "step_2", "text_ur": "دوسرا قدم", "text_en": "Second step", "source_id": "src_1"},
        ],
        "sources": [
            {"id": "src_1", "url": "https://nepra.org.pk/some-page", "quote": "Exact excerpt."},
        ],
    }


# ---------- validation ----------

def test_good_pack_has_no_errors():
    assert pl.validate_pack(good_pack()) == []


def test_missing_field_is_reported():
    pack = good_pack()
    del pack["office"]
    assert any("office" in e for e in pl.validate_pack(pack))


def test_step_with_unknown_source_is_reported():
    pack = good_pack()
    pack["steps"][0]["source_id"] = "src_99"
    assert any("unknown source 'src_99'" in e for e in pl.validate_pack(pack))


def test_todo_is_reported():
    pack = good_pack()
    pack["steps"][1]["text_ur"] = "TODO"
    assert any("TODO" in e for e in pl.validate_pack(pack))


def test_duplicate_step_id_is_reported():
    pack = good_pack()
    pack["steps"][1]["id"] = "step_1"
    assert any("duplicate step id" in e for e in pl.validate_pack(pack))


@pytest.mark.parametrize("url", [
    "https://nepra.org.pk/x",
    "https://www.fbr.gov.pk/x",
    "https://nadra.gov.pk/x",
])
def test_official_urls_allowed(url):
    assert pl.is_allowed_url(url)


@pytest.mark.parametrize("url", [
    "http://nepra.org.pk/x",            # not https
    "https://fakenepra.org.pk/x",       # look-alike domain
    "https://nepra.org.pk.evil.com/x",  # domain trick
    "https://example.com/x",
    "not a url",
])
def test_unofficial_urls_rejected(url):
    assert not pl.is_allowed_url(url)


def test_bad_url_in_pack_is_reported():
    pack = good_pack()
    pack["sources"][0]["url"] = "https://example.com/page"
    assert any("not an allowed official" in e for e in pl.validate_pack(pack))


# ---------- chunking ----------

def test_chunks_carry_ids():
    chunks = pl.pack_to_chunks(good_pack())
    assert len(chunks) == 2
    assert chunks[0]["pack_id"] == "sample_pack"
    assert chunks[0]["step_id"] == "step_1"
    assert chunks[0]["source_id"] == "src_1"
    assert chunks[0]["text_ur"] == "پہلا قدم"


def test_load_pack_from_file(tmp_path):
    import yaml
    f = tmp_path / "p.yaml"
    f.write_text(yaml.safe_dump(good_pack(), allow_unicode=True), encoding="utf-8")
    assert pl.load_pack(f)["id"] == "sample_pack"


def test_load_invalid_pack_raises(tmp_path):
    import yaml
    bad = copy.deepcopy(good_pack())
    bad["steps"][0]["source_id"] = "nope"
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.safe_dump(bad, allow_unicode=True), encoding="utf-8")
    with pytest.raises(pl.PackError):
        pl.load_pack(f)


# ---------- the real packs in packs/ ----------

def _real_pack_files():
    return sorted(list(pl.PACKS_DIR.glob("*.yaml")) + list(pl.PACKS_DIR.glob("*.yml")))


@pytest.mark.parametrize("path", _real_pack_files(), ids=lambda p: p.name)
def test_real_pack_is_valid(path):
    """Every pack in packs/ must be complete and cite only official sources."""
    pl.load_pack(path)  # raises PackError listing every problem
