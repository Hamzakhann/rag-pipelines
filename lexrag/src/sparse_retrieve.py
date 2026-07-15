"""Sparse retrieval with BM25 — matches exact terms, not meaning."""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import re
import sys
from pathlib import Path
from rank_bm25 import BM25Okapi
from loader import load_file
from chunkers import chunk_structure

_bm25 = None
_chunks = None
_meta = None

def tokenize(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric. Simple and effective."""
    return re.findall(r"[a-z0-9]+", text.lower())

def build_corpus():
    """Chunk every contract the SAME way the dense index did."""
    global _bm25, _chunks, _meta
    if _bm25 is not None:
        return
    chunks, meta = [], []
    for f in sorted(Path("data/raw").glob("*.txt")):
        text = load_file(f)
        for i, ch in enumerate(chunk_structure(text)):
            chunks.append(ch)
            meta.append({"contract": f.name, "chunk_index": i})
    _chunks, _meta = chunks, meta
    _bm25 = BM25Okapi([tokenize(c) for c in chunks])

def sparse_retrieve(question: str, k: int = 4):
    build_corpus()
    scores = _bm25.get_scores(tokenize(question))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [{"text": _chunks[i], "contract": _meta[i]["contract"],
             "chunk_index": _meta[i]["chunk_index"],
             "score": round(float(scores[i]), 3)} for i in ranked]

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Nelnet joint filing agreement date"
    print(f"BM25 QUERY: {q}\n" + "=" * 60)
    for i, r in enumerate(sparse_retrieve(q, k=4), 1):
        print(f"\n[{i}] {r['contract']}  (BM25 score {r['score']})")
        print("    " + r["text"][:250].replace("\n", "\n    "))
