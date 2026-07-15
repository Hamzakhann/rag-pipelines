# Create and activate the virtual environment
python3 -m venv .venv

### Activate it:
###   macOS/Linux/WSL:
source .venv/bin/activate


Raw documents
        │
        ▼
   ① LOAD        ← parse PDF/HTML/text into clean plain text
        │
        ▼
   ② CHUNK       ← split text into retrievable units   ★ TODAY
        │
        ▼
   ③ EMBED       ← turn each chunk into a vector        (Day 2)
        │
        ▼
   ④ RETRIEVE    ← find top-k chunks for a query        (Day 3)
        │
        ▼
   ⑤ GENERATE    ← LLM answers over retrieved chunks
        │
        ▼
      Answer


# The 5 Chunking Strategies

| **Strategy** | **How it splits** | **Best for** | **Cost / Trade-off** |
|---------------|-------------------|--------------|----------------------|
| **Fixed-size** | Splits every **N tokens**, ignoring meaning | Uniform text, fast processing | May cut sentences or ideas in half |
| **Recursive** | Splits by **paragraph → sentence → word**, in order | General prose (good default) | Low cost |
| **Semantic** | Embeds sentences and splits where the **meaning changes** | High-quality retrieval | Slow; requires embedding computation |
| **Parent-child** | Embeds **small chunks** but returns the **larger parent chunk** | High precision with sufficient context | More storage and implementation complexity |
| **Structure-aware** | Splits using the document's own **headings, sections, or clauses** | Contracts, source code, manuals | Requires well-structured/parseable documents |


**3 FAILURE MODES**

| **Failure Mode**      | **What Happens?**                                                                              | **How to Prevent It**                                                    |
| --------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **1. Severed Clause** | A sentence or idea is split into two chunks, so the AI retrieves only half of the information. | Split at natural boundaries (paragraphs/sections) and use chunk overlap. |
| **2. Diluted Chunk**  | A chunk is too large, so the important information is buried among lots of unrelated text.     | Keep chunks reasonably small.                                            |
| **3. Orphan Chunk**   | A chunk refers to something explained in another chunk, so by itself it doesn't make sense.    | Use overlap or parent-child chunking to keep related context together.   |

Easy way to remember
--------------------
✂️ Severed Clause = Information is cut in half.
🌊 Diluted Chunk = Important information gets lost in too much text.
👤 Orphan Chunk = A chunk needs context from another chunk to make sense.


Before I embed, three things must be true:

- My text is clean (LOAD done right)
- My chunks hold answers intact (CHUNK + INSPECT)
- I have some way to grade retrieval later (a golden set, however small)



### Rules for a good golden question:

- It must have a real answer somewhere in your corpus (no unanswerable questions yet).
- The ground_truth_passage is the actual text that answers it — copy it verbatim from the contract.
- Cover variety: exact-term queries ("Section 8.2"), paraphrase queries ("can they cancel early?"), and multi-part queries ("all conditions for termination").




"What is the governing law?"
          │
          ▼
   [embedding model]
          │
          ▼
   [0.021, -0.44, 0.87, ... ]   ← 384 numbers = coordinates on the meaning map


How do you measure "closeness" on the map? → Cosine similarity
You've got two locations (two lists of numbers). How do you measure how close they are? The standard tool is cosine similarity.
Plain English version: it gives you a score between -1 and 1.

- 1.0 = identical meaning (same direction on the map)
- ~0 = unrelated
- -1 = opposite meaning



### 1. Sparse Retrieval (Keyword Search)
* **What it is:** Exact word matching.
* **Easy Analogy:** Using **`Ctrl + F`**.
* **The Good:** Finds specific codes, numbers, or exact names perfectly (e.g., *"Section 8.2"*, *"Tom Watson"*).
* **The Bad:** Blind to meaning. If you search *"governing law"*, it completely misses the clause if the text says *"applicable law"*.

### 2. Dense Retrieval (Embedding Search)
* **What it is:** Meaning and concept matching.
* **Easy Analogy:** A **smart assistant** who gets your drift.
* **The Good:** Finds synonyms and related ideas. If you search *"governing law"*, it successfully surfaces *"choice of law"* or *"jurisdiction"*.
* **The Bad:** Can be too "fuzzy" or vague, occasionally missing the exact phrase you typed.

---

### 💡 Summary Trick
* **Sparse** = Matches the **letters**.
* **Dense** = Matches the **meaning**.


### What a Vector Database Does (e.g., Chroma)
It acts like a specialized warehouse for text and meaning, handling three main jobs locally with zero setup:

* **Job 1: Stores Embeddings** – It keeps track of the mathematical vectors that represent your chunk meanings.
* **Job 2: Finds Neighbors Fast (ANN)** – It uses **Approximate Nearest Neighbor (ANN)** indexing to find related chunks instantly.
* **Job 3: Stores Metadata** – It holds extra tags alongside the text (e.g., *which contract*, *which section*, *what year*).

---

### 💡 The Big Takeaway on "Approximate"
The word **approximate** matters because it means the database takes smart indexing shortcuts rather than checking every single vector in existence. This makes the search incredibly fast, trading a tiny fraction of mathematical perfection for massive speed.



### MRR vs NDCG vs MAP 

Reciprocal Rank Fusion (RRF)


============================
# 7 Core Retrieval Concepts

Here are the **7 core retrieval concepts** we will break down:

1. Precision@k
2. Recall@k
3. MRR (Mean Reciprocal Rank)
4. nDCG (Normalized Discounted Cumulative Gain)
5. BM25 (Sparse Search)
6. Bi-Encoders vs. Cross-Encoders
7. Two-Stage Retrieval (Hybrid + Re-ranking)

---

# 1. Precision@k

## What it is

Out of the top **k** results you showed the user, how many were actually correct?

## Example

You search an App Store for **"photo editor."**

The system displays the **top 5 results (k = 5).**

- 3 are actual photo editors.
- 2 are mobile games.

**Precision@5 = 3/5 = 60%**

## One-Liner to Memorize

> **Precision is about quality:**  
> *"How much of what you showed me is actually what I wanted?"*

---

# 2. Recall@k

## What it is

Out of **all the correct results** that actually exist in your entire database, how many did you manage to find and show in the top **k**?

## Example

There are exactly **10 photo editors** in the entire App Store database.

Your top 5 results contain **3** of them.

**Recall@5 = 3/10 = 30%**

## One-Liner to Memorize

> **Recall is about coverage:**  
> *"Out of all the good stuff out there, how much did you successfully find?"*

---

# 3. MRR (Mean Reciprocal Rank)

## What it is

A metric that cares only about one thing:

**How deep did the user have to scroll to find the first correct result?**

## Example

You search a Help Center for **"reset password."**

- If the correct article is at **Position 1**:

  ```
  Score = 1/1 = 1
  ```

- If the correct article is at **Position 4**:

  ```
  Score = 1/4 = 0.25
  ```

MRR is simply the **average of these reciprocal scores across many different searches.**

## One-Liner to Memorize

> **MRR is about speed to the first win:**  
> *"Where is the very first right answer?"*

---

# 4. nDCG (Normalized Discounted Cumulative Gain)

## What it is

A metric that checks whether your search results are **perfectly sorted**.

It allows different **degrees of relevance**, such as:

- Highly Relevant
- Moderately Relevant
- Slightly Relevant
- Not Relevant

It heavily penalizes rankings where a highly relevant result appears below a weaker one.

## Example

You search for a **laptop.**

- **Result A:** Exactly the laptop you want (**Highly Relevant**)
- **Result B:** A laptop charger (**Slightly Relevant**)

Ideal ranking:

```
1. Result A
2. Result B
```

Bad ranking:

```
1. Result B
2. Result A
```

The second ranking receives a lower **nDCG** because users must scroll past a weaker result before finding the best one.

## One-Liner to Memorize

> **nDCG is about perfect sorting:**  
> *"Are the absolute best results sitting at the very top of the list?"*

---

# 5. BM25 (Sparse Search)

## What it is

BM25 is a ranking algorithm that scores documents primarily by counting matching query words—but intelligently.

It:

- Ignores very common words.
- Rewards rare words.
- Penalizes documents that are unnecessarily long.

## Example

You search a legal database for:

```
Nelnet tax agreement
```

- **"Tax"** and **"agreement"** appear in thousands of documents, so they contribute less.
- **"Nelnet"** is rare, so it becomes highly important.

Suppose:

- **Document A** contains "Nelnet" 3 times in a short paragraph.
- **Document B** contains "Nelnet" 3 times in a 100-page document.

BM25 ranks **Document A** higher because the keyword is more concentrated.

## One-Liner to Memorize

> **BM25 is a smart word-counter:**  
> *"Reward rare query words, but don't let long, bloated documents cheat."*

---

# 6. Bi-Encoders vs. Cross-Encoders

## What they are

These are two different neural approaches for comparing search queries with documents.

### Bi-Encoder

- Encodes the query into a vector.
- Encodes every document into vectors beforehand.
- Compares vectors using similarity.

**Pros**

- Extremely fast
- Scales to millions of documents

**Cons**

- Query and document never directly interact.
- Can miss subtle contextual meaning.

### Cross-Encoder

The query and document are fed into the model **together**.

The model reads both simultaneously and evaluates how every word interacts with every other word.

**Pros**

- Extremely accurate
- Understands context much better

**Cons**

- Computationally expensive
- Too slow for searching millions of documents directly

## One-Liner to Memorize

> **Bi-Encoders are fast but approximate (vector comparison).**  
> **Cross-Encoders are slow but highly accurate (joint word-by-word comparison).**

---

# 7. Two-Stage Retrieval

## What it is

The standard architecture used in modern search engines.

The idea:

1. Use a **fast retriever** to gather a broad set of candidate documents.
2. Use a **slow but accurate reranker** to sort only those candidates.

## Example

Suppose your database contains **1,000,000 documents.**

### Stage 1 — The Net

Use:

- BM25
- Bi-Encoder

Goal:

- Quickly retrieve the **top 50 candidate documents.**
- Optimize for **Recall (Coverage).**

### Stage 2 — The Scale

Pass only those **50 candidates** into a **Cross-Encoder.**

Goal:

- Produce the final **Top 5** perfectly ranked results.
- Optimize for **Precision and Ranking Quality.**

## One-Liner to Memorize

> **Two-stage retrieval is "wide net, best fish."**  
> Use fast retrieval to catch the best candidates, then use slow reranking to perfectly sort the final results.

---

# Quick Summary Table

| Concept | Focus | Easy Memory |
|----------|-------|-------------|
| **Precision@k** | Quality | How many shown results are correct? |
| **Recall@k** | Coverage | How many of all correct results did we find? |
| **MRR** | First Correct Result | How quickly does the user find the first correct answer? |
| **nDCG** | Ranking Quality | Are the best results ranked at the top? |
| **BM25** | Sparse Retrieval | Smart keyword matching using rare terms and document length. |
| **Bi-Encoder** | Fast Retrieval | Compare query/document vectors. |
| **Cross-Encoder** | Accurate Ranking | Read query and document together. |
| **Two-Stage Retrieval** | Retrieval Pipeline | Fast retrieval → Accurate reranking. |