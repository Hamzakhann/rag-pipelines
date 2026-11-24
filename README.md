# RAG Pipelines

Retrieval-augmented generation (RAG) projects built step by step and measured against a golden set. Each project lives in its own folder.

| Project | What it does | Best result |
|---|---|---|
| [`lexrag/`](lexrag/) | Question answering over legal contracts (CUAD dataset) with Claude | **20/20** correct contract retrieved with hybrid search + re-ranking, up from 16/20 for plain vector search |

---

## LexRAG: contract Q&A

Ask questions about a set of real commercial contracts and get answers that cite the contract they came from. The pipeline is built stage by stage, and every change is checked against a 20-question answer key, not judged by eye.

```
LOAD → CHUNK → EMBED → RETRIEVE → (RE-RANK) → GENERATE
```

### Results

Measured on 20 golden questions over 25 contracts, top-5 retrieval. A question counts as a hit when the right contract appears in the top 5.

| Retriever | Hits | Latency per query |
|---|---|---|
| Dense (vector search) | 16 / 20 (80%) | ~10 ms |
| Hybrid (dense + BM25, fused with RRF) | 18 / 20 (90%) | ~10 ms |
| Hybrid + cross-encoder re-ranking | **20 / 20 (100%)** | ~194 ms |

What the numbers showed:

- **Hybrid search is free accuracy.** BM25 adds exact-term matching for about 0.3 ms and fixed 2 more questions.
- **Re-ranking fixed the last two misses.** For one of them, a date in a Nelnet filing, hybrid search did not help: common words outvoted the rare one. The right chunk was in the top 30 but not the top 5, and the cross-encoder moved it up.
- **The re-ranker is worth its cost here.** It adds ~185 ms, but the LLM call takes ~2 s, so it's under 10% of what the user waits. For a sub-50 ms use case like autocomplete, hybrid alone would be the better choice.

### How it works

| Stage | Choice | File |
|---|---|---|
| Load | 25 contracts from [CUAD](https://huggingface.co/datasets/theatticusproject/cuad-qa) (CC-BY 4.0), cleaned | `src/download_data.py`, `src/loader.py` |
| Chunk | Structure-aware: splits on SECTION / ARTICLE / numbered headings, max 600 tokens, recursive fallback. Compared against fixed-size and recursive splitting. | `src/chunkers.py` |
| Embed | `all-MiniLM-L6-v2` (384 dims) into a persistent Chroma store | `src/embed_index.py` |
| Retrieve | Dense (Chroma), sparse (BM25), and hybrid with Reciprocal Rank Fusion (k = 60, pool of 30) | `src/retrieve.py`, `src/sparse_retrieve.py`, `src/hybrid_retrieve.py` |
| Re-rank | `cross-encoder/ms-marco-MiniLM-L-6-v2` over the hybrid pool | `src/rerank.py` |
| Generate | Claude answers only from the retrieved context, cites the contract, and says so when the answer isn't there | `src/rag_answer.py` |
| Evaluate | Golden set, baseline run, retriever comparison, latency check | `eval/` |

### Run it

```bash
cd lexrag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env

python src/download_data.py          # fetch 25 CUAD contracts into data/raw/
python src/embed_index.py            # chunk, embed and index into Chroma
python src/rerank.py "What is the governing law?"      # see retrieval before and after re-ranking
python src/rag_answer.py "What is the governing law?"  # full answer from Claude with citations

python eval/compare_retrievers.py    # dense vs hybrid vs hybrid + re-rank on the golden set
python eval/latency_check.py         # time each retriever
```

### Notes and playbook

- [`docs/playbook.md`](lexrag/docs/playbook.md): a project-agnostic RAG operating manual (pipeline, golden rules, setup, what to try when an answer is wrong).
- [`docs/day1_chunking_notes.md`](lexrag/docs/day1_chunking_notes.md): why structure-aware chunking kept clauses intact.
- [`docs/day3_notes.md`](lexrag/docs/day3_notes.md): hybrid vs re-ranking, latency trade-offs, and where my prediction was wrong.

### Next

- Wire hybrid + re-ranking into the answer step (generation still uses dense retrieval).
- Score answers, not just retrieval: faithfulness and citation accuracy.
- Test a smaller re-rank pool (10) to keep 100% at lower latency.

---

**Stack:** Python · Claude (Anthropic API) · Chroma · sentence-transformers · BM25 · tiktoken · LangChain text splitters

Built by [Hamza Khan](https://github.com/Hamzakhann), senior full-stack and AI engineer. [Portfolio](https://hamzakhann.vercel.app/)
