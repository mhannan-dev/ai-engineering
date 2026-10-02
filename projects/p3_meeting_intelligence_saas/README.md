# Project 3: Hybrid Audio Meeting Minutes & Action Items Engine (p3_meeting_intelligence_saas)

A production-grade meeting intelligence system featuring a modern **Next.js** frontend and an asynchronous **FastAPI** backend designed with **Layered Architecture**. The engine provides hybrid audio transcription routing (Local **Faster-Whisper** vs. Cloud **Deepgram**) and map-reduce LLM minutes synthesis (**LiteLLM** + **Instructor**).

---

## 🏗️ System Architecture Flow

```
[User Browser (Next.js App)]
        │
        ├─► 1. File Upload (.mp3 / .wav) + Sensitivity Flag
        │
        ▼
[FastAPI Async Backend]
        │
        ├─► 2. Save Temporary File / Read Audio Stream
        ├─► 3. Audio Transcription Engine
        │       ├── Confidential ──► Local faster-whisper (CPU, int8, VAD)
        │       └── Public       ──► Cloud Deepgram API
        │
        ├─► 4. Map-Reduce Chunking & LLM Synthesis (LiteLLM + Instructor)
        │
        ▼
[Validated Structured JSON (Pydantic Schema)]
        │
        └─► 5. Return Structured Response to Next.js Client
```

---

## 🌟 Core Features

1. **Hybrid Sensitivity-Based Audio Routing:**
   - **Confidential Recordings:** Processed entirely on-premises using `faster-whisper` (CPU int8 with Voice Activity Detection - VAD) to guarantee zero data leakage.
   - **Public Recordings:** Routed to Cloud `Deepgram API` for high-concurrency, low-latency transcription.

2. **Map-Reduce LLM Synthesis with Pydantic & Instructor:**
   - Long meetings are chunked and synthesized into structured meeting minutes.
   - Outputs strict, type-safe JSON schema including executive summaries, categorized discussion points, decisions made, and assigned action items with deadlines and priority levels.

3. **Production Layered Architecture:**
   - Clean separation of concerns across Configuration, Presentation (API/Routers), Business Logic (Services), Domain Models, Data Transfer Objects (Schemas), and Persistence (Repositories/Database).

4. **Next.js Interactive Dashboard:**
   - Audio uploader with progress tracking, visual sensitivity toggle, rich markdown minutes rendering, and actionable task management table.

---

## 📂 Project Structure

```
p3_meeting_intelligence_saas/
├── README.md
├── web/                                   # Next.js Frontend Application
│   ├── app/                               # App router pages (page.tsx, layout.tsx, dashboard/)
│   ├── components/                        # UI components (audio-uploader, mom-display, action-items-table)
│   ├── lib/                               # API client and TypeScript data types (api.ts)
│   └── package.json
└── api/                                   # FastAPI Async Backend (Layered Architecture)
    ├── pyproject.toml                     # Python dependencies & tooling (pytest, ruff)
    ├── .env.example                       # Sample environment variables
    ├── .env                               # Active configuration settings
    ├── main.py                            # Runner entrypoint (delegates to app factory)
    ├── print_routes.py                    # CLI utility to inspect all registered API endpoints
    ├── src/
    │   └── meeting_intelligence/          # Core Python Package
    │       ├── main.py                    # FastAPI application factory (create_app)
    │       ├── config.py                  # Pydantic Settings singleton (get_settings)
    │       ├── api/
    │       │   ├── deps.py                # Shared dependencies (get_db, get_current_user, services)
    │       │   └── v1/
    │       │       ├── router.py          # Aggregated v1 API router
    │       │       └── endpoints/
    │       │           ├── health.py      # Health & echo diagnostic endpoints
    │       │           ├── auth.py        # User login & JWT token generation
    │       │           ├── users.py       # User management endpoints
    │       │           └── meetings.py    # Multipart audio upload, routing & minutes
    │       ├── core/
    │       │   ├── security.py            # Password hashing & JWT token verification
    │       │   └── exceptions.py          # Custom exceptions & global exception handlers
    │       ├── models/                    # Domain entities (User, Meeting, ActionItemRecord)
    │       ├── schemas/                   # Pydantic DTOs (MeetingMinutes, ActionItem, User, Health)
    │       ├── services/                  # Business logic (TranscriptionService, SynthesisService, UserService)
    │       └── db/                        # Repository pattern & session management
    └── tests/                             # Automated Test Suite (15+ unit & integration tests)
        ├── conftest.py                    # Fixtures (clean_database, client, auth_headers)
        ├── api/                           # Endpoint integration tests (health, auth, users, meetings)
        └── services/                      # Service layer unit tests (transcription routing, user auth)
```

---

## 🚀 Getting Started

### 1. Backend Setup (`api/`)

Ensure you have Python 3.12+ and `uv` installed:

```powershell
# Navigate to the backend directory
cd projects/p3_meeting_intelligence_saas/api

# Sync virtual environment and install dependencies
uv sync

# Run the development server (auto-reloading)
uv run fastapi dev main.py
```
Backend will be live at `http://localhost:8000` (Interactive Swagger Docs: `http://localhost:8000/docs`).

#### Useful Backend Commands:

- **Inspect all registered routes in console:**
  ```powershell
  uv run python print_routes.py
  ```
- **Execute test suite:**
  ```powershell
  uv run pytest
  ```
- **Lint and format code:**
  ```powershell
  uv run ruff check .
  ```

---

### 2. Frontend Setup (`web/`)

In a separate terminal:

```powershell
# Navigate to the web frontend directory
cd projects/p3_meeting_intelligence_saas/web

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 📡 Registered API Endpoints

| Method | Path | Summary / Description |
|---|---|---|
| `GET` | `/` | Root service health check & version info |
| `GET` | `/health` | Service health status and version info |
| `POST` | `/echo` | Connectivity probe echo endpoint |
| `POST` | `/api/process-audio` | Direct audio upload & hybrid synthesis (Next.js compatible) |
| `POST` | `/api/v1/meetings/process-audio` | Audio upload endpoint (`v1` versioned) |
| `GET` | `/api/v1/meetings/` | List all processed meeting minutes |
| `GET` | `/api/v1/meetings/{meeting_id}` | Retrieve specific meeting minutes by ID |
| `POST` | `/api/v1/auth/login` | User authentication & Bearer token generation |
| `POST` | `/api/v1/users/` | Register new user account |
| `GET` | `/api/v1/users/me` | Fetch authenticated user profile |
| `GET` | `/api/v1/users/` | List registered accounts (authenticated) |

---

## ⚙️ Environment Configuration

| Variable | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `Meeting Intelligence API` | API display title in OpenAPI docs |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `testing`, `production`) |
| `SECRET_KEY` | *(dev secret)* | Cryptographic key for JWT token signing |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins for Next.js app |
| `WHISPER_MODEL_SIZE` | `base` | Model size for local faster-whisper |
| `WHISPER_DEVICE` | `cpu` | Execution device (`cpu` or `cuda`) |
| `WHISPER_COMPUTE_TYPE`| `int8` | Model quantization (`int8`, `float16`) |
| `DEEPGRAM_API_KEY` | *(optional)* | API key for cloud Deepgram transcription |
| `LITELLM_MODEL` | `gpt-4o-mini` | Default LLM model identifier for minutes synthesis |
| `OPENAI_API_KEY` | *(optional)* | OpenAI API key for LiteLLM provider |
