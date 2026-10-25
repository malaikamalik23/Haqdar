"""Module K7: Evaluation (owner: Malaika Khan).

Measures, per language (Urdu / Roman Urdu / English):
  - retrieval hit rate@4: an expected step is in the top-4 search results
  - answer accuracy:       Haqdar answered (no abstain) AND an expected step is in the answer
  - citation accuracy:     every answered step cites a source that exists in its pack
  - correct abstention:    out-of-scope questions are refused
  - false abstention:      answerable questions that were wrongly refused
It also sweeps abstention thresholds and reports mean confidence for right vs wrong answers.

Run from the repo root:
    python eval/run_eval.py             (real model)
    python eval/run_eval.py --fake      (fast smoke test, no model)
Writes eval/results.md and eval/results.json.
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from ai import answer, pack_loader, retrieval  # noqa: E402

LANG_NAMES = {"ur": "Urdu", "roman": "Roman Urdu", "en": "English"}
THRESHOLDS = [0.15, 0.20, 0.25, 0.30, 0.35]


class CachedRetriever:
    """Runs each search once so the threshold sweep is fast."""

    def __init__(self, inner):
        self.inner, self.cache = inner, {}

    def search(self, query, k=4):
        if (query, k) not in self.cache:
            self.cache[(query, k)] = self.inner.search(query, k)
        return self.cache[(query, k)]


def evaluate(retriever, packs, threshold):
    data = yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    rows = []
    for item in data["answerable"]:
        top4 = retriever.search(item["q"], 4)
        out = answer.answer_question(item["q"], "en", retriever=retriever, packs=packs, threshold=threshold)
        pack = packs[item["expected_pack"]]
        expected_texts = {s["text_ur"] for s in pack["steps"] if s["id"] in item["expected_steps"]}
        answered_texts = {s["text_ur"] for s in out["steps"]}
        src_ids = {s["id"] for p in packs.values() for s in p["sources"]}
        rows.append({
            "q": item["q"], "lang": item["lang"], "kind": "answerable",
            "retrieval_hit": any(r["pack_id"] == item["expected_pack"] and r["step_id"] in item["expected_steps"] for r in top4),
            "abstained": out["abstained"],
            "correct": (not out["abstained"]) and bool(expected_texts & answered_texts),
            "citations_ok": all(s["source_id"] in src_ids for s in out["steps"]),
            "confidence": out["confidence"],
        })
    for item in data["out_of_scope"]:
        out = answer.answer_question(item["q"], "en", retriever=retriever, packs=packs, threshold=threshold)
        rows.append({
            "q": item["q"], "lang": item["lang"], "kind": "out_of_scope",
            "abstained": out["abstained"], "correct": out["abstained"],
            "confidence": out["confidence"], "note": item.get("note", ""),
        })
    return rows


def pct(n, d):
    return f"{100 * n / d:.0f}% ({n}/{d})" if d else "n/a"


def summarize(rows):
    ans = [r for r in rows if r["kind"] == "answerable"]
    oos = [r for r in rows if r["kind"] == "out_of_scope"]
    answered = [r for r in ans if not r["abstained"]]
    return {
        "retrieval_hit": (sum(r["retrieval_hit"] for r in ans), len(ans)),
        "answer_accuracy": (sum(r["correct"] for r in ans), len(ans)),
        "citation_accuracy": (sum(r["citations_ok"] for r in answered), len(answered)),
        "correct_abstention": (sum(r["correct"] for r in oos), len(oos)),
        "false_abstention": (sum(r["abstained"] for r in ans), len(ans)),
    }


def main():
    fake = "--fake" in sys.argv
    if fake:
        sys.path.insert(0, str(ROOT / "backend" / "ai"))
        from test_retrieval import FakeEmbedder
        base = retrieval.build_retriever(embedder=FakeEmbedder())
    else:
        base = retrieval.build_retriever()
    retriever = CachedRetriever(base)
    packs = {p["id"]: p for p in pack_loader.load_all_packs()}

    # Threshold sweep
    sweep = []
    for t in THRESHOLDS:
        s = summarize(evaluate(retriever, packs, t))
        balanced = (s["answer_accuracy"][0] / s["answer_accuracy"][1] + s["correct_abstention"][0] / s["correct_abstention"][1]) / 2
        sweep.append((t, s, balanced))

    chosen = answer.ABSTAIN_THRESHOLD
    rows = evaluate(retriever, packs, chosen)
    overall = summarize(rows)

    lines = [f"# Haqdar evaluation results{' (FAKE embedder smoke test)' if fake else ''}", "",
             f"Abstention threshold: **{chosen}**  |  questions: {len(rows)}", "",
             "## Overall", "", "| Metric | Result |", "|---|---|"]
    labels = {"retrieval_hit": "Retrieval hit rate@4", "answer_accuracy": "Answer accuracy",
              "citation_accuracy": "Citation accuracy (answered)", "correct_abstention": "Correct abstention (out of scope)",
              "false_abstention": "False abstention (answerable refused)"}
    for k, label in labels.items():
        lines.append(f"| {label} | {pct(*overall[k])} |")

    lines += ["", "## By language", "", "| Language | Retrieval hit@4 | Answer accuracy | Correct abstention |", "|---|---|---|---|"]
    for lang, name in LANG_NAMES.items():
        s = summarize([r for r in rows if r["lang"] == lang])
        lines.append(f"| {name} | {pct(*s['retrieval_hit'])} | {pct(*s['answer_accuracy'])} | {pct(*s['correct_abstention'])} |")

    lines += ["", "## Threshold sweep", "", "| Threshold | Answer accuracy | Correct abstention | Balanced |", "|---|---|---|---|"]
    for t, s, b in sweep:
        lines.append(f"| {t} | {pct(*s['answer_accuracy'])} | {pct(*s['correct_abstention'])} | {b:.2f} |")

    right = [r["confidence"] for r in rows if r["correct"] and r["kind"] == "answerable"]
    oos_conf = [r["confidence"] for r in rows if r["kind"] == "out_of_scope"]
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0  # noqa: E731
    lines += ["", "## Confidence calibration", "",
              f"- Mean confidence, correctly answered questions: {mean(right):.3f}",
              f"- Mean confidence, out-of-scope questions: {mean(oos_conf):.3f}",
              "", "## Every question", "", "| Kind | Lang | Question | Confidence | Abstained | Correct |", "|---|---|---|---|---|---|"]
    for r in rows:
        mark = "✅" if r["correct"] else "❌"
        note = f" _{r['note']}_" if r.get("note") else ""
        lines.append(f"| {r['kind']} | {r['lang']} | {r['q']}{note} | {r['confidence']:.3f} | {r['abstained']} | {mark} |")

    failures = [r for r in rows if not r["correct"]]
    lines += ["", "## Failure cases", ""]
    lines += [f"- [{r['lang']}] {r['q']} (confidence {r['confidence']:.3f}, abstained={r['abstained']})" for r in failures] or ["- none"]

    (ROOT / "eval" / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "eval" / "results.json").write_text(json.dumps({"threshold": chosen, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(lines[:40]))
    print("\nFull report: eval/results.md")


if __name__ == "__main__":
    main()
