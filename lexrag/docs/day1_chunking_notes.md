# Day 1 — Chunking Inspection Notes

## Which strategy kept clauses intact?
Based on the visual evaluation, the STRUCTURE strategy clearly won because it successfully isolated target clauses cleanly into their own standalone chunks without pulling in unrelated neighboring text. For instance, when searching for 'indemnif', the structure-aware chunker produced a highly concise, 77-token chunk containing exclusively Section 14, whereas the FIXED and RECURSIVE chunkers pulled in unnecessary text from sections 13, 15, and 16. This layout-driven separation guarantees that the downstream LLM receives zero trailing noise or truncated sentences from adjacent contract clauses.

## Surprises
The 'governing law' search returning zero hits across all strategies was a sharp reminder that raw keyword search fails if a contract uses alternative terminology like 'Choice of Law' or 'Applicable Law'. Additionally, searching for 'confidential' highlighted how prominent header text (like 'CONFIDENTIAL TREATMENT REQUESTED' on the cover page) can systematically hijack the first chunk hit across all strategies, delaying retrieval of actual confidentiality operational clauses.