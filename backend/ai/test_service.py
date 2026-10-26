"""Tests for ai.service (the functions behind the API endpoints)."""

import pytest

from ai import retrieval, service


class FakeEmbedder:
    def encode(self, texts):
        import numpy as np
        out = np.zeros((len(texts), 64), dtype="float32")
        for i, t in enumerate(texts):
            for tok in retrieval.tokenize(t):
                out[i, sum(map(ord, tok)) % 64] += 1.0
        return out


@pytest.fixture(scope="module")
def r():
    return retrieval.build_retriever(embedder=FakeEmbedder())


def test_empty_notice_abstains_without_crashing(r):
    out = service.analyze("", "ur", retriever=r)
    assert out["abstained"] is True and out["fields"]["amount"] == ""


def test_facts_are_returned_separately_from_the_explanation(r):
    out = service.analyze("LESCO bill amount payable Rs 7,250. Due date 25-11-2026. Please pay.", "ur", retriever=r)
    assert "۷,۲۵۰" in out["fields_ur"]["amount_ur"]
    assert "۷,۲۵۰" not in out["explanation_ur"]  # no facts glued onto the answer text


def test_unknown_letter_pack_raises_not_found():
    with pytest.raises(service.NotFound):
        service.letter("nope", {}, "en")
