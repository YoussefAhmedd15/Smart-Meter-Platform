# Smart Meter Intelligence Platform - Architectural Specification

## Architecture Principles
The **Smart Meter Intelligence Platform** provides an end-to-end telemetry, testing automation, failure intelligence, and RAG AI assistant layer surrounding standard **Gurux DLMS Python** protocol stacks for Iskraemeco smart meters.

```text
+-----------------------------------------------------------------------+
|                   REACT INDUSTRIAL DASHBOARD (Vite)                   |
|  - Executive Dashboard           - Live Meter Telemetry               |
|  - Automated Testing Center      - Failure Intelligence RAG Assistant |
|  - Firmware Regression Center    - Knowledge Base & Reports           |
+-----------------------------------+-----------------------------------+
                                    | REST / WebSocket / HTTP
                                    v
+-----------------------------------------------------------------------+
|                         FASTAPI BACKEND SERVICE                        |
|  - API Routers                    - SQLModel / SQLAlchemy 2.x ORM     |
|  - Pydantic Validation Schemas    - Async Task Dispatchers            |
+------+----------------------------+----------------------------+------+
       |                            |                            |
       v                            v                            v
+--------------+           +------------------+         +------------------+
| Meter Service|           | Testing Engine   |         | Failure RAG AI   |
| - DLMS/COSEM |           | - Suite Runner   |         | - Pluggable LLM  |
| - Gurux      |           | - Pass/Fail      |         | - Similarity     |
|   Integration|           | - Log Collector  |         | - Knowledge Base |
+------+-------+           +--------+---------+         +--------+---------+
       |                            |                            |
       +----------------------------+----------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                      POSTGRESQL RELATIONAL DATABASE                    |
|  (Meters, Readings, TestRuns, TestResults, Failures, KnowledgeBase)    |
+-----------------------------------------------------------------------+
```

## Layer Definitions
1. **Meter Adapter & Connection Layer (`meter/`)**:
   Wraps Gurux DLMS client libraries (`GXDLMSSecureClient2`, `GXSerial`, `GXNet`, `GXDLMSReader`) with support for IEC 62056-21 Mode E optical head handshakes, HDLC framing, TCP WRAPPER, and fallback to high-fidelity **MockMeterAdapter** when physical hardware (`COM6`) is detached.
2. **Backend API & Service Layer (`backend/`)**:
   FastAPI web service exposing clean JSON endpoints for meter management, object discovery, test suite execution, failure similarity search, regression comparison, PDF/Excel report export, and AI chat.
3. **Database Layer (`backend/app/db/`)**:
   SQLAlchemy 2.x relational models storing meters, COSEM objects, historical readings, test runs, test results, failure records, firmware versions, regression runs, knowledge items, and recommendations.
4. **Frontend Cyber Dashboard (`frontend/`)**:
   Industrial dark-themed React + TypeScript dashboard with vibrant cyber-cyan accents, dynamic charts, live meter streaming cards, test logs, failure similarity analysis, side-by-side firmware regression, and AI RAG assistant interface.
