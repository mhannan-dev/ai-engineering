# Multi-Modal Airline Customer Support Agent (`p2_airline_agent`)

[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20Layered-blue.svg)](docs/architecture.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)](pyproject.toml)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-orange.svg)](https://docs.pydantic.dev/)

An enterprise-grade, bilingual (বাংলা / English) multi-modal AI customer support agent for airlines. Built with **Clean Architecture**, **GPT-4o Vision OCR**, **LiteLLM tool calling**, **Instructor + Pydantic v2**, **deterministic business arithmetic**, **2FA-gated cancellations**, and an interactive **Streamlit** user interface.

---

## 🏗️ Layered Project Structure (`src/` Layout)

```
p2_airline_agent/
├── pyproject.toml              # Build system, pytest, ruff, mypy configs
├── requirements.txt            # Dependency list
├── .env.example                # Environment variables template
├── .gitignore                  # Git exclusions
├── README.md                   # Project documentation
├── src/
│   └── airline_agent/
│       ├── __init__.py         # Public API entry point
│       ├── __main__.py         # CLI execution entry point
│       ├── config/             # Runtime configuration
│       │   ├── __init__.py
│       │   ├── settings.py     # Typed Settings dataclass
│       │   └── prompts.py      # System prompts & injection regexes
│       ├── domain/             # Pure Enterprise Business Rules
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic v2 domain models
│       │   ├── database.py     # Transactional mock repository
│       │   └── business.py     # Deterministic refund math & 2FA rules
│       ├── services/           # Application Services & Orchestration
│       │   ├── __init__.py
│       │   ├── agent_service.py# LLM reasoning loop & sanitizer
│       │   ├── vision_service.py # Boarding pass vision extraction
│       │   └── tools.py        # Tool caller schemas & dispatcher
│       ├── infra/              # External Adapters & Drivers
│       │   ├── __init__.py
│       │   ├── llm_client.py   # LiteLLM & Instructor wrapper (Protocol)
│       │   └── audit_log.py    # Append-only audit logger (Protocol)
│       └── ui/                 # Presentation Layer
│           ├── __init__.py
│           ├── app.py          # Streamlit application lifecycle
│           └── components.py   # Reusable UI visual components
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_business.py    # 5 test cases for deterministic refund logic
│   │   ├── test_models.py      # Pydantic v2 schema tests
│   │   └── test_tools.py       # Tool execution & 2FA tests
│   ├── integration/
│   │   └── test_agent_loop.py  # Mocked agent reasoning loop integration
│   └── fixtures/
│       └── sample_boarding_pass.png
├── scripts/
│   ├── seed_db.py              # Database seed inspector
│   ├── run_streamlit.ps1       # One-click Streamlit launcher
│   └── migrate.ps1             # Migration utility from legacy flat structure
└── docs/
    └── architecture.md         # Detailed Clean Architecture design spec
```

---

## 🔒 Layering Rules (Strict Compliance)

1. **Dependency Direction:** `ui` → `services` → `domain`
2. **`domain/`** has **zero external dependencies** except `pydantic`.
3. **`services/`** orchestrates domain operations and interfaces with `infra/` strictly through **Protocols (`LLMClientProtocol`, `AuditLoggerProtocol`)**.
4. **`ui/`** imports **`services/` only** — never touches `domain/` or `infra/` directly.

---

## 🚀 Quickstart & How to Run

### 1. Installation
Activate your virtual environment and install dependencies:

```powershell
pip install -r requirements.txt
```

Or install in editable mode:

```powershell
pip install -e .
```

### 2. Environment Configuration
Copy `.env.example` to `.env` in the repository root or project folder:

```env
OPENAI_API_KEY="your-api-key"
OPENAI_BASE_URL="https://api.deepseek.com"
LLM_MODEL="deepseek-chat"
VISION_MODEL="openai/gpt-4o"
```

### 3. Launch Streamlit UI

#### From Project Directory:
```powershell
streamlit run src/airline_agent/ui/app.py
```

#### Or using the PowerShell Script:
```powershell
.\scripts\run_streamlit.ps1
```

#### Or via Root Workspace:
```powershell
python -m streamlit run projects/p2_airline_agent/src/airline_agent/ui/app.py
```

---

## 🧪 Running the Test Suite

Execute the unit and integration tests with coverage:

```powershell
pytest
```

Run specific unit tests:

```powershell
pytest tests/unit/test_business.py -v
```

---

## 📦 Public Python API

The agent can be imported directly into any FastAPI or backend service:

```python
from airline_agent import execute_agent_loop, parse_boarding_pass_vision

# 1. Run multi-turn agent reasoning loop
messages = [{"role": "user", "content": "What are the details for PNR ABC123?"}]
reply = execute_agent_loop(messages)
print(reply)

# 2. Extract structured fields from boarding pass image bytes
with open("tests/fixtures/sample_boarding_pass.png", "rb") as f:
    ticket = parse_boarding_pass_vision(f.read())
    print(f"Passenger: {ticket.passenger_name}, PNR: {ticket.pnr}")
```
