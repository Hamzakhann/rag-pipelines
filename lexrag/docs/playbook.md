# RAG STEPS — My Operating Manual

> A general, project-agnostic playbook. Works for any corpus.
> **Status:** Days 1–3 complete. Days 4–5 to be appended.

---

## THE PIPELINE (never changes)

```
LOAD → CHUNK → EMBED → RETRIEVE → GENERATE
```

**Rule:** When an answer is wrong, name the stage that broke it. ~80% of RAG failures are retrieval failures, not LLM failures. Never blame the model first.

---

## THE 5 GOLDEN RULES

1. **Evaluate, don't vibe.** One lucky query proves nothing. Build the answer key first.
2. **You can't retrieve what isn't there.** Fix chunking before tuning retrieval.
3. **One variable per experiment.** Change two things, learn nothing.
4. **Measure cost, not just accuracy.** The best pipeline depends on the product.
5. **Theory predicts, measurement decides.** My predictions were wrong on real data — twice.

---

## PROJECT SETUP (every time)

```bash
mkdir <project> && cd <project>
mkdir -p data/raw data/processed src eval outputs docs
python3 -m venv .venv && source .venv/bin/activate
git init
```

**Folder contract:**
- `data/raw/` — untouched sources. **Read-only in your mind.**
- `data/processed/` — chunks, vector DB. **Regenerable = disposable.**
- `src/` — pipeline code · `eval/` — golden set + harness · `docs/` — notes & diary

`.gitignore`: `.venv/`, `__pycache__/`, `.env`, `data/raw/`, `data/processed/`, `outputs/`

> If you can't reproduce a result by re-running from `data/raw/`, you have an invisible bug.

**Kill console noise early** (top of every file, **before** other imports):
```python
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```

---

## STEP 1 — LOAD → `src/loader.py`

- Parse source → clean plain text
- Strip boilerplate: page markers, headers/footers, cover-page stamps
- Normalize whitespace
- Errors → **stderr**, skip the file, never crash the batch

**Watch for:** cover-page text (e.g. "CONFIDENTIAL TREATMENT REQUESTED") hijacking retrieval later. Strip it here or tag it in metadata.

---

## STEP 2 — CHUNK → `src/chunkers.py`

Chunk by **tokens**, not characters (the LLM sees tokens).

| Strategy | Use when |
|---|---|
| Fixed-size | Never by default — cuts sentences in half |
| **Recursive** | **Sane default.** Paragraph → sentence → word |
| Structure-aware | Docs with real headers (contracts, code, manuals) — often best |
| Semantic | High quality, high cost. Only if measured need |
| Parent-child | Embed small for matching, return big for context |

**Default hypothesis:** recursive, ~512 tokens, ~15% overlap. A hypothesis to disprove, not a setting to trust. **No universally best chunk size** — it's a function of your documents AND your queries.

### The 3 chunking failure modes
1. **Severed clause** — boundary lands mid-answer → kills **Recall**
2. **Diluted chunk** — answer is 5% of a huge chunk; the embedding becomes a blurry average of many facts, matching nothing sharply → kills **Precision**
3. **Orphan chunk** — references context living in another chunk

**Always have a fallback.** Structure-aware silently produces one giant blob if headers don't match. Short docs are where chunkers break.

---

## STEP 3 — INSPECT (5 min, never skip) → `src/inspect_chunks.py`

Search your chunks for a key term and **read the output with your own eyes.**

1. Is the answer **complete**, or cut off at the boundary?
2. How much of the chunk is **noise**?
3. Which strategy gives the cleanest result?

⚠️ **Inspection can't tell you if retrieval will FIND it.** Keyword search misses synonyms ("governing law" ≠ "Choice of Law"). That's what the golden set is for.

---

## STEP 4 — GOLDEN SET → `eval/golden_set.json`

```json
{
  "id": 1,
  "question": "What is the governing law?",
  "contract": "<source file that holds the answer>",
  "ground_truth_passage": "<the exact text that answers it>"
}
```

**Rules:**
- Start with **15–20**. Rough is fine. Grow it over time.
- Every answer must be **real and verified** — open the doc and confirm. A wrong answer key is worse than no answer key.
- Cover variety: exact-fact (dates/names/IDs), paraphrase, multi-part.
- It's a **living regression test** — when a real user query fails, add it.

> The highest-leverage 45 minutes of any RAG project. Without it you're tweaking knobs and hoping.

---

## STEP 5 — EMBED & INDEX → `src/embed_index.py`

An embedding = **coordinates on a map of meaning.** Similar meaning → nearby points. Cosine similarity measures *direction in meaning-space*, not word overlap.

- Start small/fast (e.g. MiniLM-384d). Bigger ≠ better; costs speed + storage.
- **Attach metadata to every chunk** (source, section, date, type)
- Persist to disk; rebuild fresh each time (never mix old + new chunks)
- Swapping the embedding model **requires full re-indexing** (vectors aren't comparable)

**Metadata = free precision.** Filter *before* you search → smaller haystack, no extra model work.

---

## STEP 6 — RETRIEVE

### Dense vs Sparse — they fail in OPPOSITE places

| | Dense (embeddings) | Sparse (BM25) |
|---|---|---|
| Matches | Meaning | Exact words |
| Synonyms / paraphrase | ✅ Strong | ❌ Blind |
| Rare tokens (names, dates, IDs) | ⚠️ Blurs | ✅ Strong |

Embeddings are a **summary** — compression loses exact detail. That's why they blur dates and proper nouns.

### Hybrid = Dense + Sparse via RRF → `src/hybrid_retrieve.py`

Never add raw scores (different scales). Fuse by **rank**:

```
RRF(chunk) = Σ  1 / (60 + rank_in_that_list)
```

Rank is universal — "3rd place" means the same to any retriever. No calibration needed. Consensus wins: good-in-both beats great-in-one.

### Re-ranking = Cross-Encoder → `src/rerank.py`

- **Bi-encoder** (embeddings): query and chunk encoded **separately** → fast, approximate
- **Cross-encoder**: query and chunk read **together** → accurate, slow (1 model pass per pair)

**The two-stage pattern (memorize):**
```
ALL chunks → hybrid retrieve top-N   (wide net  → RECALL)
          → cross-encoder rerank top-k (best fish → PRECISION + ORDER)
```

If the right chunk isn't in the top-N pool, **re-ranking cannot save you.** You can only reorder what you caught. `pool` is a dial: too small starves the reranker, too big burns time. Latency ≈ linear in pool size.

---

## STEP 7 — GENERATE → `src/rag_answer.py`

- Prompt: *"Answer using ONLY the context below. If not present, say so. Cite sources."*
- Include source name with each chunk so citation is possible
- API keys in `.env`, never hardcoded

⚠️ **The #1 RAG self-deception: the LLM sounds confident even over garbage context.** Always spot-check an answer against the real source.

---

## STEP 8 — MEASURE

Run **all** golden questions through each pipeline variant. Compare.

| Metric | Asks | Raised by |
|---|---|---|
| **Precision@k** | Of k retrieved, how many are useful? | Re-ranking, better chunking |
| **Recall@k** | Of all relevant, how many did we get? | **Hybrid**, query expansion |
| **MRR** | Where's the **first** right answer? | **Re-ranking** |
| **nDCG** | Is the **whole list** perfectly ordered? | **Re-ranking** |
| **Faithfulness** | Is the answer grounded, or invented? | Better prompts |

**Division of labor (memorize):**
> **Hybrid raises Recall. Re-ranking raises MRR / nDCG / Precision.**
> Confusing these is the #1 RAG mistake.

**Also measure latency.** Accuracy without cost is half a decision.

---

## THE DECISION LADDER

Retrieval failing? Stop at the first "yes":

1. Is the right chunk even **in the index, intact**? → fix **chunking/ingestion**
2. In the index but ranked low? → add **hybrid**, then **re-ranking**
3. Query vague / matches poorly? → **query rewriting / expansion**
4. Context right but answer strays? → **fix the prompt**, not the retriever
5. Question spans many linked docs? → **hierarchical / graph RAG**
6. Needs to adapt mid-question? → **guarded agentic loop**
7. Corpus tiny or task reasoning-heavy? → **RAG may be the wrong tool**

---

## DEBUGGING: the two causes of failure

They look **identical** from outside. Diagnose before you fix.

- **Cause A — ranked low.** Chunk IS indexed → tuning fixes it (hybrid, rerank).
- **Cause B — not in index.** Loader/chunker broke → no retrieval trick will help.

**The tell:** if the *same document* fails multiple different questions → suspect B.

**Diagnostic — run BEFORE "fixing" anything:**
```python
# 1. Is the file in data/raw/ at all?
# 2. Loaded text length?
# 3. How many chunks produced?  (0 = broken, 1 giant = dilution)
# 4. Print each chunk preview — sane?
```

> Tuning cannot rescue a document that was never indexed.
> Never debug the retrieval layer before confirming the ingestion layer.

---

## ANTI-PATTERNS

- **Vibe-driven tuning** — judging on one lucky query
- **Re-ranker as band-aid** — reordering can't create chunks that never retrieved
- **Chunk-size cargo cult** — copying 512 without measuring on YOUR docs
- **Technique soup** — adding 3 things at once, learning nothing
- **Blaming the LLM** — 80% of the time the context was wrong
- **Tool collecting** — adding sophistication without a measured win

---

## MEASURED RESULTS — LexRAG (24 contracts, 735 chunks, 20 golden Qs)

| Pipeline | Accuracy | Latency | Verdict |
|---|---|---|---|
| dense | 80% | 10.1 ms | baseline |
| hybrid | 90% | 10.4 ms | **+10 pts for +0.3 ms — free lunch, always ship** |
| hybrid+rerank | 100% | 194 ms | 19× slower, but LLM ≈2000 ms → only ~9% real cost |

**Key insight:** the right pipeline depends on the **product**, not on what's most sophisticated.

| Product | Verdict |
|---|---|
| Legal search (LLM in loop, correctness critical) | **Ship the re-ranker** |
| Autocomplete (<50 ms budget) | **Hybrid only, accept 90%** |
| High-volume API | 19× compute is a real bill — weigh it |
| Batch / overnight | Re-rank everything, big pool |

---

## LESSONS THAT COST ME SOMETHING

1. **Keyword search missed "governing law"** because the contract said "Choice of Law."
   → Embeddings match *meaning*. This is why dense retrieval exists.

2. **Nelnet: 1081 chars → 1 chunk.** Structure-aware found no headers and dumped the whole doc into one blurry chunk. Indexed, but no specific query could match it sharply.
   → **A doc can be fully indexed and still fail. Dilution is real.**

3. **Hybrid did NOT fix Nelnet — re-ranking did.** Theory said BM25's rare-token power would nail "Nelnet." Reality: common tokens (*agreement, joint, date*) **outvoted** the one rare token. The cross-encoder, reading query+chunk together, rescued it.
   → **Theory predicts. Measurement decides. Trust your data over any expert.**

---

## PRE-FLIGHT CHECKLIST

**Before embedding, three things must be true:**
- [ ] Text is clean (LOAD correct)
- [ ] Chunks hold answers **intact** (CHUNK + INSPECT)
- [ ] I have *some* way to grade retrieval later (golden set, however small)

**Before shipping:**
- [ ] Beats the naive baseline **on measured numbers**
- [ ] Every layer earned its place with a measured win
- [ ] Latency fits the product's budget
- [ ] Spot-checked an answer against the real source

---

## DAILY PRACTICES

- **Eval diary** — log metrics per change. 10 lines is enough. Trend them up.
- **Failure review** — take one wrong answer, trace it to a stage.
- **Simplicity check** — "could a simpler pipeline score the same?" Usually: yes.

---

*Days 4–5 (real metrics, faithfulness, advanced techniques, agentic RAG) to be appended.*