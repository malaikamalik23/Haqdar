"""Tests for Module K2 (retrieval).

Fast tests use a tiny fake embedder, so they run without downloading the model.
The real-model test runs only when HAQDAR_SLOW_TESTS=1 is set:
    $env:HAQDAR_SLOW_TESTS=1; pytest backend/ai -v       (PowerShell)
"""

import os

import numpy as np
import pytest

from ai import retrieval


class FakeEmbedder:
    """Bag-of-words hashing embedder: same words -> similar vectors. Deterministic."""

    dim = 64

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype="float32")
        for i, t in enumerate(texts):
            for tok in retrieval.tokenize(t):
                out[i, sum(map(ord, tok)) % self.dim] += 1.0
        return out


def make_chunks():
    base = {"pack_id": "p", "title_ur": "بجلی کا بل", "keywords": []}
    return [
        {**base, "step_id": "s1", "source_id": "a", "text_ur": "بل کی آخری تاریخ", "text_en": "bill due date"},
        {**base, "step_id": "s2", "source_id": "b", "text_ur": "میٹر چیک کروائیں", "text_en": "meter challenge check",
         "keywords": ["meter", "tez"]},
        {**base, "step_id": "s3", "source_id": "c", "text_ur": "نیپرا شکایت", "text_en": "nepra complaint"},
    ]


@pytest.fixture
def retriever():
    return retrieval.Retriever(make_chunks(), FakeEmbedder())


def test_tokenize_removes_stopwords():
    assert retrieval.tokenize("mera meter tez hai") == {"meter", "tez"}


def test_tokenize_urdu():
    assert "بل" in retrieval.tokenize("میرا بل زیادہ ہے")


def test_keyword_score():
    assert retrieval.keyword_score({"meter", "tez"}, {"meter"}) == 0.5
    assert retrieval.keyword_score(set(), {"meter"}) == 0.0


def test_result_has_contract_fields(retriever):
    r = retriever.search("meter check", k=1)[0]
    assert set(r) == {"pack_id", "step_id", "source_id", "text_ur", "score"}


def test_finds_meter_step_from_roman_urdu(retriever):
    assert retriever.search("mera meter tez chal raha hai", k=1)[0]["step_id"] == "s2"


def test_finds_nepra_step(retriever):
    assert retriever.search("nepra complaint", k=1)[0]["step_id"] == "s3"


def test_k_limits_results(retriever):
    assert len(retriever.search("bill", k=2)) == 2


def test_scores_sorted_and_in_range(retriever):
    scores = [r["score"] for r in retriever.search("bill meter nepra", k=3)]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_empty_query_returns_nothing(retriever):
    assert retriever.search("   ") == []


def test_step_keywords_help_matching():
    chunks = make_chunks()
    chunks[0]["step_keywords"] = ["akhri", "tareekh"]
    r = retrieval.Retriever(chunks, FakeEmbedder())
    assert r.search("akhri tareekh", k=1)[0]["step_id"] == "s1"


def test_exclude_keywords_skip_pack():
    chunks = [{**c, "exclude_keywords": ["gas", "sui"]} for c in make_chunks()]
    r = retrieval.Retriever(chunks, FakeEmbedder())
    assert r.search("gas ka bill zyada", k=4) == []
    assert r.search("bill zyada", k=4) != []


def test_build_from_real_packs():
    r = retrieval.build_retriever(embedder=FakeEmbedder())
    assert len(r.chunks) > 0
    assert all("keywords" in c for c in r.chunks)


@pytest.mark.skipif(os.getenv("HAQDAR_SLOW_TESTS") != "1", reason="set HAQDAR_SLOW_TESTS=1 to run with the real model")
@pytest.mark.parametrize("query, expected_step", [
    ("میرا میٹر تیز چل رہا ہے", "step_3"),
    ("meter tez chal raha hai check kaise karwaun", "step_3"),
    ("bill ki last date kya hoti hai", "step_1"),
])
def test_real_model_finds_right_step(query, expected_step):
    top = retrieval.build_retriever().search(query, k=3)
    assert expected_step in [r["step_id"] for r in top]
