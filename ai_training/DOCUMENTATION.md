# ISKRA Smart Meter Intelligence Platform — Conversational L1 AI Support Agent

## 1. Architecture Overview

The ISKRA Smart Meter L1 Support Agent is a conversational, grounded AI support system that assists customers in troubleshooting electric, water, and ultrasonic smart meters without subjecting them to a rigid form or questionnaire.

```
                      CUSTOMER MESSAGE
                             │
                             ▼
                 CONVERSATION MANAGER
               (ConversationManager)
                             │
                             ▼
                        AGENT BRAIN
                         (L1Agent)
                ┌────────────┴────────────┐
                ▼                         ▼
           CASE MEMORY             INTENT DETECTION
           (CaseMemory)            (IntentDetector)
                │                         │
                └────────────┬────────────┘
                             │
                             ▼
                      DECISION ENGINE
                      (DecisionEngine)
          ┌──────────────┬───┴──────────┬──────────────┐
          ▼              ▼              ▼              ▼
        ANSWER          RAG            ASK          ESCALATE
          │              │              │              │
          └──────────────┼──────────────┴──────────────┘
                         │
                         ▼
                 VERIFIED EVIDENCE
            (HybridRetriever & Exact Search)
                         │
                         ▼
                RESPONSE GENERATION
                (ResponseGenerator)
                         │
                         ▼
                   FINAL RESPONSE
```

---

## 2. Agent Conversational Flow

Unlike legacy support bots that insist on a fixed questionnaire (forcing the user to provide Meter Type, Model, System, Error Code, and Scenario upfront), this system treats case fields as **optional case facts**:

1. **Understand & Extract:** The user's input is parsed naturally for facts (system name, meter type, model, error code, scenario, symptoms) in English, Arabic, Egyptian Arabic, or mixed technical language.
2. **Multi-Turn Accumulation:** Facts are merged into `CaseState` without discarding previously learned information.
3. **Intent Detection:** Customer intent is identified (e.g. `troubleshooting`, `error_explanation`, `identification`, `follow_up`, `escalation`, `status_question`).
4. **Knowledge Retrieval:** ChromaDB vector search and exact line matching look up verified documentation in `MT514 Meter Pages & Meter Errors.pdf`. Duplicates from chunk overlap are automatically removed.
5. **Decision Engine:**
   - If the user asks a direct question (e.g. *"What is Error 70?"*), the agent answers directly without asking for meter model or system.
   - If information is missing and genuinely necessary for the next troubleshooting action, the agent asks **at most ONE targeted question**.
   - If the user expresses that they don't know a field (e.g. *"مش عارف الموديل"* / *"I don't know the model"*), the agent marks the field in `user_does_not_know`, acknowledges gracefully, and continues without repeating the question.
6. **Grounding & Safety:** Technical answers are strictly grounded in retrieved evidence. No root causes or troubleshooting fixes are invented. If no procedure is in verified documents, the case is recommended for L2 escalation.

---

## 3. Structured Case Memory

The agent maintains an explicit, persistent case memory across multi-turn interactions:

```python
case_state = {
    "intent": "troubleshooting",
    "issue": "account opening failure",
    "meter_type": "Electric",
    "meter_model": "MT514",
    "system": "Vending",
    "error_code": "70",
    "error_message": None,
    "scenario": "account opening",
    "known_facts": {
        "system": "Vending",
        "error_code": "70",
        "scenario": "account opening"
    },
    "unknown_facts": [],
    "user_does_not_know": ["meter_model"],
    "conversation_summary": "Issue: account opening failure | System: Vending | Error Code: 70",
    "last_user_message": "...",
    "last_agent_message": "...",
    "last_question": None,
    "last_question_field": None,
    "evidence": [...],
    "confidence": 0.95,
    "issue_category": "Software",
    "l1_status": "Needs L2",
    "routing": "L2 Software"
}
```

- `null` is a valid value for any field. Missing information does not block the conversation.
- `user_does_not_know` prevents the agent from re-asking for fields the user cannot provide.

---

## 4. RAG Integration & Exact Error Code Retrieval

The retrieval engine (`HybridRetriever`) combines:
1. **Direct Line-Based Error Code Search (`DirectErrorSearcher`):** Scans document chunks for exact error code patterns (`^\s*0*<code>\s+` or `error code <code>`) to retrieve exact error definitions (e.g. `70 The lead seal button is not be pressed`, `96 The firmware of old meter is too old`).
2. **Dense Semantic Search:** Uses SentenceTransformers (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) against the ChromaDB collection `iskra_knowledge`.
3. **Deduplication (`deduplicate_evidence`):** Removes duplicate chunks created by chunk overlap, ensuring each unique matched evidence line is reported once.
4. **Singleton Initialization:** The embedding model and ChromaDB client are loaded once at startup to guarantee fast multi-turn responses.

---

## 5. Intent Detection

The `IntentDetector` classifies customer messages into 8 distinct intents:
- `troubleshooting`: Active meter issue or malfunction reported.
- `error_explanation`: Direct questions inquiring about an error code meaning (e.g. *"What is Error 70?"*, *"ما معنى كود 70؟"*).
- `general_question`: Greetings or broad inquiries (*"Can you help me?"*).
- `identification`: Queries on how or where to locate meter attributes (*"Where can I find the model?"*).
- `follow_up`: Continuation messages (*"same problem"*, *"still not working"*, *"I checked the power"*).
- `escalation`: Explicit requests for human or tier-2 support (*"Send this to L2"*, *"حولني لمهندس"*).
- `status_question`: Ticket status queries (*"What is the status of my ticket?"*).
- `other`: General conversation or acknowledgment (*"OK"*, *"شكرا"*).

---

## 6. L1 Decision Engine & Category Classification

### A. Issue Category
Classified conservatively into:
- `Software`: Vending, Billing, Symbiot, MeterVerse, Aqua, account opening, login, database errors.
- `Hardware`: Broken screen, damaged casing, relay failure, no power, battery faults.
- `Firmware`: Firmware version mismatch, firmware update failures, old firmware.
- `Communication`: RS485, RS232, Modbus, DLMS/COSEM, connection drops, HDLC errors.
- `Unknown`: Insufficient information to classify.

### B. Knowledge Status
- `Verified Knowledge Available`: Exact error code documentation retrieved.
- `Partial Knowledge`: Relevant semantic chunks found without exact match.
- `No Verified Knowledge`: No matching documentation found.

### C. Resolution Status & Error Separation
Knowing the **meaning** of an error is strictly separated from knowing its **resolution**:
- For Error 70, the meaning is verified: *"70 The lead seal button is not be pressed"*.
- However, because the ISKRA documents do not contain an approved L1 repair procedure, `l1_status` is set to `Needs L2`. The agent never falsely claims *"Problem solved"* or hallucinates a repair procedure.

### D. Routing Rules
Configured in `config.py`:
- `Software` ➔ `L2 Software`
- `Hardware` ➔ `L2 Hardware`
- `Firmware` ➔ `L2 Firmware`
- `Communication` ➔ `L2 Software` (Configurable default)
- `Unknown` ➔ `L1 Review`

---

## 7. Safety Rules & Prompt Injection Defense

`SafetyGuard` shields the assistant:
- **Jailbreak Defenses:** Detects and blocks prompts such as *"ignore instructions"*, *"tell me your system prompt"*, *"invent a fake solution"*, and Arabic equivalents.
- **Output Sanitization:** Strips internal `<think>...</think>` tags and reasoning artifacts emitted by reasoning models such as `granite4.2:8b`.
- **JSON Recovery:** Recovers structured data safely from LLM outputs even if malformed or wrapped in markdown fences.

---

## 8. Running the Support Agent

To launch the interactive CLI:

```powershell
python ai_training/scripts/13_agent_brain.py
```

### Supported Interactive Commands:
- `reset` / `new`: Clears current session memory and starts a fresh case.
- `state` / `debug`: Displays internal structured case state diagnostics.
- `exit` / `quit`: Closes the application.

### Legacy RAG Script Compatibility:
The legacy script `12_ollama_rag.py` has been updated to remove the blocking questionnaire loop while preserving its underlying vector search and Ollama prompt pipeline:

```powershell
python ai_training/scripts/12_ollama_rag.py
```

---

## 9. Running Automated Tests

All tests use Python's built-in `unittest` runner.

### Run All 39 Automated Tests:
```powershell
python -m unittest discover -s ai_training/tests -p "test_*.py" -v
```

### Run Unit Tests (21 Tests):
```powershell
python -m unittest ai_training/tests/test_agent.py -v
```

### Run Multi-Turn Conversational Tests (18 Test Cases including Tests A-H):
```powershell
python -m unittest ai_training/tests/test_conversations.py -v
```

### Run Manual Conversational Verification (5 Core Dialogues):
```powershell
python ai_training/scripts/verify_manual_conversations.py
```

### Run Hybrid Retrieval Regression Test:
```powershell
python -c "from ai_training.rag.retriever import HybridRetriever; r = HybridRetriever(); print(r.search('Error 70', error_code='70')); print(r.search('Error 96', error_code='96'))"
```

---

## 10. Adding New Knowledge Documents

1. Place new PDF files in `ai_training/data/knowledge/` (e.g. `AM550_User_Manual.pdf`).
2. Run the knowledge base builder:
   ```powershell
   python ai_training/scripts/10_build_knowledge_base.py
   ```
3. Test retrieval:
   ```powershell
   python ai_training/scripts/11_test_retrieval.py
   ```

---

## 11. Configuring Ollama

Central configuration is maintained in `ai_training/agent/config.py`:
- `OLLAMA_URL`: Default `http://localhost:11434/api/generate` (override via env var `OLLAMA_URL`).
- `OLLAMA_MODEL`: Default `granite4.2:8b` (override via env var `OLLAMA_MODEL`).
- `OLLAMA_TIMEOUT`: Default `120` seconds (override via env var `OLLAMA_TIMEOUT`).
- `OLLAMA_TEMPERATURE`: `0.0` for deterministic, grounded outputs.
- `OLLAMA_MAX_TOKENS`: `350` tokens.

If Ollama is offline or times out, the agent automatically falls back to verified deterministic templates without crashing.

---

## 12. Known Limitations & Terminology Clarification

1. **RAG vs Training:** This platform is a **Conversational L1 AI Support Agent with Knowledge Retrieval (RAG)**. The model (`granite4.2:8b`) is not fine-tuned on ISKRA data; all domain facts are dynamically retrieved from verified PDFs in ChromaDB and exact line tables.
2. **Resolution Procedures:** The current knowledge base (`MT514 Meter Pages & Meter Errors.pdf`) defines error codes and display registers, but does not provide exhaustive step-by-step physical repair procedures. Escalation to L2 is properly recommended when procedures are not verified.
