# Project 5: Enterprise Knowledge Worker (p5_knowledge_worker)

[![P5 Knowledge Worker](https://github.com/mhannan-dev/ai-engineering/actions/workflows/p5-knowledge-worker.yml/badge.svg)](https://github.com/mhannan-dev/ai-engineering/actions/workflows/p5-knowledge-worker.yml)

Hybrid-search RAG over your own **English and Bangla** documents: dense vectors + BM25, fused with Reciprocal Rank Fusion, reranked by a cross-encoder, and answered with bracketed citations that point to a file and page.

> **Status: Phases 1–6 implemented.** API, web UI, JWT authentication and the retrieval benchmark are in place, and automated checks pass. [Evaluation results](#-evaluation-results-phase-5) are below; the manual end-to-end smoke test remains.

---

## 🗺️ Roadmap

| Phase | Scope | Status |
| :--- | :--- | :--- |
| 1 | Ingestion: parse → chunk → embed → Qdrant + BM25 | ✅ Done |
| 2 | Hybrid retrieval + hand-written RRF, `/search/debug` | ✅ Done |
| 3 | Cross-encoder rerank (`jina-reranker-v2-base-multilingual`) + "I don't know" threshold | ✅ Done |
| 4 | Faithful generation: Instructor schema, citation validator, SSE streaming | ✅ Done |
| 5 | Eval harness: Recall@5 / MRR / nDCG, ablation dense vs BM25 vs RRF vs RRF+rerank | ✅ Done |
| 6 | Next.js UI, JWT auth (from P3), README results | ✅ Done (manual smoke test pending) |

### Phase 6 verification

Automated checks passed on 2026-10-30:

- API: `uv run pytest`: 219 passed (one upstream deprecation warning). `uv run ruff check .`: clean.
- Web: `npx eslint src` and `npx tsc --noEmit`: clean.
- Web: `npm run build`: passed; `/`, `/chat`, `/login`, `/register` and `/search` prerendered as static.

Manual end-to-end verification is still pending: register/sign in, upload a document, search and chat with it, then confirm citations and user-scoped access. [sample_documents/extra/](sample_documents/extra/) has documents and questions for this.

---

## 📊 Evaluation results (Phase 5)

Retrieval benchmark on [eval_dataset.json](sample_documents/eval_dataset.json): 30 queries (27 answerable, 3 unanswerable) over the three documents it references (the two sample handbooks and `BN.md`, 63 chunks), indexed with the real models (`multilingual-e5-large`, `jina-reranker-v2-base-multilingual`) on CPU. Run on 2026-10-30.

| Variant | Recall@5 | MRR | nDCG@5 |
| :--- | ---: | ---: | ---: |
| Dense (e5-large) | 0.951 | 0.869 | 0.891 |
| BM25 | 0.685 | 0.674 | 0.676 |
| RRF (dense + BM25) | 0.815 | 0.737 | 0.756 |
| **RRF + cross-encoder rerank** (what chat uses) | **1.000** | **0.954** | **0.964** |

Recall@5 by query category:

| Category | Dense | BM25 | RRF | RRF + rerank |
| :--- | ---: | ---: | ---: | ---: |
| English | 1.000 | 1.000 | 1.000 | 1.000 |
| Bangla | 0.967 | 0.950 | 1.000 | 1.000 |
| Cross-lingual | 0.833 | 0.000 | 0.167 | 1.000 |
| Banglish | 1.000 | 0.333 | 1.000 | 1.000 |

**What this shows**

- **The full pipeline finds every answer in the top 5.** RRF + rerank is the best variant on every metric and every category.
- **RRF alone is worse than dense alone (0.815 vs 0.951), entirely because of cross-lingual queries (0.167 vs 0.833).** An English question about a Bangla section shares almost no words with it, so BM25's hits are unrelated. RRF still rewards chunks that appear in both lists, and with `k = 60` that bonus outweighs being dense's #1: the gap between rank 1 and rank 2 is 1/61 − 1/62 ≈ 0.0003, while appearing in the other list too adds 1/(60 + rank), between 0.016 (rank 1) and 0.0125 (rank 20).
- **Reranking fixes it because RRF is used for candidates, not the final order.** The correct passage is still within RRF's top 20, and the cross-encoder reads the query and passage together, across languages, to put it first (cross-lingual 0.167 → 1.000).
- **BM25 earns its place on exact terms**, not on recall: it is at 1.000 for English and 0.950 for Bangla, where codes, numbers and names must match literally, and it adds candidates dense search ranks low.

**What was tried and dropped.** Weighting BM25 per query by how much of the query its best hit contains (low for cross-lingual queries, high for exact codes) changed RRF's MRR by only +0.005 and Recall@5 not at all. The reason is the same rank-gap arithmetic: any non-trivial weight still lets two-list "consensus" beat dense's #1, and pushing the weight near zero would mean tuning a threshold on 30 queries. Since the reranked output was already at 1.000, the extra complexity wasn't kept.

**Eval fixes behind these numbers.** An earlier run reported much lower scores (dense 0.667, RRF + rerank 0.556) because of three benchmark bugs, now fixed:

1. Labels weren't normalized like stored headings. Ingestion stores NFC text, which decomposes Bangla `য়` (U+09DF) into `য` + nukta, so labels such as `২. খোলা ও বন্ধের সময়` never matched their own sections.
2. `BN.md`, which two queries need, wasn't indexed.
3. `search_debug` reranked only RRF's top 5, while chat's `retrieve_and_rerank` reranks the top 20, so the benchmark measured a weaker pipeline than production.

**Caveats**

- 30 queries over 63 chunks is small: one query moves Recall@5 by about 0.04, and a 1.000 here doesn't mean a larger corpus would score the same.
- `BN.md` has no headings, and the runner treats an empty chunk heading as matching any expected heading, so for its two queries any `BN.md` chunk counts as relevant.
- Latency isn't reported per variant: one `search_debug` call produces all four rankings, so its time (a few seconds per query on CPU, mostly the reranker) belongs to the whole pipeline.

**Next experiments**

1. A larger eval set over [sample_documents/extra/](sample_documents/extra/) (PDF pages, DOCX tables, HTML) to test the pipeline beyond 63 chunks.
2. Time each variant separately, and measure how far the rerank pool can shrink before recall drops (it is the main latency cost).
3. Add headings to `BN.md`, or label its queries at chunk level, so the runner's heading match is meaningful there.

To reproduce: index the three documents for `LOCAL_USER_ID` (e.g. with `AUTH_ENABLED=false`), stop the API (embedded Qdrant allows one process), then run `.\run.ps1 -Eval`.

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

### With Docker (full stack)

Prerequisites: Docker with Compose.

```powershell
cd projects/p5_knowledge_worker
cp .env.example .env          # set SECRET_KEY (the API refuses to start without one)
cp api/.env.example api/.env  # optional: OPENAI_API_KEY for chat answers
docker compose up --build     # web: http://localhost:3000   API: http://localhost:8000/docs
```

This runs the web UI, the API (migrations run on start) and a Qdrant server, so there is no embedded-Qdrant lock to manage. The API runs with `ENVIRONMENT=production`: the demo-account button is off, so register an account. Data lives in Docker volumes; models are read from `data/models`, so a machine that already ran `.\run.ps1 -Install` doesn't download them again (otherwise the first start downloads about 3 GB). Stop `.\run.ps1` first, since both use ports 8000 and 3000.

### Local development

Prerequisites: Python 3.12+, [uv](https://astral.sh/uv). Docker is optional.

```powershell
cd projects/p5_knowledge_worker
cp api/.env.example api/.env
.\run.ps1 -Install     # uv sync + migrations + model download (~2.2 GB, once)
.\run.ps1              # API at http://localhost:8000 (Swagger: /docs) + web UI at http://localhost:3000
.\run.ps1 -Web         # web UI only
.\run.ps1 -Test        # pytest (uses a fake embedder and in-memory Qdrant)
.\run.ps1 -Eval        # retrieval benchmark (stop the API first)
.\run.ps1 -Stop        # stop the API and web, including leftover worker processes
.\run.ps1 -Qdrant      # optional Qdrant server via docker compose
```

`.\run.ps1` stops any earlier API or web process of this project before starting, so a leftover worker can't keep the embedded Qdrant locked.

For answers in chat, set `OPENAI_API_KEY` (a DeepSeek key with the default `LLM_MODEL=deepseek/deepseek-chat`) in `api/.env`. LiteLLM needs the provider prefix in the model name.

By default Qdrant runs **embedded** (stored in `data/qdrant`, no Docker). For a server, run `.\run.ps1 -Qdrant` and set `QDRANT_URL=http://localhost:6333` in `api/.env`.

All runtime data (SQLite DB, uploads, Qdrant, BM25, models) lives in `data/`, which is git-ignored.

---

## 📡 API

All `/api/v1` routes except `auth/*` and `health` need `Authorization: Bearer <token>` when `AUTH_ENABLED=true` (the default). Swagger's **Authorize** button takes the token.

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/auth/config` | Whether sign-in is required |
| `POST` | `/api/v1/auth/register` | Create an account; returns a token |
| `POST` | `/api/v1/auth/login` | Sign in; returns a token. **429** + `Retry-After` after repeated failures |
| `POST` | `/api/v1/auth/demo` | Demo account, local development only |
| `GET` | `/api/v1/auth/me` | The signed-in user |
| `POST` | `/api/v1/documents` | Upload (multipart `file`). Returns **202** with `status: pending`. |
| `GET` | `/api/v1/documents?limit=&offset=` | List (max 100 per page) |
| `GET` | `/api/v1/documents/{id}` | Status: `pending` → `processing` → `indexed` \| `failed` (+ `error_message`) |
| `GET` | `/api/v1/documents/{id}/chunks` | The passages retrieval will search, with page and heading |
| `POST` | `/api/v1/documents/{id}/reindex` | Re-run ingestion (e.g. after changing chunk settings) |
| `DELETE` | `/api/v1/documents/{id}` | Removes the file, chunks, vectors and BM25 entries |
| `POST` | `/api/v1/search` | Hybrid search (RRF, optional rerank) |
| `GET` | `/api/v1/search/debug?query=` | Dense, BM25, RRF and reranked lists side by side |
| `POST` | `/api/v1/chat` | Answer with citations and citation validation. Optional `conversation_id` continues a saved chat |
| `POST` | `/api/v1/chat/stream` | Same, streamed as Server-Sent Events: `status`, `sources`, `token`, `validation`, `conversation`, `done`, or `error` |
| `GET` | `/api/v1/chat/conversations` | Saved chats, most recent first |
| `GET` | `/api/v1/chat/conversations/{id}` | One chat with its messages, citations and sources |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete a chat and its messages |
| `GET` | `/health` | Liveness |

```powershell
curl -H "Authorization: Bearer $token" -F "file=@handbook.pdf" http://localhost:8000/api/v1/documents
```

Errors always have the shape `{"error", "message", "details"}`, with these status codes: 401 not signed in, 409 duplicate file (`details.document_id`) or email, 413 too large (25 MB), 415 unsupported type, 404 not found or not yours, 429 too many sign-in attempts, 502 the LLM provider failed. Provider errors are logged on the server; the client only gets a generic message, never the provider's text (which can contain keys and paths).

**Chat history.** A question and its answer are saved together once the answer completes (a failed or stopped answer saves nothing), so a reopened chat shows exactly what was cited. Follow-ups such as "And sick leave?" are rewritten into a standalone question from the last `CHAT_HISTORY_TURNS` turns (default 3) before retrieval; the rewrite keeps the message's language and is what both search and the answer use, while the history keeps the user's own words. A conversation's first message needs no rewrite, so it costs no extra LLM call.

There is no `GET` variant of the chat stream: browsers' EventSource can't send the `Authorization` header, and a token in the URL would end up in logs and history. The web UI reads the `POST` stream with `fetch()`.

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

## ⚠️ Known Limitations

- **Authentication is configurable.** With `AUTH_ENABLED=true` (the default), protected API requests require a bearer access token obtained from `/api/v1/auth/register` or `/api/v1/auth/login`. In local development, the login page also offers a demo-account button; the API disables this endpoint outside local/development environments. For local experiments, `AUTH_ENABLED=false` makes requests act as `LOCAL_USER_ID`. Every row and vector carries `user_id`, and queries are scoped to it.
- **Embedded Qdrant is single-process.** Run one API worker, or use the Qdrant server.
- **Sign-in rate limiting is in memory.** Counts reset on restart and aren't shared between processes; several API processes would need a shared store such as Redis. The client IP is the socket address, so behind a reverse proxy it needs trusted-proxy handling.
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
      api/v1/endpoints/             auth, documents, search, chat, health
      services/                     document and user services, container (models, Qdrant, BM25, worker)
      ingestion/                    parsers, chunker, embedder, vector_store, sparse_index, pipeline
      retrieval/                    RRF fusion, hybrid retriever, cross-encoder reranker
      generation/                   LLM client, prompts, faithful generator, citation validator
      evaluation/                   dataset, metrics, benchmark runner, CLI
      core/                         errors, security (password hashing, JWT), sign-in rate limit
      text/                         normalize, language (+ Bijoy detection), bilingual tokenizer, Banglish
      db/                           models (users, documents, chunks), session
    tests/                          219 tests
  web/                              Next.js UI: documents, search (with retriever comparison), chat, sign-in
  sample_documents/                 eval handbooks + eval_dataset.json; extra/ for manual testing
  docker-compose.yml                full stack: Qdrant server + API + web (Dockerfiles in api/ and web/)
  run.ps1
  data/                             runtime data (git-ignored)
```
