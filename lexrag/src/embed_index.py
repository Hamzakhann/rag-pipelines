"""Stage 3: EMBED. Chunk every contract, embed, and store in Chroma."""

import sys
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from loader import load_file
from chunkers import chunk_structure

# A small, fast, high-quality embedding model. 384 dimensions.
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DB_PATH = "data/processed/chroma"
COLLECTION = "contracts"


def build_index():
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    # Persistent client = survives restarts (stored on disk)
    client = chromadb.PersistentClient(path=DB_PATH)
    # Fresh start each build so we never mix old + new chunks
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)

    files = sorted(Path("data/raw").glob("*.txt"))
    if not files:
        print("No contracts in data/raw/. Run download_data.py first.", file=sys.stderr)
        sys.exit(1)

    all_chunks, all_ids, all_meta = [], [], []
    for f in files:
        text = load_file(f)
        chunks = chunk_structure(text)
        for i, ch in enumerate(chunks):
            all_chunks.append(ch)
            all_ids.append(f"{f.stem}__{i}")
            all_meta.append({"contract": f.name, "chunk_index": i})

    print(f"Embedding {len(all_chunks)} chunks from {len(files)} contracts...")
    # Embed in batches — returns the coordinates on the meaning map
    embeddings = model.encode(
        all_chunks, show_progress_bar=True, batch_size=64
    ).tolist()

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_meta,
    )
    print(f"✅ Indexed {collection.count()} chunks into {DB_PATH}/")


if __name__ == "__main__":
    build_index()
