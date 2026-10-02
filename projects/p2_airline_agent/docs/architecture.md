# Clean Architecture Specification: Airline Customer Support Agent

## 1. Architectural Philosophy

This project strictly adheres to **Clean Architecture** principles and the **Dependency Inversion Principle (DIP)**.

```
       +---------------------------------------------+
       |             UI (Presentation)               |
       |  - Streamlit Web App                        |
       |  - Visual Components                        |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |             Services (Application)          |
       |  - Agent Loop Orchestration                 |
       |  - Deterministic Tool Coordination          |
       |  - Vision Extraction Service                |
       +---------------------------------------------+
                       /              \
                      /                \
                     v                  v
+------------------------+      +---------------------------+
|    Domain (Enterprise)  |      |   Infrastructure (Drivers)|
| - Pure Business Math   |      | - LiteLLM / Instructor    |
| - Value Models         |      | - PIL Image Verification  |
| - Transactional DB     |      | - Immutable Audit Logger  |
+------------------------+      +---------------------------+
```

---

## 2. Layering Rules & Boundaries

| Layer | Responsibility | Allowed Imports | Forbidden Imports |
| :--- | :--- | :--- | :--- |
| **`domain/`** | Core business logic, pricing math, data validation rules, database state. | Standard library, `pydantic`. | `services/`, `ui/`, `infra/`, `config/`, and all external libraries. |
| **`infra/`** | External drivers, SDK wrappers (`litellm`, `instructor`, `PIL`), audit logging sinks. | Standard library, `litellm`, `instructor`, `PIL`, `pydantic`. | `ui/`, `services/`. Exposes ABCs/Protocols to services. |
| **`services/`**| Business orchestration, reasoning loops, tool calling, OCR pipelines. | `domain/`, `infra/` (via Protocols), `config/`. | `ui/`. |
| **`ui/`** | Presentation controllers, Streamlit components, state management. | `services/`, `streamlit`. | `domain/`, `infra/` directly. |
| **`config/`**| Environment variables, runtime parameters, system prompt templates. | Standard library, `dotenv`. | `domain/`, `ui/`. |

---

## 3. Key Design Decisions

1. **Protocol-Driven Infrastructure:** Services depend on `LLMClientProtocol` and `AuditLoggerProtocol`. This enables seamless mocking in unit tests without live API calls.
2. **Zero-LLM Financial Arithmetic:** All cancellation fee percentages and refund balances are calculated using domain arithmetic (`domain/business.py`).
3. **Idempotency Guard & 2FA Gate:** Destructive state mutations require exact matching verification tokens and refuse duplicate cancellations.
4. **Prompt Injection Sanitization:** Redaction regex rules run before LLM processing.
