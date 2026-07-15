"""Cross-encoder re-ranking: read (query, chunk) TOGETHER for true relevance."""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
from sentence_transformers import CrossEncoder
from hybrid_retrieve import hybrid_retrieve

# Small, fast, strong re-ranker trained on relevance judgments
RERANKER = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model = None

def get_reranker():
    global _model
    if _model is None:
        _model = CrossEncoder(RERANKER)
    return _model

def rerank(question: str, k: int = 5, pool: int = 30):
    """Wide net (hybrid, `pool`) → best fish (cross-encoder, top-k)."""
    candidates = hybrid_retrieve(question, k=pool, pool=pool)
    pairs = [(question, c["text"]) for c in candidates]
    scores = get_reranker().predict(pairs)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = round(float(s), 3)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:k]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is the governing law?"
    print(f"RE-RANKED QUERY: {q}\n" + "=" * 60)

    # Show BEFORE and AFTER so you can SEE the reordering
    before = hybrid_retrieve(q, k=5, pool=30)
    print("\n--- BEFORE re-ranking (hybrid order) ---")
    for i, r in enumerate(before, 1):
        print(f"[{i}] {r['contract'][:60]}")

    after = rerank(q, k=5, pool=30)
    print("\n--- AFTER re-ranking (cross-encoder order) ---")
    for i, r in enumerate(after, 1):
        print(f"[{i}] {r['contract'][:60]}  (score {r['rerank_score']})")
        print("    " + r["text"][:200].replace("\n", "\n    "))
