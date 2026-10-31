"""Calibrate RETRIEVAL_MIN_SCORE and RESOLVED_REUSE_MIN_SCORE (Gate G2).

Official: embeds each question in backend/tests/fixtures/retrieval_eval.yaml, searches the official collection (top 6)
and, for thresholds 0.30..0.80, reports recall of the expected item among hits >= threshold, and the false-accept rate
(share of unanswerable questions that still get at least one hit >= threshold).
Resolved: compares query embeddings of paraphrases ("same") and non-matching questions ("different") against
document embeddings of synthetic stored question+answer texts.
"""

import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml

from app.services.embeddings.embedder import cosine, get_embedder
from app.services.vector.qdrant_store import get_store

EVAL = Path(__file__).resolve().parents[1] / "backend" / "tests" / "fixtures" / "retrieval_eval.yaml"
THRESHOLDS = [round(0.30 + 0.05 * i, 2) for i in range(11)]


def main() -> int:
    data = yaml.safe_load(EVAL.read_text())
    store, emb = get_store(), get_embedder()
    ans = [(a["q"], set(a["expected"]), store.search("OFFICIAL", emb.embed_query(a["q"]), 6)) for a in data["answerable"]]
    una = [(q, store.search("OFFICIAL", emb.embed_query(q), 6)) for q in data["unanswerable"]]
    print(f"Official retrieval: {len(ans)} answerable, {len(una)} unanswerable questions (top 6)\n")
    print("| threshold | recall@6 | false-accept rate |")
    print("|---|---|---|")
    rows = []
    for t in THRESHOLDS:
        recall = sum(1 for _, exp, hits in ans if any(h.payload["knowledge_id"] in exp and h.score >= t for h in hits)) / len(ans)
        far = sum(1 for _, hits in una if any(h.score >= t for h in hits)) / len(una)
        rows.append((t, recall, far))
        print(f"| {t:.2f} | {recall:.0%} | {far:.0%} |")
    ok = [r for r in rows if r[2] <= 0.10 and r[1] >= 0.90]
    if ok:
        best = ok[0]
        print(f"\nRecommended RETRIEVAL_MIN_SCORE={best[0]:.2f} (lowest threshold with false-accept <= 10% and recall >= 90%).")
    else:
        best = max(rows, key=lambda r: (r[1] >= 0.90, r[1] - r[2], r[0]))
        print(
            f"\nNo threshold reaches recall >= 90% with false-accept <= 10%. Best trade-off: {best[0]:.2f} "
            f"(recall {best[1]:.0%}, false-accept {best[2]:.0%})."
        )
    misses = [
        (q, sorted(exp), [(h.payload["knowledge_id"], round(h.score, 3)) for h in hits[:2]])
        for q, exp, hits in ans
        if not any(h.payload["knowledge_id"] in exp and h.score >= best[0] for h in hits)
    ]
    if misses:
        print("Misses at that threshold:")
        for q, exp, top in misses:
            print(f"  - {q}  expected {exp}  top {top}")
    print("Top official score per unanswerable question:")
    for q, hits in una:
        print(f"  {hits[0].score if hits else 0:.3f}  {q}")

    # ---- resolved reuse threshold ----
    same, diff = [], []
    for p in data["resolved_pairs"]:
        doc = emb.embed_documents([f"{p['stored']}\n{p['answer']}"])[0]
        same += [cosine(emb.embed_query(q), doc) for q in p["same"]]
        diff += [cosine(emb.embed_query(q), doc) for q in p["different"]]
    print(
        f"\nResolved reuse: paraphrase scores min {min(same):.3f} / mean {sum(same) / len(same):.3f}; non-matching max {max(diff):.3f} / mean {sum(diff) / len(diff):.3f}"
    )
    for t in [round(0.60 + 0.025 * i, 3) for i in range(13)]:
        print(
            f"  t={t:.3f}: paraphrases reused {sum(s >= t for s in same)}/{len(same)}, non-matching reused {sum(d >= t for d in diff)}/{len(diff)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
