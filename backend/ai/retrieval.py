"""Module K2: Retrieval engine.

Finds the pack steps most relevant to a user's question (Urdu, Roman Urdu or English).

How it works (hybrid search):
  1. Semantic score: multilingual sentence embeddings + FAISS cosine search.
     Understands meaning across languages ("بل زیادہ آیا" ~ "bill is too high").
  2. Keyword score: word overlap between the question and the chunk text plus the
     pack's optional `keywords` list. This helps Roman Urdu ("meter tez chal raha"),
     which multilingual models handle poorly.
  final score = SEMANTIC_WEIGHT * semantic + KEYWORD_WEIGHT * keyword   (0..1)
  3. Scope guard: a pack can list `exclude_keywords` (e.g. "gas", "sui" for the electricity
     pack). If the question contains one, that pack's chunks are skipped, so a gas-bill
     question is not answered with electricity steps.

Public contract (docs/api.md):
  search(query: str, k: int = 4) -> list of {pack_id, step_id, source_id, text_ur, score}
"""

from __future__ import annotations

import os
import re

import numpy as np

from . import pack_loader

DEFAULT_MODEL = os.getenv(
    "HAQDAR_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3
CANDIDATES = 20  # how many chunks FAISS returns before re-ranking

# Very common words that carry no meaning for matching (English, Roman Urdu, Urdu).
STOPWORDS = {
    "the", "a", "an", "is", "are", "my", "i", "to", "of", "and", "or", "in", "on", "for",
    "what", "how", "do", "does", "can", "it", "me", "with",
    "mera", "meri", "mere", "ka", "ki", "ke", "ko", "se", "hai", "hain", "ho", "kya",
    "kaise", "kese", "aur", "ya", "main", "mein", "me", "par", "pe", "to", "bhi", "raha", "rahi",
    "کا", "کی", "کے", "کو", "سے", "ہے", "ہیں", "کیا", "اور", "میں", "پر", "بھی", "میرا", "میری",
}

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> set[str]:
    """Lowercase word tokens without stopwords. Works for Urdu script and Latin."""
    return {t for t in _TOKEN_RE.findall(str(text).lower()) if t not in STOPWORDS and len(t) > 1}


def keyword_score(query_tokens: set[str], chunk_tokens: set[str]) -> float:
    """Fraction of the question's words that appear in the chunk (0..1)."""
    if not query_tokens:
        return 0.0
    return len(query_tokens & chunk_tokens) / len(query_tokens)


class SentenceTransformerEmbedder:
    """Wraps sentence-transformers. Loaded lazily so tests can run without the model."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        from sentence_transformers import SentenceTransformer  # heavy import, only when needed

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return np.asarray(vecs, dtype="float32")


def _chunk_index_text(chunk: dict) -> str:
    """Text that represents a chunk for semantic search."""
    return " ".join([chunk["title_ur"], chunk["text_ur"], chunk["text_en"]])


class Retriever:
    def __init__(self, chunks: list[dict], embedder):
        import faiss

        self.chunks = chunks
        self.embedder = embedder
        self.chunk_tokens = [
            tokenize(" ".join([_chunk_index_text(c), *c.get("keywords", []), *c.get("step_keywords", [])]))
            for c in chunks
        ]
        self.chunk_excludes = [tokenize(" ".join(c.get("exclude_keywords", []))) for c in chunks]
        vecs = embedder.encode([_chunk_index_text(c) for c in chunks])
        vecs = _normalize(vecs)
        self.index = faiss.IndexFlatIP(vecs.shape[1])  # inner product on unit vectors = cosine
        self.index.add(vecs)

    def search(self, query: str, k: int = 4) -> list[dict]:
        query = (query or "").strip()
        if not query or not self.chunks:
            return []
        qvec = _normalize(self.embedder.encode([query]))
        n = min(CANDIDATES, len(self.chunks))
        sims, ids = self.index.search(qvec, n)

        q_tokens = tokenize(query)
        results = []
        for sim, idx in zip(sims[0], ids[0]):
            if idx < 0 or (self.chunk_excludes[idx] & q_tokens):
                continue
            semantic = max(0.0, float(sim))  # cosine can be negative; clamp to 0
            kw = keyword_score(q_tokens, self.chunk_tokens[idx])
            score = SEMANTIC_WEIGHT * semantic + KEYWORD_WEIGHT * kw
            c = self.chunks[idx]
            results.append({
                "pack_id": c["pack_id"],
                "step_id": c["step_id"],
                "source_id": c["source_id"],
                "text_ur": c["text_ur"],
                "score": round(score, 4),
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]


def _normalize(vecs: np.ndarray) -> np.ndarray:
    vecs = np.asarray(vecs, dtype="float32")
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def build_retriever(packs_dir=pack_loader.PACKS_DIR, embedder=None) -> Retriever:
    """Load all packs, attach each pack's keywords to its chunks, and build the index."""
    chunks = []
    for pack in pack_loader.load_all_packs(packs_dir):
        keywords = [str(k) for k in pack.get("keywords", [])]
        excludes = [str(k) for k in pack.get("exclude_keywords", [])]
        for chunk in pack_loader.pack_to_chunks(pack):
            chunk["keywords"] = keywords
            chunk["exclude_keywords"] = excludes
            chunks.append(chunk)
    return Retriever(chunks, embedder or SentenceTransformerEmbedder())


_default_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """Build the retriever once and reuse it (model load takes a few seconds)."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = build_retriever()
    return _default_retriever


def search(query: str, k: int = 4) -> list[dict]:
    """Contract function: top-k pack steps for the query, best first."""
    return get_retriever().search(query, k)


if __name__ == "__main__":
    # Manual try-out:  cd backend; python -m ai.retrieval "meter tez chal raha hai"
    import sys

    q = " ".join(sys.argv[1:]) or "میرا بل بہت زیادہ آیا ہے"
    print(f"Query: {q}\n")
    for r in search(q, k=4):
        print(f"{r['score']:.3f}  {r['pack_id']}/{r['step_id']}  ({r['source_id']})")
        print(f"       {r['text_ur']}\n")
