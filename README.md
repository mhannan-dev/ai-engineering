# AI Engineering Master Repository

A production-grade collection of real-world AI Engineering projects and core foundational concepts, demonstrating modern LLM orchestration, structured outputs, agentic systems, and multi-modal intelligence.

---

## 🛠️ Global Environment Setup

### 1. Prerequisites & Installation
Ensure Python 3.10+ is installed on your system. Run from the workspace root:

```bash
# Install core dependencies
pip install -r requirements.txt

# Install Playwright browser binary (Chromium)
python -m playwright install chromium
```

### 2. Environment Variables Configuration
Copy [.env.example](file:///e:/DockerProjects/saaa_rag_product/ai-engineering/.env.example) to `.env`:

```bash
cp .env.example .env
```

Open `.env` and configure your preferred LLM provider:

```env
# Option A: DeepSeek API (High Performance & Cost Effective)
OPENAI_API_KEY="your-deepseek-api-key"
OPENAI_BASE_URL="https://api.deepseek.com"
LLM_MODEL="deepseek-chat"

# Option B: Official OpenAI API
# OPENAI_API_KEY="your-openai-api-key"
# LLM_MODEL="gpt-4o-mini"
```

### 3. Verify Environment Readiness
Run the environment verification script to ensure all packages, models, and keys are properly detected:

```bash
python verify_env.py
```

---

## 📁 Projects Index & How to Run

| Project | Name | Core Tech Stack | Status |
| :--- | :--- | :--- | :--- |
| **P1** | [Enterprise Brochure Generator](#-project-1-enterprise-brochure-generator) | Crawl4AI, Playwright, Instructor, Pydantic v2, Tailwind CSS v3 | **Complete & Verified** |
| **P2** | [Airline Multi-Agent Customer Support](#-project-2-airline-multi-agent-system) | LiteLLM, LangGraph / Multi-Agent, Tool Calling | *In Development* |
| **P3** | [Meeting Intelligence SaaS](#-project-3-meeting-intelligence-saas) | FastAPI, Next.js, Faster-Whisper, Deepgram, LiteLLM + Instructor | *In Development* |
| **P4** | [High-Performance Code Transpiler](#-project-4-high-performance-code-transpiler) | FastAPI, Next.js, g++ C++20, OpenMP, LLM self-correction | **Complete** |

---

## 🚀 Project 1: Enterprise Brochure Generator

### 📌 Overview
An automated B2B intelligence and marketing system that crawls dynamic JavaScript single-page apps (SPAs), discovers deep internal business links (`/about`, `/pricing`, `/products`), removes 60–80% boilerplate noise, and generates 100% type-safe executive brochures using **Instructor**, **Pydantic v2**, and **Tailwind CSS v3**.

### 💻 How to Run

#### Method A: From the Root Directory (Recommended)
```powershell
# Basic execution (defaults to 5 pages with configured LLM)
python -m projects.p1_brochure_generator.main https://stripe.com

# Custom sub-pages and specific model
python -m projects.p1_brochure_generator.main https://stripe.com --pages 3 --model deepseek-chat
```

#### Method B: From the Project Subdirectory
```powershell
# Navigate into the project folder
cd projects/p1_brochure_generator

# Run directly
python main.py https://stripe.com --pages 3
```

### 📂 Generated Outputs
Every run automatically outputs three production-ready artifacts in `projects/p1_brochure_generator/output/`:
1. **`.json` File:** 100% type-safe, validated Pydantic JSON structure for databases & APIs.
2. **`.md` File:** Executive Markdown summary document with offerings and ICP.
3. **`.html` File:** Fully responsive, interactive Tailwind CSS v3 web brochure with dynamic category filtering and instant **Print / PDF export**.

👉 Detailed architectural documentation: [projects/p1_brochure_generator/README.md](file:///e:/DockerProjects/saaa_rag_product/ai-engineering/projects/p1_brochure_generator/README.md)

---

## ✈️ Project 2: Airline Multi-Agent System

### 📌 Overview
An enterprise customer support multi-modal agent architecture handling boarding pass parsing, flight lookups, deterministic refund calculations, and 2FA-gated cancellations with structured tool calling and an interactive Streamlit UI.

### 💻 How to Run

#### Method A: From the Root Directory (Recommended)
```powershell
python -m streamlit run projects/p2_airline_agent/airline_main_agent.py
```

#### Method B: From the Project Subdirectory
```powershell
cd projects/p2_airline_agent
streamlit run airline_main_agent.py
```

👉 Detailed architectural documentation & test scenarios: [projects/p2_airline_agent/README.MD](file:///e:/DockerProjects/saaa_rag_product/ai-engineering/projects/p2_airline_agent/README.MD)

---

## 🎙️ Project 3: Meeting Intelligence SaaS

### 📌 Overview
Upload a meeting recording and get structured minutes: summary, decisions, and action items. Confidential audio is transcribed locally with Faster-Whisper; everything else goes to Deepgram. A FastAPI backend (JWT auth, Alembic) and a Next.js frontend.

### 💻 How to Run
```powershell
cd projects/p3_meeting_intelligence_saas
.un.ps1 -Install
.un.ps1 -Migrate
.un.ps1
```

👉 Detailed documentation: [projects/p3_meeting_intelligence_saas/README.md](projects/p3_meeting_intelligence_saas/README.md)

---

## ⚡ Project 4: High-Performance Code Transpiler

### 📌 Overview
Converts numerical Python into C++20 with OpenMP, builds it with g++, feeds compiler errors back to the LLM until it builds, then benchmarks Python vs C++ and checks the outputs match.

### 💻 How to Run
Requires g++ with C++20 and OpenMP (on Windows: `scoop install mingw`).
```powershell
cd projects/p4_code_transpiler
.un.ps1 -Install
.un.ps1            # API :8000 + UI :3000
```

👉 Detailed documentation & sample results: [projects/p4_code_transpiler/README.md](projects/p4_code_transpiler/README.md)

---

## 🛡️ Git Security Rules
- `.env` and all secret credentials are automatically excluded by [.gitignore](file:///e:/DockerProjects/saaa_rag_product/ai-engineering/.gitignore).
- Cached output files (`**/output/`), browser reports (`.crawl4ai/`, `playwright-report/`), and bytecode (`**/__pycache__/`) are never committed to GitHub.
