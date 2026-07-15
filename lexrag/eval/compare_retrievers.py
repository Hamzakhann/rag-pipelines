"""Compare naive dense vs hybrid vs hybrid+rerank on the golden set."""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import retrieve as dense_retrieve
from hybrid_retrieve import hybrid_retrieve
from rerank import rerank

golden = json.loads(Path("eval/golden_set.json").read_text())
K = 5

PIPELINES = {
    "dense (baseline)": lambda q: dense_retrieve(q, k=K),
    "hybrid":           lambda q: hybrid_retrieve(q, k=K),
    "hybrid+rerank":    lambda q: rerank(q, k=K, pool=30),
}

summary = {}
per_q = {name: {} for name in PIPELINES}

for name, fn in PIPELINES.items():
    hits = 0
    for item in golden:
        got = [h["contract"] for h in fn(item["question"])]
        hit = item.get("contract") in got
        per_q[name][item["id"]] = hit
        hits += hit
    summary[name] = hits
    print(f"{name:20} {hits}/{len(golden)}  ({100*hits//len(golden)}%)")

print("\n--- Per-question breakdown ---")
print(f"{'Q':<4}{'dense':<10}{'hybrid':<10}{'hyb+rerank':<12}question")
for item in golden:
    i = item["id"]
    row = "".join("✅  " if per_q[n][i] else "❌  " for n in PIPELINES)
    marks = [("✅" if per_q[n][i] else "❌") for n in PIPELINES]
    print(f"{i:<4}{marks[0]:<10}{marks[1]:<10}{marks[2]:<12}{item['question'][:45]}")

Path("eval/day3_comparison.json").write_text(json.dumps(
    {"summary": summary, "per_question": per_q}, indent=2))
print("\nSaved → eval/day3_comparison.json")
