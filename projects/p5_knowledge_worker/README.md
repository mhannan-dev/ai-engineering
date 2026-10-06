# Project 5: Enterprise Knowledge Worker (p5_knowledge_worker)

Hybrid-search RAG over your own **English and Bangla** documents: dense vectors + BM25, fused with Reciprocal Rank Fusion, reranked by a cross-encoder, and answered with bracketed citations that point to a file and page.

> **Status: Phase 1 of 6 complete (ingestion).** Documents can be uploaded, parsed, chunked and indexed into both Qdrant and BM25. Retrieval, reranking, answer generation, evaluation and the web UI follow.

---

## 🗺️ Roadmap

| Phase | Scope | Status |
| :--- | :--- | :--- |
| 1 | Ingestion: parse → chunk → embed → Qdrant + BM25 | ✅ Done |
| 2 | Hybrid retrieval + hand-written RRF, `/search/debug` | ⏳ |
| 3 | Cross-encoder rerank (`jina-reranker-v2-base-multilingual`) + "I don't know" threshold | ⏳ |
| 4 | Faithful generation: Instructor schema, citation validator, SSE streaming | ⏳ |
| 5 | Eval harness: Recall@5 / MRR / nDCG, ablation dense vs BM25 vs RRF vs RRF+rerank | ⏳ |
| 6 | Next.js UI, JWT auth (from P3), README results | ⏳ |

---

## 🏗️ Ingestion Pipeline (Phase 1)

```
POST /api/v1/documents ──► validate by content ──► data/uploads/<user>/<id>.<fmt>   (202, status=pending)
                                                          │
                              single background worker ◄──┘
                                                          │
  parse        ingestion/parsers.py     PDF pages · DOCX/MD/HTML headings · DOCX tables
  guard        text/language.py         Bijoy/SutonnyMJ legacy encoding → failed with a fix-it message
  chunk        ingestion/chunker.py     sentence-aware (. ! ? ।), 400 tokens, 60 overlap, never crosses a page
  embed        ingestion/embedder.py    multilingual-e5-large (1024-d, ONNX on CPU), "passage: " prefix
  store        chunks table             text + page + heading + language (citations come from here)
               Qdrant                   vector + {user_id, document_id}
               BM25 (bm25s)             per-user index rebuilt from the chunks table
                                                          │
                                                   status=indexed
```

### Why Bangla needs its own tokenizer

The standard BM25 token pattern `\b\w\w+\b` breaks Bangla words at every vowel sign, because Python doesn't treat combining marks as word characters:

```
"ছুটির নীতিমালা অনুযায়ী কর্মীরা বছরে ২০ দিন ছুটি পাবেন।"
  default bm25s : ['অন', 'কর', 'বছর', '২০']                       ← useless
  text/tokenizer: ['ছুটি', 'নীতিমালা', 'অনুযায়ী', 'কর্মী', 'বছরে', '20', 'দিন', 'ছুটি', 'পাবেন']
```

[text/tokenizer.py](api/src/knowledge_worker/text/tokenizer.py) keeps Bengali-block runs whole, maps `২০` to `20`, removes ZWJ/ZWNJ, drops English and Bangla stopwords, applies Snowball stemming to English and a conservative suffix stripper to Bangla (`ছুটির → ছুটি`, `কর্মীদের → কর্মী`, `বইটি → বই`, but `ছুটি`, `মাটি` and `শহর` stay as they are).

### Why hybrid search

Measured on a sample handbook with English and Bangla sections (real model):

| Query | Dense top hit | BM25 top hit |
| :--- | :--- | :--- |
| How many days of annual leave do I get? | Leave Policy ✅ | Leave Policy ✅ |
| ঢাকার বাইরে গেলে দৈনিক ভাতা কত? | যাতায়াত ভাতা ✅ | যাতায়াত ভাতা ✅ |
| ছুটি কত দিন? | ছুটির নীতিমালা ✅ | ছুটির নীতিমালা ✅ |
| travel allowance outside Dhaka | যাতায়াত ভাতা ✅ (cross-lingual) | Remote Work ❌ (no shared words) |

Dense search matches meaning across languages. BM25 matches exact terms (codes, names, numbers) that embeddings blur. Phase 2 fuses both.

---

## 🛠️ Setup

Prerequisites: Python 3.12+, [uv](https://astral.sh/uv). Docker is optional.

```powershell
cd projects/p5_knowledge_worker
cp api/.env.example api/.env
.\run.ps1 -Install     # uv sync + migrations + model download (~2.2 GB, once)
.\run.ps1              # API at http://localhost:8000, Swagger at /docs
.\run.ps1 -Test        # pytest (uses a fake embedder and in-memory Qdrant; ~2 s)
.\run.ps1 -Qdrant      # optional Qdrant server via docker compose
```

By default Qdrant runs **embedded** (stored in `data/qdrant`, no Docker). For a server, run `.\run.ps1 -Qdrant` and set `QDRANT_URL=http://localhost:6333` in `api/.env`.

All runtime data (SQLite DB, uploads, Qdrant, BM25, models) lives in `data/`, which is git-ignored.

---

## 📡 API (Phase 1)

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents` | Upload (multipart `file`). Returns **202** with `status: pending`. |
| `GET` | `/api/v1/documents?limit=&offset=` | List (max 100 per page) |
| `GET` | `/api/v1/documents/{id}` | Status: `pending` → `processing` → `indexed` \| `failed` (+ `error_message`) |
| `GET` | `/api/v1/documents/{id}/chunks` | The passages retrieval will search, with page and heading |
| `POST` | `/api/v1/documents/{id}/reindex` | Re-run ingestion (e.g. after changing chunk settings) |
| `DELETE` | `/api/v1/documents/{id}` | Removes the file, chunks, vectors and BM25 entries |
| `GET` | `/health` | Liveness |

```powershell
curl -F "file=@handbook.pdf" http://localhost:8000/api/v1/documents
```

Errors always have the shape `{"error", "message", "details"}`, with these status codes: 409 duplicate file (`details.document_id`), 413 too large (25 MB), 415 unsupported type, 404 not found or not yours.

### Supported files

| Format | Detected by | Citation unit |
| :--- | :--- | :--- |
| PDF | `%PDF-` header | page |
| DOCX | ZIP containing `word/document.xml` | heading (+ tables) |
| Markdown / HTML / TXT | extension, must be UTF-8 | heading |

**Rejected with a clear message:**
- scanned PDFs (no text layer; OCR is not supported yet)
- password-protected PDFs
- legacy **Bijoy / SutonnyMJ** Bangla, which extracts as `Avgvi †mvbvi evsjv`; convert it to Unicode first
- non-UTF-8 text
- duplicate files

---

## ⚠️ Known Limitations (Phase 1)

- **No auth yet.** Every request acts as `LOCAL_USER_ID`. Every row and vector already carries `user_id`, and all queries filter on it, so Phase 6 only needs to replace `get_current_user_id` in [api/deps.py](api/src/knowledge_worker/api/deps.py).
- **Embedded Qdrant is single-process.** Run one API worker, or use the Qdrant server.
- **Re-indexing rebuilds the user's whole BM25 index.** bm25s can't update an index in place. This is fine up to tens of thousands of chunks.
- **CPU embedding speed.** e5-large indexes roughly a few chunks per second, so a 300-page PDF takes minutes. Indexing runs on one background worker, and the API stays responsive.
- **Model loading needs a workaround.** onnxruntime ≥ 1.30 won't load models from the Hugging Face cache's symlinked layout, so [embedder.py](api/src/knowledge_worker/ingestion/embedder.py) hard-links the model files into `data/models/flat/` first.

---

## 📂 Structure

```
p5_knowledge_worker/
  api/
    main.py                         entrypoint (uv run fastapi dev main.py)
    migrations/                     Alembic (SQLite + MySQL-safe, batch mode)
    src/knowledge_worker/
      api/v1/endpoints/             documents, health
      services/document_service.py  upload validation, list/get/delete/reindex (user-scoped)
      services/container.py         model, Qdrant, BM25 singletons + ingestion worker
      ingestion/                    parsers, chunker, embedder, vector_store, sparse_index, pipeline
      text/                         normalize, language (+ Bijoy detection), bilingual tokenizer
      db/                           models (documents, chunks), session
    tests/                          49 tests: tokenizer, parsers, chunker, indexes, API, migrations
  docker-compose.yml                optional Qdrant server
  run.ps1
  data/                             runtime data (git-ignored)
```
