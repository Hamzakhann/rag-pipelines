"""Run all golden questions through naive RAG and log results for grading."""
import json
import sys
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import retrieve

golden = json.loads(Path("eval/golden_set.json").read_text())
results = []

for item in golden:
    hits = retrieve(item["question"], k=5)
    retrieved_contracts = [h["contract"] for h in hits]
    # Simple check: did we retrieve the contract holding the ground-truth answer?
    hit = item.get("contract") in retrieved_contracts
    results.append({
        "id": item["id"],
        "question": item["question"],
        "expected_contract": item.get("contract"),
        "retrieved_contracts": retrieved_contracts,
        "hit": hit,
    })

hits = sum(r["hit"] for r in results)
print(f"\nBASELINE: retrieved correct contract in {hits}/{len(results)} questions "
      f"({100*hits//len(results)}%)\n")
for r in results:
    mark = "✅" if r["hit"] else "❌"
    print(f"{mark} Q{r['id']}: {r['question'][:60]}")

Path("eval/baseline_results.json").write_text(json.dumps(results, indent=2))
print("\nSaved → eval/baseline_results.json")
