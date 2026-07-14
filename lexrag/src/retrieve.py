"""Stage 4: RETRIEVE. Turn a question into its k nearest chunks."""
import sys
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DB_PATH = "data/processed/chroma"
COLLECTION = "contracts"

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def retrieve(question: str, k: int = 4, where: dict | None = None):
    """Return top-k chunks nearest to the question in meaning-space."""
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION)
    q_emb = get_model().encode([question]).tolist()
    results = collection.query(
        query_embeddings=q_emb,
        n_results=k,
        where=where,  # optional metadata filter
    )
    out = []
    for doc, meta, dist in zip(results["documents"][0],
                               results["metadatas"][0],
                               results["distances"][0]):
        out.append({"text": doc, "contract": meta["contract"],
                    "distance": round(dist, 3)})
    return out

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "What is the governing law?"
    print(f"QUERY: {q}\n" + "=" * 60)
    for i, r in enumerate(retrieve(q, k=4), 1):
        print(f"\n[{i}] {r['contract']}  (distance {r['distance']})")
        print("    " + r["text"][:350].replace("\n", "\n    "))
