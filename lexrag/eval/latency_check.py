"""How much time does each layer cost per query?"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys, time
sys.path.insert(0, "src")
from retrieve import retrieve as dense_retrieve
from hybrid_retrieve import hybrid_retrieve
from rerank import rerank

Q = "What are the termination provisions?"
# warm up models so we time retrieval, not model loading
dense_retrieve(Q, k=5); hybrid_retrieve(Q, k=5); rerank(Q, k=5, pool=30)

for name, fn in [("dense", lambda: dense_retrieve(Q, k=5)),
                 ("hybrid", lambda: hybrid_retrieve(Q, k=5)),
                 ("hybrid+rerank", lambda: rerank(Q, k=5, pool=30))]:
    t = time.perf_counter()
    for _ in range(3):
        fn()
    avg = (time.perf_counter() - t) / 3
    print(f"{name:16} {avg*1000:7.1f} ms/query")
