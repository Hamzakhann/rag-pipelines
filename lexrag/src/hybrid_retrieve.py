"""Hybrid retrieval: fuse dense + sparse rankings with RRF."""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
from retrieve import retrieve as dense_retrieve
from sparse_retrieve import sparse_retrieve

RRF_K = 60  # dampening constant — standard default

def hybrid_retrieve(question: str, k: int = 5, pool: int = 30):
    """Cast a wide net with both retrievers, fuse by RANK (not score)."""
    dense_hits = dense_retrieve(question, k=pool)
    sparse_hits = sparse_retrieve(question, k=pool)

    scores, docs = {}, {}

    def add(hits):
        for rank, h in enumerate(hits, start=1):
            # Key by content so the same chunk from both lists merges
            key = (h["contract"], h["text"][:120])
            scores[key] = scores.get(key, 0) + 1.0 / (RRF_K + rank)
            docs[key] = h

    add(dense_hits)
    add(sparse_hits)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    out = []
    for key, rrf in ranked:
        d = docs[key]
        out.append({"text": d["text"], "contract": d["contract"],
                    "rrf_score": round(rrf, 5)})
    return out

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is the governing law?"
    print(f"HYBRID QUERY: {q}\n" + "=" * 60)
    for i, r in enumerate(hybrid_retrieve(q, k=5), 1):
        print(f"\n[{i}] {r['contract']}  (RRF {r['rrf_score']})")
        print("    " + r["text"][:250].replace("\n", "\n    "))
