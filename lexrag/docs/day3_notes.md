## Latency cost — worth it?
dense           10.1 ms  → 80%
hybrid          10.4 ms  → 90%   (+0.3ms for +10pts — FREE. Always ship.)
hybrid+rerank  194.0 ms  → 100%  (19x slower; 30 cross-encoder passes)

VERDICT for LexRAG: ship re-ranker. LLM call is ~2000ms, so 194ms is ~9%
of real user-perceived latency. Correctness >> 0.2s for a legal tool.

BUT: if this were autocomplete (<50ms budget), I'd ship hybrid only at 90%.
The right pipeline depends on the product, not on what's most sophisticated.

TODO: test pool=10 — might keep 100% at ~70ms.



## My prediction vs actual
Teacher predicted: hybrid fixes Nelnet, reranking adds little.
ACTUAL: hybrid did NOT fix Nelnet (common tokens outvoted the rare one).
        Re-ranking fixed it — the chunk was in the top-30 pool but not top-5.
Lesson: theory predicts, measurement decides.