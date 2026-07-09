"""Download a sample of the CUAD legal-contract dataset into data/raw/.
CUAD: Contract Understanding Atticus Dataset (CC-BY 4.0).
https://huggingface.co/datasets/theatticusproject/cuad-qa
"""
import json
from pathlib import Path
from datasets import load_dataset

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

# CUAD-QA gives us contracts as context + expert Q/A annotations.
print("Downloading CUAD-QA (first load caches ~from HuggingFace)...")
ds = load_dataset("theatticusproject/cuad-qa", split="train", trust_remote_code=True)

# Each row: id, title, context (full contract text), question, answers.
# Many questions repeat per contract, so we dedupe by contract title/context.
seen = {}
N_CONTRACTS = 25   # start small and real; scale later

for row in ds:
    title = row["title"]
    if title not in seen and len(seen) < N_CONTRACTS:
        seen[title] = row["context"]

for title, context in seen.items():
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:80].strip()
    (RAW / f"{safe}.txt").write_text(context, encoding="utf-8")

print(f"Wrote {len(seen)} contracts to {RAW}/")

# Also save the raw QA annotations — the seed for our golden set.
qa_rows = []
titles = set(seen.keys())
for row in ds:
    if row["title"] in titles and row["answers"]["text"]:
        qa_rows.append({
            "contract": row["title"],
            "question": row["question"],
            "answer_text": row["answers"]["text"][0][:400],
        })
Path("data/raw/_cuad_qa_annotations.json").write_text(
    json.dumps(qa_rows[:200], indent=2), encoding="utf-8"
)
print(f"Saved {min(len(qa_rows),200)} QA annotations for golden-set seeding.")
