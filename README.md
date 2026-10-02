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

## 🛡️ Git Security Rules
- `.env` and all secret credentials are automatically excluded by [.gitignore](file:///e:/DockerProjects/saaa_rag_product/ai-engineering/.gitignore).
- Cached output files (`**/output/`), browser reports (`.crawl4ai/`, `playwright-report/`), and bytecode (`**/__pycache__/`) are never committed to GitHub.
