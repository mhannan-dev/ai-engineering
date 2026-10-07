# Northstar Knowledge Operations Handbook

> Synthetic retrieval-test document. Northstar and all policies, dates, and figures in this handbook are fictional.

## 1. Document ownership

Every published handbook page has a named team owner, a review date, and a short purpose statement. The Knowledge Operations team owns shared search guidance; the Service Desk owns support procedures; and the Records team owns retention rules. A page without an owner is a draft, not an authoritative answer. Search results should be treated as evidence only when the result identifies its source and current revision. Staff should report an ownerless or contradictory page to the Knowledge Operations queue rather than silently copying it into another document.

## 2. Revision identifiers

Northstar assigns each approved document a revision in the form `DOC-AREA-YYYY-NN`, where `AREA` is a three-letter subject code and `NN` is a sequence number for that year. For example, `DOC-OPS-2026-04` is the fourth Operations revision recorded in 2026. The revision belongs in the document metadata and the first page, not in the filename alone. A new revision supersedes the prior one only after its reviewer approves it. Draft revisions must not be uploaded to the production retrieval collection.

## 3. Review schedule

Operational procedures are reviewed every 90 days, while stable reference glossaries are reviewed every 180 days. The document owner starts the review ten business days before its due date and checks links, contact routes, figures, and any dependency on another policy. If a procedure has not changed, the reviewer still records a no-change decision and a new review date. A page more than 30 days overdue is marked `review_required`; search can return it, but an answer must disclose that its currency is uncertain.

## 4. Accepted file formats

The knowledge service accepts UTF-8 Markdown, plain text, HTML, DOCX, and text-based PDF. Markdown headings become section labels, PDF pages become citation units, and DOCX headings preserve their hierarchy. A scanned PDF without a text layer is not searchable until OCR has produced a reviewed text version. Password-protected PDFs and legacy-font Bangla that extracts as Latin gibberish are rejected with a conversion message. Uploaders should preview extracted text before relying on any table, footnote, or page reference.

## 5. File size and duplicate handling

An upload may contain at most 25 MiB. The service calculates a SHA-256 digest and rejects an identical file already uploaded by the same workspace, returning the identifier of the existing record. A revised document with changed bytes is a new upload; the owner must archive or delete the superseded version after confirming the replacement has indexed successfully. Renaming a duplicate does not create a new source. For large manuals, split the material at meaningful policy boundaries instead of reducing font size in a PDF.

## 6. Section-aware chunking

The indexer packs sentences up to a 400-token budget and carries up to 60 tokens of trailing context into the next chunk. It recognizes English full stops, question marks, exclamation marks, Bangla danda, and paragraph breaks. A chunk never crosses a PDF page or a parsed heading section, so citations remain local to the original source. Very long sentences are split at word boundaries. Short sections still produce their own chunks; adding many useful headings can therefore improve citation precision without making passages excessively long.

## 7. Language labels

Each indexed passage receives an English, Bangla, mixed, or unknown language label. The document-level label is based on token-weighted passage labels: one language must account for at least 80 percent of the measured content for the whole document to receive that single-language label. Otherwise the document is marked mixed. A short English heading does not erase a mostly Bangla passage. Reviewers should check extracted Unicode text when a Bangla page is unexpectedly classified as English or unknown.

## 8. Dense retrieval

Dense retrieval compares multilingual passage vectors with a query vector. The embedding model is multilingual E5 Large with 1,024 dimensions; indexed passages receive the `passage:` prefix and user queries receive the `query:` prefix. Similarity can connect an English question to a Bangla answer even when they share no exact words. Dense similarity is not proof of factual correctness: near-topic passages may rank highly. Evaluators should record whether the top result contains the requested fact, not merely whether its topic looks related.

## 9. Sparse retrieval

Sparse retrieval uses BM25 to reward query terms that appear in a passage, with greater weight for rarer terms. The custom tokenizer keeps Bangla combining marks attached to their base words, normalizes Bengali numerals such as `২০` to `20`, removes selected stopwords, and stems common English forms. This makes exact policy codes, amounts, and names easier to find. Sparse search may miss a valid cross-language paraphrase, so its result list should be compared with dense search before judging the final ranking.

## 10. Hybrid evaluation records

An evaluation row contains a stable query identifier, query text, expected document, expected heading or page, and a short answerable fact. A row may also list acceptable alternative passages when more than one source says the same thing. Do not store the expected answer only as a document title: that cannot distinguish the correct section from a topically similar section. Mark unanswerable questions explicitly and include at least one query that uses different wording from the source.

## 11. Recall at five

Recall@5 checks whether at least one relevant passage occurs in the first five results. For a single relevant passage, the row scores 1 when the passage appears in ranks one through five and 0 otherwise. With multiple relevant passages, recall is the number retrieved in the first five divided by the number judged relevant. Report the mean across the evaluation rows, and include the number of rows so that a change in test-set size cannot be mistaken for a quality improvement.

## 12. Mean reciprocal rank

Mean reciprocal rank rewards an early first relevant result. For each query, take the reciprocal of the rank of its first relevant passage; a passage at rank one scores 1, at rank two scores 0.5, and at rank five scores 0.2. If no relevant passage appears in the result list, the query scores 0. Average those values over the same fixed query set. MRR is sensitive to the first useful result and should be paired with a metric that considers more than one relevant passage.

## 13. Normalized discounted cumulative gain

NDCG supports graded relevance judgments. Reviewers assign relevance 3 to a passage that directly answers the query, 2 to one that provides essential supporting context, 1 to a related but incomplete passage, and 0 to an irrelevant passage. The score discounts lower-ranked results and divides the observed gain by the ideal ranking's gain. This makes the result comparable across queries with different numbers of relevant passages. Keep the same relevance rubric and assessors when comparing retrieval configurations.

## 14. Reciprocal rank fusion

Reciprocal Rank Fusion combines independent ranked lists without requiring their scores to share a scale. For each passage, add `1 / (k + rank)` across lists; Northstar's experiment uses `k = 60` and one-based ranks. A passage present in both dense and BM25 results accumulates evidence from both. A passage missing from a list contributes nothing for that list. Record the candidate-list depth and tie-breaking rule because changing either can alter the fused order even when the formula stays the same.

## 15. Reranking boundary

A cross-encoder reranker receives a query and each candidate passage together, then scores their pairwise relevance. It can improve ordering within the retrieved candidate set, but it cannot recover a relevant passage that dense and sparse retrieval both omitted. Keep the first-stage candidate depth fixed during a reranker comparison. Store both the fused rank and reranked rank for each result so that an evaluation can tell whether an improvement came from candidate recall or from better ordering.

## 16. Citation requirements

Every factual answer must cite the document filename and a page number or heading that exists in the indexed source. A citation should support the sentence immediately before it, not merely point to a document about the same subject. If two clauses rely on different sources, cite each clause separately. The answer validator rejects a citation whose document identifier was not among the retrieved passages. When a source has no page numbers, use its parsed heading and avoid inventing a page reference.

## 17. Unanswerable questions

The assistant should abstain when no indexed passage supports a requested fact, when sources conflict without a defined precedence rule, or when the only result is marked stale and the question requires current status. A fluent answer is not a substitute for evidence. An abstention should state which information is missing and identify the best source owner or follow-up route when one is available. Evaluation data should include answerable and unanswerable rows so that a system is not rewarded for guessing.

## 18. Indexing status and recovery

An uploaded document moves from `pending` to `processing`, then to `indexed` or `failed`. Only indexed documents are eligible for retrieval. A failed record includes a user-safe error message; operators can correct the source and request re-indexing. Re-indexing replaces old chunks and vectors rather than appending another copy. If an index count is zero, check the document status, parser output, and section count before investigating embedding quality. Never interpret a pending upload as a successful search source.

## 19. Access and retention

Every document and passage is scoped to a workspace user identifier, and vector searches must apply the same filter. The current local demonstration uses a single configured local user; it is not a multi-tenant production deployment. Deleting a document removes its stored upload, chunk records, vectors, and sparse-index entry. Operators should verify all four layers after a deletion test. Backups follow the workspace retention schedule and must not be placed in public sample folders.

## 20. Benchmark procedure

A benchmark run records the corpus revision, chunk settings, embedding model, candidate depth, fusion constant, reranker version, and evaluation-set revision. Run dense-only, BM25-only, fused, and fused-plus-reranker variants against the same queries. Report Recall@5, MRR, and NDCG, plus latency and the number of indexed documents and chunks. Inspect failures by language and query type instead of relying on one aggregate score. A result is reproducible only when its configuration and source snapshot can be identified.
