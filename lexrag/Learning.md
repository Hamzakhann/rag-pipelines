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