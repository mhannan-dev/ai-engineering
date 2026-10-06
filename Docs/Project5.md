# Project 5: Enterprise Knowledge Worker — Production-Grade RAG
## এন্টারপ্রাইজ নলেজ ওয়ার্কার — প্রোডাকশন-গ্রেড RAG

---

## 🎯 Project Overview / প্রজেক্ট পরিচিতি

**English:** Build a production-ready Enterprise Knowledge Assistant that ingests company documents, retrieves relevant information via hybrid search, reranks results, and generates grounded answers with verifiable citations — backed by a measurable RAG evaluation framework.

**বাংলা:** একটি প্রোডাকশন-লেভেল এন্টারপ্রাইজ নলেজ অ্যাসিস্ট্যান্ট তৈরি করব — যা কোম্পানির ডকুমেন্ট ingest করবে, hybrid search দিয়ে তথ্য retrieve করবে, cross-encoder দিয়ে rerank করবে, এবং verifiable citation সহ grounded উত্তর দেবে — সাথে একটি measurable RAG evaluation framework থাকবে।

**Why this matters / কেন গুরুত্বপূর্ণ:** Most RAG tutorials stop at "embed → vector search → LLM." That's a toy. Real enterprise RAG needs **hybrid retrieval, reranking, citation verification, RBAC, and evaluation**. This project builds all of that.

**কেন গুরুত্বপূর্ণ:** বেশিরভাগ RAG টিউটোরিয়াল "embed → vector search → LLM" এ থেমে যায় — এটা খেলনা। আসল এন্টারপ্রাইজ RAG-এ দরকার **hybrid retrieval, reranking, citation verification, RBAC, এবং evaluation**। এই প্রজেক্টে সবকিছুই বানানো হবে।

---

# Phase 1 — Document Ingestion Pipeline
# ফেজ ১ — ডকুমেন্ট ইনজেশন পাইপলাইন

**English:** Support PDF, DOCX, TXT, Markdown, and HTML ingestion with parsing, metadata extraction, intelligent chunking, versioning, deduplication, and async job processing.

**বাংলা:** PDF, DOCX, TXT, Markdown, HTML ingest করা; parsing, metadata extraction, intelligent chunking, versioning, deduplication, এবং async job processing সহ।

### English — What to Build

```python
# src/ingestion/parser.py
from pathlib import Path
from typing import Protocol
import hashlib
from datetime import datetime, timezone

class DocumentParser(Protocol):
    """Contract for any document parser."""
    def parse(self, path: Path) -> dict: ...


class PDFParser:
    """Parse PDF → text + per-page metadata."""
    def parse(self, path: Path) -> dict:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            pages.append({"page": i + 1, "text": page.extract_text() or ""})
        return {
            "source": str(path),
            "doc_type": "pdf",
            "pages": pages,
            "metadata": dict(reader.metadata or {}),
        }


def compute_content_hash(text: str) -> str:
    """SHA-256 of normalized text — used for duplicate detection."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def detect_duplicate(new_hash: str, known_hashes: set[str]) -> bool:
    return new_hash in known_hashes
```

### বাংলা — কী বানাবেন

- **Parser Protocol**: প্রতিটা document type-এর জন্য আলাদা parser (`PDFParser`, `DOCXParser`, `MarkdownParser`, `HTMLParser`) — সবাই একই `parse()` contract মানবে।
- **Metadata extraction**: title, author, created date, file size, page count, language।
- **Duplicate detection**: content-এর SHA-256 hash মিলিয়ে দেখা — একই document দুইবার ingest হবে না।
- **Versioning**: একই document-এর নতুন version এলে পুরোনো version `archived` flag পাবে, delete হবে না।
- **Async ingestion**: FastAPI `BackgroundTasks` বা Celery/ARQ দিয়ে queue-এ push — API block হবে না।
- **Retry mechanism**: failed ingestion ৩ বার retry, তারপর dead-letter queue-তে যাবে।

**Interview Tip:** "How do you handle duplicate documents in an enterprise RAG?" — উত্তর: content hash + version tracking।

---

# Phase 2 — Intelligent Chunking
# ফেজ ২ — বুদ্ধিমান চাংকিং

**English:** Chunking strategy decides RAG quality more than the LLM choice. Use structure-aware chunking with overlap.

**বাংলা:** RAG-এর গুণমান LLM-এর চেয়ে chunking strategy-র উপর বেশি নির্ভর করে। Structure-aware chunking ব্যবহার করুন, overlap সহ।

### English — Chunking Strategy

```python
# src/ingestion/chunker.py
from dataclasses import dataclass
import tiktoken

@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    content: str
    token_count: int
    page: int | None
    metadata: dict


class RecursiveChunker:
    """Split by headers → paragraphs → sentences, with overlap."""
    
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 64):
        self.max_tokens = max_tokens
        self.overlap = overlap_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def chunk(self, text: str, doc_id: str, page: int | None = None) -> list[Chunk]:
        # 1. Split on double newlines (paragraphs)
        # 2. Greedily pack paragraphs until max_tokens
        # 3. Carry over last overlap_tokens to next chunk
        ...
```

### বাংলা — চাংকিং কৌশল

| Strategy | কখন ব্যবহার | সুবিধা |
|---|---|---|
| **Fixed-size** | Simple baseline | সহজ, predictable |
| **Recursive** | General purpose | Structure respect করে |
| **Semantic** | High-value docs | Meaning-preserving |
| **Parent-child** | Long docs | Small chunks retrieve, big chunks feed LLM |
| **Structure-aware** | Markdown/HTML | Headers preserve |

**Golden rule:** 512-token chunk, 64-token overlap — industry default। কিন্তু **parent-child** strategy সবচেয়ে ভালো results দেয়: ছোট chunk দিয়ে search করবেন, বড় parent chunk LLM-কে দেবেন।

---

# Phase 3 — Embeddings & Vector Search
# ফেজ ৩ — এমবেডিং ও ভেক্টর সার্চ

**English:** Generate embeddings, store in vector DB, filter by metadata, top-K similarity search.

**বাংলা:** Embedding generate করা, vector DB-তে রাখা, metadata দিয়ে filter করা, top-K similarity search চালানো।

```python
# src/retrieval/vector_store.py
from typing import Protocol

class VectorStore(Protocol):
    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...
    async def search(self, query_vec: list[float], top_k: int, filters: dict) -> list[dict]: ...


class QdrantStore:
    """Qdrant — production-grade vector DB with payload filtering."""
    def __init__(self, url: str, collection: str):
        from qdrant_client import AsyncQdrantClient
        self.client = AsyncQdrantClient(url=url)
        self.collection = collection
    
    async def search(self, query_vec, top_k, filters):
        return await self.client.search(
            collection_name=self.collection,
            query_vector=query_vec,
            limit=top_k,
            query_filter=filters,   # ← metadata filtering
        )
```

**এমবেডিং মডেল তুলনা / Embedding model comparison:**

| Model | Dim | Speed | Quality | Cost |
|---|---|---|---|---|
| `text-embedding-3-small` | 1536 | Fast | Good | $0.02/M |
| `text-embedding-3-large` | 3072 | Medium | Best | $0.13/M |
| `bge-large-en-v1.5` | 1024 | Medium | Very good | Free (self-host) |
| `e5-mistral-7b` | 4096 | Slow | Excellent | GPU needed |

**Interview Tip:** "Why might vector search fail?" — It can miss exact tokens like `INV-2026-1003`, `Laravel Sanctum`, product SKUs, error codes. Semantic similarity doesn't care about exact strings. That's why we need BM25.

---

# Phase 4 — Sparse Keyword Search with BM25
# ফেজ ৪ — BM25 দিয়ে স্পার্স কীওয়ার্ড সার্চ

**English:** Implement BM25 from scratch (or use `rank_bm25`). This handles exact-term retrieval that vectors miss.

**বাংলা:** BM25 নিজে implement করুন (বা `rank_bm25` ব্যবহার করুন)। এটি exact-term retrieval সামলায়, যা vector miss করে।

### The BM25 Formula / BM25 সূত্র

$$
\text{score}(q, d) = \sum_{t \in q} IDF(t) \cdot \frac{f(t,d) \cdot (k_1 + 1)}{f(t,d) + k_1 \cdot (1 - b + b \cdot \frac{|d|}{avgdl})}
$$

যেখানে:
- `f(t,d)` = term `t`-এর frequency `d` document-এ
- `|d|` = document length
- `avgdl` = average document length
- `k1` = term frequency saturation (1.2–2.0)
- `b` = length normalization (0.75)

```python
# src/retrieval/bm25_index.py
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.tokenized: list[list[str]] = []
        self.index: BM25Okapi | None = None
    
    def add(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            self.chunks.append(c)
            self.tokenized.append(self._tokenize(c.content))
        self.index = BM25Okapi(self.tokenized)
    
    def _tokenize(self, text: str) -> list[str]:
        import re
        return re.findall(r"\w+", text.lower())
    
    def search(self, query: str, top_k: int) -> list[tuple[Chunk, float]]:
        scores = self.index.get_scores(self._tokenize(query))
        ranked = sorted(zip(self.chunks, scores), key=lambda x: -x[1])
        return ranked[:top_k]
```

**কী শিখবেন / What you learn:**

> `INV-2026-1003` — vector search এটা "invoice number" ভাববে, exact match পাবে না। BM25 exact token হিসেবে পাবে। এটাই **hybrid search কেন দরকার** — দুইটা ভিন্ন দৃষ্টিভঙ্গি।

---

# Phase 5 — Hybrid Search
# ফেজ ৫ — হাইব্রিড সার্চ

**English:** Combine dense + sparse retrieval into one candidate pool.

**বাংলা:** Dense + sparse retrieval একসাথে মিলিয়ে এক candidate pool-এ আনুন।

```
User Query
    │
    ├──► Dense Vector Search ──► Top 20
    │
    └──► BM25 Search ─────────► Top 20
                │
                ▼
        Candidate Pool (dedup)
                │
                ▼
          Metadata Filter
                │
                ▼
         Merged Results
```

```python
# src/retrieval/hybrid.py
class HybridRetriever:
    def __init__(self, vector: VectorStore, bm25: BM25Index):
        self.vector = vector
        self.bm25 = bm25
    
    async def retrieve(self, query: str, top_k: int = 20, filters: dict = None):
        query_vec = await embed(query)
        dense = await self.vector.search(query_vec, top_k=top_k, filters=filters)
        sparse = self.bm25.search(query, top_k=top_k)
        return self._dedupe(dense, sparse)
    
    def _dedupe(self, dense, sparse):
        seen = set()
        merged = []
        for chunk, score in dense + sparse:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                merged.append(chunk)
        return merged
```

**বাংলা — কী বানাবেন:**
- **Configurable Top-K** — dense-এর জন্য আলাদা, sparse-এর জন্য আলাদা
- **Metadata filtering** — access control + document type + date range
- **Weighted hybrid** — `α·vector + (1-α)·bm25` — α tune করতে হবে
- **Fallback strategy** — যদি vector result কম আসে, BM25 বেশি weight পাবে

---

# Phase 6 — Reciprocal Rank Fusion (RRF)
# ফেজ ৬ — রিসিপ্রোকাল র‍্যাংক ফিউশন

**English:** RRF combines ranked lists from multiple retrieval systems without needing score normalization — because raw BM25 scores and cosine similarities are incomparable.

**বাংলা:** RRF একাধিক retrieval system-এর ranked list মেলায় — score normalization ছাড়াই, কারণ BM25-এর raw score আর cosine similarity তুলনাযোগ্য নয়।

### Formula / সূত্র

$$
RRF(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}
$$

- `k` = constant (usually 60)
- `rank_r(d)` = rank of document `d` in ranking `r`
- `R` = set of ranked lists

```python
# src/retrieval/rrf.py
def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    ranked_lists: list of lists of doc_ids, each sorted by relevance.
    Returns: merged list of (doc_id, rrf_score), sorted descending.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

**কেন RRF ভালো / Why RRF works:**
- **Scale-free** — BM25 score (0-50) আর cosine (0-1) comparably করা লাগে না
- **Robust** — এক system খারাপ result দিলেও combined result ভালো থাকে
- **Simple** — 10 lines of code, no tuning except `k`

### Experiment / পরীক্ষা

```
Experiment A: Vector only       → Recall@10 = 0.62
Experiment B: BM25 only         → Recall@10 = 0.58
Experiment C: Weighted hybrid   → Recall@10 = 0.71
Experiment D: RRF               → Recall@10 = 0.79  ← winner
```

**Interview gold:** "I replaced naive weighted hybrid with RRF and improved Recall@10 from 0.71 to 0.79 — because RRF is rank-based, it doesn't suffer from score scale mismatch."

---

# Phase 7 — Cross-Encoder Re-Ranking
# ফেজ ৭ — ক্রস-এনকোডার রি-র‍্যাংকিং

**English:** Bi-encoders (embeddings) are fast but approximate. Cross-encoders see query + document together — much more accurate, but too slow to run on millions of docs. So we use them only on top candidates.

**বাংলা:** Bi-encoder (embedding) দ্রুত কিন্তু approximate। Cross-encoder query + document একসাথে দেখে — অনেক বেশি accurate, কিন্তু millions docs-এ চালানো অসম্ভব। তাই শুধু top candidate-এ চালাই।

```
Query
  ↓
Hybrid Retrieval (top 50)
  ↓
RRF
  ↓
Top 20
  ↓
Cross Encoder  ← query + doc together
  ↓
Top 5
  ↓
LLM
```

```python
# src/retrieval/reranker.py
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model = CrossEncoder(model_name)
    
    def rerank(self, query: str, candidates: list[Chunk], top_n: int = 5):
        pairs = [(query, c.content) for c in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
        return [c for c, _ in ranked[:top_n]]
```

**Bi-encoder vs Cross-encoder / তুলনা:**

| | Bi-encoder | Cross-encoder |
|---|---|---|
| **Input** | Query & doc separately | Query + doc together |
| **Speed** | Very fast (pre-computed) | Slow (per pair) |
| **Accuracy** | Good | Excellent |
| **Use case** | Retrieve 1M docs | Rerank top 50 |
| **Model** | `text-embedding-3-small` | `bge-reranker-v2-m3` |

---

# Phase 8 — Query Understanding
# ফেজ ৮ — কুয়েরি আন্ডারস্ট্যান্ডিং

**English:** Raw user query → multiple refined queries. This often improves retrieval more than upgrading the LLM.

**বাংলা:** Raw user query → একাধিক refined query। LLM upgrade করার চেয়ে এটা প্রায়ই বেশি retrieval improvement দেয়।

```python
# src/query/rewriter.py
from pydantic import BaseModel
import instructor, litellm

class QueryPlan(BaseModel):
    normalized: str
    rewritten: list[str]
    intent: str  # "policy_lookup" | "how_to" | "definition" | ...
    entities: list[str]

client = instructor.from_litellm(litellm.completion)

def plan_query(user_query: str, history: list[dict] = None) -> QueryPlan:
    return client.chat.completions.create(
        model="openai/gpt-4o-mini",
        response_model=QueryPlan,
        messages=[{
            "role": "system",
            "content": (
                "Rewrite the user query into 2-3 search-optimized variants. "
                "Preserve exact IDs, names, and codes. Detect intent."
            ),
        }, {
            "role": "user",
            "content": user_query,
        }],
    )
```

**বাংলা — কোন কোন feature:**

| Feature | উদাহরণ |
|---|---|
| **Normalization** | `"রিফান্ড"` → `"refund policy"` (bangla→english) |
| **Rewriting** | `"refund?"` → `"company refund policy"` |
| **Expansion** | `"PTO"` → `"PTO OR paid time off OR annual leave"` |
| **Intent detection** | classify: policy / how-to / definition / data lookup |
| **Multi-query** | 3 variants → retrieve 3× → merge with RRF |
| **Conversation-aware** | `"What about managers?"` → `"manager leave policy"` |

**Golden insight:** "Retrieval quality > LLM size." A GPT-4o with bad retrieval hallucinates. A GPT-4o-mini with perfect retrieval is grounded.

---

# Phase 9 — Context Selection & Compression
# ফেজ ৯ — কনটেক্সট সিলেকশন ও কম্প্রেশন

**English:** Don't dump 20 documents into the LLM. Dedupe, order, compress, and fit within a token budget.

**বাংলা:** LLM-এ ২০টা document ঠেলে দেবেন না। Dedupe, order, compress করুন এবং token budget-এ ফিট করুন।

```
Retrieved (Top 20)
       ↓
Deduplicate (content hash + n-gram overlap)
       ↓
Rerank (cross-encoder)
       ↓
Compress (extract relevant sentences)
       ↓
Order (most relevant first — "lost in middle" mitigation)
       ↓
Token Budget Check (≤ 8K tokens)
       ↓
LLM
```

```python
# src/context/builder.py
def build_context(chunks: list[Chunk], budget_tokens: int = 8000) -> list[Chunk]:
    # 1. Dedupe by content hash
    seen = set()
    unique = []
    for c in chunks:
        h = hash(c.content[:200])
        if h not in seen:
            seen.add(h)
            unique.append(c)
    
    # 2. Fit within budget, most-relevant first
    total = 0
    selected = []
    for c in unique:
        if total + c.token_count > budget_tokens:
            break
        selected.append(c)
        total += c.token_count
    return selected
```

**"Lost in the middle" problem:** LLM-রা context-এর শুরু আর শেষ ভালো মনে রাখে, মাঝখানে ভুলে যায়। তাই **most-relevant chunk সবার আগে** রাখুন।

---

# Phase 10 — Faithful / Grounded Generation
# ফেজ ১০ — বিশ্বস্ত / গ্রাউন্ডেড জেনারেশন

**English:** The LLM must answer **only** from retrieved evidence. No evidence → say so.

**বাংলা:** LLM শুধু retrieve করা evidence থেকে উত্তর দেবে। Evidence না থাকলে বলবে।

### System Prompt / সিস্টেম প্রম্পট

```python
GROUNDED_SYSTEM_PROMPT = """You are an enterprise knowledge assistant.

RULES:
1. Answer ONLY using the provided context.
2. Every factual claim MUST have a citation like [1], [2].
3. If context is insufficient, respond EXACTLY:
   "I don't have enough information in the available documents to answer that."
4. NEVER use outside knowledge.
5. NEVER speculate or infer beyond the context.
6. Preserve exact IDs, codes, names as they appear in the source.

Context:
{context}
"""
```

**বাংলা উদাহরণ:**

```
প্রশ্ন: "কত দিনের annual leave পাই?"

Context: Employee Handbook, Page 12:
"All full-time employees are entitled to 20 days of annual leave per calendar year."

উত্তর: "Employee Handbook অনুযায়ী, full-time employee-রা বছরে ২০ দিন annual leave পান। [1]

[1] Employee Handbook — Page 12"
```

---

# Phase 11 — Citation System
# ফেজ ১১ — সাইটেশন সিস্টেম

**English:** Every chunk has structured metadata; every LLM claim references `[n]`; the UI resolves `[n]` back to source.

**বাংলা:** প্রতিটা chunk-এ structured metadata; প্রতিটা LLM claim `[n]` reference করে; UI `[n]` কে source-এ resolve করে।

### Chunk Schema / চাংক স্কিমা

```json
{
  "document_id": "doc_123",
  "chunk_id": "chunk_45",
  "title": "Employee Handbook",
  "page": 12,
  "section": "Leave Policy",
  "content": "All full-time employees are entitled to 20 days...",
  "metadata": {
    "author": "HR Department",
    "created_at": "2025-01-15",
    "version": "3.2",
    "access_level": "public"
  }
}
```

### Rendering / রেন্ডারিং

```
উত্তর:
Full-time employee-রা বছরে ২০ দিন annual leave পান [1]। Manager-রা অতিরিক্ত ৫ দিন পান [2]।

Sources:
[1] Employee Handbook — Page 12, Section "Leave Policy"
[2] Management Policy — Page 4, Section "Additional Benefits"
```

**Citation أنواع / সাইটেশনের ধরন:**
- Multiple citations: `[1][2]`
- Ranges: `[1-3]`
- Page numbers: `Page 12`
- Source links: `https://intranet/hr/handbook#page=12`

---

# Phase 12 — Citation Verification
# ফেজ ১২ — সাইটেশন যাচাই

**English:** Don't trust the LLM's citations blindly. Verify each `[n]` claim against the actual chunk.

**বাংলা:** LLM-এর citation অন্ধভাবে বিশ্বাস করবেন না। প্রতিটা `[n]` claim আসল chunk-এর সাথে মিলিয়ে দেখুন।

```
Generated Answer
       ↓
Extract [1], [2], [3]
       ↓
Find referenced chunks
       ↓
Check supporting evidence
   (NLI model or embedding sim)
       ↓
Verdict: PASS / FAIL
```

```python
# src/verification/citation_checker.py
from pydantic import BaseModel
import instructor, litellm

class ClaimCheck(BaseModel):
    claim: str
    citation_id: int
    supported: bool
    reason: str

client = instructor.from_litellm(litellm.completion)

def verify_citations(answer: str, chunks: list[Chunk]) -> list[ClaimCheck]:
    return client.chat.completions.create(
        model="openai/gpt-4o-mini",
        response_model=list[ClaimCheck],
        messages=[{
            "role": "system",
            "content": (
                "For each claim + citation pair, determine if the cited chunk "
                "actually supports the claim. Be strict."
            ),
        }, {
            "role": "user",
            "content": f"Answer:\n{answer}\n\nChunks:\n{[c.content for c in chunks]}",
        }],
    )
```

**কী কী ধরবেন / What to detect:**

| Problem | Example |
|---|---|
| **Missing citation** | "Employees get 20 days leave." (no `[1]`) |
| **Invalid citation** | `[5]` but only 3 chunks exist |
| **Unsupported claim** | Citation exists, but chunk doesn't say that |
| **Wrong source** | Claim about HR, cites Finance doc |

---

# Phase 13 — RAG Evaluation Framework
# ফেজ ১৩ — RAG মূল্যায়ন ফ্রেমওয়ার্ক

**English:** This is the most interview-relevant phase. Without measurement, you're guessing.

**বাংলা:** এটা সবচেয়ে interview-relevant phase। measurement ছাড়া সব অনুমান।

### Evaluation Dataset / মূল্যায়ন ডেটাসেট

```json
[
  {
    "question": "How many annual leave days do employees get?",
    "expected_answer": "20 days per year for full-time employees",
    "expected_sources": ["Employee Handbook, Page 12"],
    "difficulty": "easy"
  },
  {
    "question": "Can managers approve leave during peak quarter?",
    "expected_answer": "No, peak-quarter leave requires VP approval",
    "expected_sources": ["Management Policy, Page 4"],
    "difficulty": "hard"
  }
]
```

### Retrieval Metrics / রিট্রিভাল মেট্রিক

| Metric | Meaning | Formula |
|---|---|---|
| **Recall@K** | কত relevant doc top-K-তে আছে | `relevant_in_top_K / total_relevant` |
| **Precision@K** | top-K-এর কত % relevant | `relevant_in_top_K / K` |
| **MRR** | প্রথম relevant doc-এর rank | `1/rank_first_relevant` |
| **NDCG@K** | Rank-weighted relevance | `DCG@K / IDCG@K` |
| **Hit Rate** | ≥1 relevant found in top-K | binary |

### Generation Metrics / জেনারেশন মেট্রিক

| Metric | Meaning |
|---|---|
| **Faithfulness** | Answer-এর প্রতিটা claim কি context-এ supported? |
| **Answer Relevance** | Answer কি প্রশ্নের উত্তর দেয়? |
| **Context Relevance** | Retrieved chunks কি প্রশ্নের সাথে relevant? |
| **Citation Accuracy** | Citation কি সঠিক chunk-কে point করে? |
| **Hallucination Rate** | Unsupported claim-এর % |

### Experiment Matrix / পরীক্ষার ম্যাট্রিক্স

```python
# src/evaluation/runner.py
EXPERIMENTS = {
    "A_vector_only":       {"vector": 1.0, "bm25": 0.0, "rerank": False},
    "B_bm25_only":         {"vector": 0.0, "bm25": 1.0, "rerank": False},
    "C_weighted_hybrid":   {"vector": 0.5, "bm25": 0.5, "rerank": False},
    "D_hybrid_rrf":        {"rrf": True, "rerank": False},
    "E_hybrid_rrf_rerank": {"rrf": True, "rerank": True},
}

async def run_experiment(name: str, config: dict, dataset: list[dict]) -> dict:
    results = []
    for item in dataset:
        retrieved = await retrieve(item["question"], config)
        answer = await generate(item["question"], retrieved)
        results.append({
            "recall@10": recall_at_k(retrieved, item["expected_sources"], 10),
            "mrr": mrr(retrieved, item["expected_sources"]),
            "faithfulness": await score_faithfulness(answer, retrieved),
            "citation_accuracy": await score_citations(answer, retrieved),
        })
    return aggregate(results)
```

### Sample Results / নমুনা ফলাফল

| Experiment | Recall@10 | MRR | Faithfulness | Citation Acc |
|---|---|---|---|---|
| A: Vector only | 0.62 | 0.51 | 0.78 | 0.72 |
| B: BM25 only | 0.58 | 0.48 | 0.75 | 0.69 |
| C: Weighted hybrid | 0.71 | 0.60 | 0.83 | 0.79 |
| D: Hybrid + RRF | 0.79 | 0.68 | 0.87 | 0.85 |
| E: + Cross-encoder | **0.86** | **0.74** | **0.92** | **0.90** |

**Interview line:** *"I improved Recall@10 from 0.62 to 0.86 by combining dense + sparse retrieval with RRF and cross-encoder reranking, then verified with a 200-question evaluation set."*

---

# Phase 14 — Hallucination Detection
# ফেজ ১৪ — হ্যালুসিনেশন সনাক্তকরণ

**English:** Post-generation verification — decompose answer into atomic claims, check each against retrieved evidence.

**বাংলা:** Generation-এর পর verification — উত্তরকে atomic claim-এ ভাঙুন, প্রতিটা evidence-এর সাথে মিলান।

```
LLM Answer
    ↓
Claim Extraction (atomic facts)
    ↓
Evidence Matching (NLI / cross-encoder)
    ↓
Support Score per claim
    ↓
If any claim < threshold → FAIL
    ↓
"I couldn't verify this information from the available documents."
```

```python
# src/verification/hallucination.py
async def check_hallucination(answer: str, chunks: list[Chunk]) -> dict:
    claims = await extract_claims(answer)
    results = []
    for claim in claims:
        score = await nli_score(claim, " ".join(c.content for c in chunks))
        results.append({"claim": claim, "support": score})
    unsupported = [r for r in results if r["support"] < 0.5]
    return {
        "total_claims": len(claims),
        "unsupported": len(unsupported),
        "hallucination_rate": len(unsupported) / max(len(claims), 1),
        "details": results,
    }
```

---

# Phase 15 — Conversation Memory
# ফেজ ১৫ — কথোপকথনের মেমোরি

**English:** Multi-turn conversations need context-aware query rewriting — a bare "What about managers?" is meaningless to a retriever.

**বাংলা:** Multi-turn কথোপকথনে context-aware query rewriting দরকার — "What about managers?" retrieve-এর জন্য অর্থহীন।

```
Turn 1:
User: What is the leave policy?
AI: ... (grounded answer with citations)

Turn 2:
User: What about managers?

Query Rewriter:
   "What about managers?" + history →
   "manager leave policy entitlements"

Retriever: ← uses rewritten query
```

```python
# src/memory/conversation.py
from dataclasses import dataclass, field

@dataclass
class Turn:
    role: str
    content: str

@dataclass
class Conversation:
    session_id: str
    turns: list[Turn] = field(default_factory=list)
    max_turns: int = 10
    
    def add(self, role: str, content: str) -> None:
        self.turns.append(Turn(role, content))
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
    
    def rewrite_query(self, new_query: str) -> str:
        """Use LLM to rewrite based on conversation history."""
        # include last 3 turns as context for rewriter
        ...
```

**Context window management:**
- Short-term: last 5 turns verbatim
- Medium-term: summarize earlier turns
- Long-term: semantic memory in vector DB

---

# Phase 16 — Access Control / Enterprise Security
# ফেজ ১৬ — অ্যাক্সেস কন্ট্রোল / এন্টারপ্রাইজ সিকিউরিটি

**English:** The most important enterprise RAG requirement — **never retrieve documents the user isn't authorized to see.** This is enforced at the vector DB level, not post-hoc.

**বাংলা:** সবচেয়ে গুরুত্বপূর্ণ এন্টারপ্রাইজ RAG requirement — **যে ডকুমেন্ট ব্যবহারকারী দেখতে অনুমোদিত নন, তা কখনো retrieve করা যাবে না।** এটি vector DB level-এ enforce করতে হবে, পরে filter করে নয়।

```
User Request
    ↓
Authentication (JWT)
    ↓
Load User Roles/Permissions
    ↓
Build Metadata Filter
   {access_level IN user.allowed_levels,
    department IN user.departments}
    ↓
Filtered Retrieval (vector + BM25)
    ↓
LLM
```

```python
# src/security/rbac.py
from pydantic import BaseModel

class User(BaseModel):
    user_id: str
    roles: list[str]
    departments: list[str]
    clearance: str  # "public" | "internal" | "confidential"

CLEARANCE_LEVELS = ["public", "internal", "confidential"]

def build_access_filter(user: User) -> dict:
    """Returns a filter expression for the vector DB."""
    allowed_levels = CLEARANCE_LEVELS[:CLEARANCE_LEVELS.index(user.clearance) + 1]
    return {
        "must": [
            {"key": "access_level", "match": {"any": allowed_levels}},
            {"key": "department", "match": {"any": user.departments}},
        ]
    }
```

**RBAC rules / RBAC নিয়ম:**

| Role | Access |
|---|---|
| **CEO** | Confidential + HR + Finance |
| **HR Manager** | HR + Public |
| **Employee** | Public only |
| **Finance** | Finance + Public |

**Interview gold:** "How do you ensure an employee doesn't see executive compensation?" — Metadata-based filter enforced at query time in the vector DB; never fetch, never rerank, never send to LLM.

---

Phase 17 — API & Backend Architecture
ফেজ ১৭ — API ও ব্যাকএন্ড আর্কিটেকচার

English: FastAPI with clean layers — routes thin, services do the work, models/schemas separate.

বাংলা: FastAPI with clean layers — routes পাতলা, services কাজ করবে, models/schemas আলাদা।
python

# src/api/v1/endpoints/documents.py
from fastapi import APIRouter, UploadFile, File, status
from src.api.deps import DbSession, CurrentUser, IngestionSvc

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    user: CurrentUser = None,
    svc: IngestionSvc = None,
) -> dict:
    """Queue a document for async ingestion."""
    job_id = await svc.enqueue(file, user)
    return {"job_id": job_id, "status": "queued"}


@router.get("")
async def list_documents(db: DbSession, user: CurrentUser, page: int = 1) -> dict:
    ...

Endpoints / এন্ডপয়েন্ট:
Method	Path	Purpose
POST	/api/v1/documents	Upload & queue ingestion
GET	/api/v1/documents	List user's documents
DELETE	/api/v1/documents/{id}	Soft-delete
POST	/api/v1/search	Retrieval only (no LLM)
POST	/api/v1/chat	Full RAG (retrieval + generation)
GET	/api/v1/conversations/{id}	Fetch history
GET	/api/v1/citations/{chunk_id}	Fetch source metadata
POST	/api/v1/evaluation/run	Run experiment
GET	/api/v1/evaluation/results	View results

Cross-cutting concerns:

    Auth: JWT via fastapi-users

    Rate limiting: slowapi (Redis-backed)

    Pagination: cursor-based for large lists

    Error handling: custom AppError + global handler

    Versioning: /api/v1/ — breaking changes /api/v2/

Phase 18 — Async Processing
ফেজ ১৮ — অ্যাসিনক্রোনাস প্রসেসিং

English: Document ingestion is slow (parsing → chunking → embedding). Don't block the API request.

বাংলা: Document ingestion ধীর (parsing → chunking → embedding)। API request block করা যাবে না।
text

Upload Document
      ↓
API returns 202 + job_id
      ↓
Queue (Redis / RabbitMQ)
      ↓
Worker 1: Parser
      ↓
Worker 2: Chunker
      ↓
Worker 3: Embedder
      ↓
Vector DB write
      ↓
Job status → "completed"

python

# src/jobs/worker.py
import arq
from arq.connections import RedisSettings

async def ingest_document(ctx, job_id: str, file_path: str, user_id: str):
    """Background job — runs in worker process, not API."""
    try:
        doc = parse(file_path)
        chunks = chunk(doc)
        embeddings = await embed_batch([c.content for c in chunks])
        await vector_store.upsert(chunks, embeddings)
        await update_job_status(job_id, "completed")
    except Exception as e:
        await update_job_status(job_id, "failed", error=str(e))
        raise arq.Retry(defer=60)  # retry in 60s


class WorkerSettings:
    functions = [ingest_document]
    redis_settings = RedisSettings()
    max_jobs = 4
    job_timeout = 600

কী কী implement করবেন / What to implement:

    Job queues: ARQ (async) বা Celery (battle-tested)

    Retries: exponential backoff — 3 attempts, then dead-letter

    Dead-letter handling: failed jobs → separate queue for manual inspection

    Progress tracking: WebSocket or polling /jobs/{id}

    Idempotency: job_id-based dedup — same doc can't be ingested twice

Phase 19 — Observability
ফেজ ১৯ — অবজারভেবিলিটি

English: Track every stage of every RAG request. Without tracing, you can't debug production.

বাংলা: প্রতিটা RAG request-এর প্রতিটা stage track করুন। tracing ছাড়া production debug করা যায় না।
Per-Request Trace / প্রতি-রিকোয়েস্ট ট্রেস
json

{
  "request_id": "req_abc123",
  "user_id": "usr_456",
  "query": "What is the leave policy?",
  "stages": {
    "query_rewrite":  {"latency_ms": 145, "tokens": 120},
    "vector_search":  {"latency_ms": 45,  "hits": 20},
    "bm25_search":    {"latency_ms": 12,  "hits": 20},
    "rrf":            {"latency_ms": 3,   "merged": 32},
    "rerank":         {"latency_ms": 210, "candidates": 20, "selected": 5},
    "llm_generation": {"latency_ms": 1200, "prompt_tokens": 3400, "completion_tokens": 180},
    "citation_check": {"latency_ms": 320, "claims": 3, "supported": 3}
  },
  "total_latency_ms": 1935,
  "cost_usd": 0.0087
}

Stack / স্ট্যাক
Concern	Tool
Structured logging	structlog (JSON logs)
Metrics	Prometheus + Grafana
Tracing	OpenTelemetry → Jaeger / Tempo
Error monitoring	Sentry
LLM observability	Langfuse / Phoenix / Helicone
Token/cost tracking	Langfuse (built-in)

Interview Tip: "How do you debug a slow RAG query?" — trace shows per-stage latency; usually it's the reranker (cross-encoder) or LLM generation, not retrieval.
Phase 20 — Production Optimization
ফেজ ২০ — প্রোডাকশন অপটিমাইজেশন

English: Before/after measurements make the optimization work visible.

বাংলা: আগে/পরে measurement থাকলে optimization-এর প্রভাব স্পষ্ট হয়।
Optimization Checklist / অপটিমাইজেশন চেকলিস্ট
Optimization	Before	After
Embedding cache (Redis)	200ms per chunk	5ms cache hit
Query cache	200ms	3ms
Batch embeddings	100 req × 100ms = 10s	1 req × 500ms
Connection pooling	New conn per req	Reused pool
Async I/O	Sequential 800ms	Parallel 250ms
Streaming responses	Wait 3s for full answer	Start at 300ms
Rate limiting	Crashed under load	Smooth 429s
Retry + backoff	Hard failures	Graceful recovery
Timeout handling	Hung requests	30s timeout
Sample Measurement / নমুনা পরিমাপ
text

Before optimization:
  P50 = 3200 ms    P95 = 8900 ms    Cost = $0.021/query

After:
  P50 = 850 ms     P95 = 2100 ms    Cost = $0.007/query

Improvement:
  Latency ↓ 73%    Cost ↓ 67%

Interview line: "I reduced P95 latency from 8.9s to 2.1s by caching embeddings, batching vector writes, and streaming LLM responses."
Phase 21 — Production Architecture (Final)
ফেজ ২১ — চূড়ান্ত প্রোডাকশন আর্কিটেকচার
text

                         ┌─────────────────┐
                         │   Frontend      │  (Next.js / Streamlit)
                         └────────┬────────┘
                                  │ HTTPS + JWT
                                  ▼
                         ┌─────────────────┐
                         │   API Gateway   │  (FastAPI + rate limit)
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  Auth / RBAC    │  (fastapi-users)
                         └────────┬────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    RAG Orchestrator       │
                    │    (service layer)        │
                    └─────────────┬─────────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ Query Understanding │  (rewrite, expand)
                       └──────────┬──────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
          ┌──────────────┐                 ┌──────────────┐
          │ Vector Search│                 │  BM25 Search │
          │  (Qdrant)    │                 │(OpenSearch)  │
          └──────┬───────┘                 └──────┬───────┘
                 │                                │
                 └──────────────┬─────────────────┘
                                ▼
                         ┌─────────────┐
                         │     RRF     │
                         └──────┬──────┘
                                ▼
                       ┌─────────────────┐
                       │ Cross Encoder   │
                       │   Re-Ranker     │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │ Context Builder │
                       │ (dedupe + fit)  │
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │       LLM       │  (GPT-4o / Claude)
                       └────────┬────────┘
                                ▼
                       ┌─────────────────┐
                       │ Citation Check  │
                       │ + Hallucination │
                       └────────┬────────┘
                                ▼
                           Final Answer
                                │
                                ▼
                       ┌─────────────────┐
                       │  Observability  │  (Langfuse + OTel)
                       └─────────────────┘

Component Inventory / কম্পোনেন্ট তালিকা
Layer	Tech	Why
Frontend	Next.js / Streamlit	UI
API	FastAPI	Async, typed
Auth	fastapi-users	JWT ready
Vector DB	Qdrant / Weaviate	Payload filtering
Sparse index	OpenSearch / Elasticsearch	BM25 at scale
Embeddings	text-embedding-3-large	Best quality
Reranker	bge-reranker-v2-m3	Self-hostable
Cache	Redis	Embedding + query cache
Queue	ARQ / Celery	Async ingestion
LLM	GPT-4o / Claude	Generation
Observability	Langfuse + OTel	Trace + cost
Deployment	Docker + K8s	Scale
Recommended Learning Progression
প্রস্তাবিত শেখার ক্রম

English: Don't build everything at once. Each phase is a self-contained project you can demo.

বাংলা: সব একসাথে বানাবেন না। প্রতিটা phase আলাদা প্রজেক্ট — আলাদাভাবে demo করা যায়।
text

Phase 1   → Document ingestion              ← Basic ETL
Phase 2   → Chunking + embeddings           ← Data prep
Phase 3   → Vector search                   ← Semantic retrieval
Phase 4   → BM25                            ← Keyword retrieval
Phase 5   → Hybrid Search                   ← Combine both
Phase 6   → RRF                             ← Rank fusion
Phase 7   → Cross Encoder                   ← Accuracy boost
Phase 8   → Query Understanding             ← Better queries
Phase 9   → Context Selection               ← Token budget
Phase 10  → Grounded Generation             ← Faithful answers
Phase 11  → Citations                       ← Source traceability
Phase 12  → Citation Verification           ← Trust but verify
Phase 13  → RAG Evaluation                  ← Measurable quality  ⭐
Phase 14  → Hallucination Detection         ← Safety
Phase 15  → Conversation Memory             ← Multi-turn
Phase 16  → RBAC / Security                 ← Enterprise grade    ⭐
Phase 17  → API & Backend                   ← Production API
Phase 18  → Async Processing                ← Scale
Phase 19  → Observability                   ← Debuggability
Phase 20  → Optimization                    ← Speed + cost
Phase 21  → Production Architecture         ← Final system

Priority for interviews / ইন্টারভিউর জন্য অগ্রাধিকার:

⭐⭐⭐ Must-have: Phase 3, 4, 5, 6, 7, 10, 11, 13, 16
⭐⭐ Nice-to-have: Phase 1, 2, 8, 9, 12, 14, 15, 17
⭐ Bonus: Phase 18, 19, 20, 21

