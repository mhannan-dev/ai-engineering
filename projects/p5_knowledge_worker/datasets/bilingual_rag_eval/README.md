# Bilingual RAG Eval (Bangla + English)

Questions in English, Bangla and Banglish over policy-style documents, with graded section-level
labels, for evaluating retrieval (and later, training a reranker). Version 0.1.0 is the seed: the
30 queries of the original benchmark, converted to this format. It is being expanded to 150+ test
queries over 9 categories.

## Files

| File | Contents |
| :--- | :--- |
| `manifest.json` | The documents: name, path, `train`/`test` split, language, license, source, publishable |
| `queries.jsonl` | One query per line (schema below) |

Documents currently point into `../../sample_documents/`; the published copy will include them.

## Query schema

```jsonc
{
  "id": "bn-num-014",                 // lowercase, digits, - and _
  "query": "আর চট্টগ্রামে?",
  "language": "bn",                   // en | bn | banglish | mixed
  "category": "follow_up",            // see below
  "answerable": true,
  "history": [["ঢাকার বাইরে দৈনিক ভাতা কত?", "১,৫০০ টাকা"]],   // follow_up only; gold answers
  "relevant": [{"doc": "travel_allowance_policy_bn.md", "section": "২. দৈনিক ভাতার হার",
                "page": null, "grade": 3}],
  "answer": "১,৮০০ টাকা",
  "split": "test"
}
```

- **`section`** is the exact heading the parser produces, or `null` for a document without
  headings. **`page`** narrows a PDF label to one page.
- **`grade`**: 3 answers the question, 2 is essential context, 1 is related. Retrieval metrics
  count grade 2 and above as relevant.
- **`history`** holds reference ("gold") answers, so a follow-up is scored on its own turn and
  results are reproducible. Measure end-to-end conversations separately.

Categories: `english`, `bangla`, `banglish`, `cross_lingual` (query and document in different
languages, either direction), `exact_term` (codes and names), `numeric`, `table`, `follow_up`,
`unanswerable`.

## Rules the validator enforces

```powershell
cd api
uv run python -m knowledge_worker.evaluation.validate ../datasets/bilingual_rag_eval
```

- **No leakage:** a query may only label documents of its own split, so a reranker trained on
  `train` is never scored on documents it saw.
- Every labelled section and page exists in the parsed document.
- The query's script matches its `language`; `cross_lingual` queries really cross languages.
- Unique ids; near-duplicate questions are flagged.
- Warns when a test category has fewer than 20 queries, and lists documents that must not be
  published.

The test suite runs the validator on this folder, so CI fails on an invalid dataset.

## Licensing

Synthetic documents (Northstar handbooks, `extra/`) are CC-BY-4.0. `BN.md` is a news article
(rights reserved by the publisher): it is used for local evaluation only and is excluded from the
published dataset.
