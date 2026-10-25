"""Tests for Module K3 (grounded answers). Uses a fake retriever: no model needed."""

from ai import answer


PACK = {
    "id": "p1",
    "title_ur": "بجلی کا بل",
    "title_en": "Electricity bill",
    "office": "SDO office",
    "documents_needed": ["bill copy"],
    "steps": [
        {"id": "s1", "text_ur": "پہلا", "text_en": "first", "source_id": "a"},
        {"id": "s2", "text_ur": "دوسرا", "text_en": "second", "source_id": "b"},
        {"id": "s3", "text_ur": "تیسرا", "text_en": "third", "source_id": "a"},
    ],
    "sources": [
        {"id": "a", "url": "https://nepra.org.pk/a", "quote": "qa", "title": "A"},
        {"id": "b", "url": "https://nepra.org.pk/b", "quote": "qb"},
    ],
}
PACKS = {"p1": PACK}


class FakeRetriever:
    def __init__(self, results):
        self.results = results

    def search(self, query, k=4):
        return self.results[:k]


def hit(step_id, score, source_id="a", pack_id="p1"):
    return {"pack_id": pack_id, "step_id": step_id, "source_id": source_id, "text_ur": "", "score": score}


def ask(results, lang="ur", question="bill zyada"):
    return answer.answer_question(question, lang, retriever=FakeRetriever(results), packs=PACKS, threshold=0.3)


def test_low_score_abstains():
    out = ask([hit("s1", 0.1)])
    assert out["abstained"] is True
    assert out["steps"] == [] and out["sources"] == []
    assert out["answer_ur"] == answer.ABSTAIN_UR


def test_no_results_abstains():
    assert ask([])["abstained"] is True


def test_empty_question_abstains():
    assert ask([hit("s1", 0.9)], question="  ")["abstained"] is True


def test_unknown_pack_abstains():
    assert ask([hit("s1", 0.9, pack_id="nope")])["abstained"] is True


def test_answer_has_contract_fields():
    out = ask([hit("s1", 0.9)])
    for key in ("answer_ur", "steps", "sources", "confidence", "abstained"):
        assert key in out
    assert out["abstained"] is False


def test_steps_come_in_pack_order():
    out = ask([hit("s3", 0.9), hit("s1", 0.85)])
    assert [s["text_ur"] for s in out["steps"]] == ["پہلا", "تیسرا"]


def test_weak_steps_are_dropped():
    out = ask([hit("s1", 0.9), hit("s2", 0.2, "b")])
    assert [s["source_id"] for s in out["steps"]] == ["a"]


def test_only_cited_sources_returned():
    out = ask([hit("s1", 0.9)])
    assert [s["id"] for s in out["sources"]] == ["a"]
    assert out["sources"][0]["url"] == "https://nepra.org.pk/a"


def test_every_step_cites_a_returned_source():
    out = ask([hit("s1", 0.9), hit("s2", 0.8, "b"), hit("s3", 0.8)])
    returned = {s["id"] for s in out["sources"]}
    assert all(s["source_id"] in returned for s in out["steps"])


def test_english_fields_only_when_asked():
    ur = ask([hit("s1", 0.9)], lang="ur")
    en = ask([hit("s1", 0.9)], lang="en")
    assert "answer_en" not in ur and "text_en" not in ur["steps"][0]
    assert "answer_en" in en and en["steps"][0]["text_en"] == "first"


def test_bad_lang_falls_back_to_urdu():
    out = ask([hit("s1", 0.9)], lang="fr")
    assert "answer_en" not in out


def test_citation_check_drops_invented_step():
    steps = [{"text_ur": "پہلا", "source_id": "a"}, {"text_ur": "جعلی قدم", "source_id": "a"},
             {"text_ur": "دوسرا", "source_id": "zzz"}]
    assert answer.citation_check(steps, PACK) == [{"text_ur": "پہلا", "source_id": "a"}]


def test_long_question_is_truncated_not_crashing():
    out = ask([hit("s1", 0.9)], question="x" * 10_000)
    assert out["abstained"] is False
