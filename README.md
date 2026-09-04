# Smart Meter Intelligence Platform

Production-grade Smart Meter Intelligence Platform designed for electricity meter testing, automated telemetry collection, failure intelligence, and firmware regression tracking for **Iskraemeco** smart meters using **DLMS/COSEM** (IEC 62056-21 Mode E optical probe / HDLC).

---

## Key Platform Capability & Features

1. **Meter Communication & DLMS Adapter Layer**:
   - Built on top of **Gurux DLMS Python** (`GXDLMSSecureClient2`, `GXSerial`, `GXNet`, `GXDLMSReader`).
   - Seamless support for physical serial/optical communication (e.g. `COM6`, 300 baud 7E1 initial Mode E handshake, SNRM negotiation, AARQ association view).
   - **Dual-Mode Engine**: Automatically operates in **Demo/Mock Mode** when physical hardware is absent, generating realistic telemetry and error payloads, and smoothly transitions to physical hardware when configured.
   - Enforces a strict **READ-ONLY** safety policy for meter communication.

2. **Automated Testing & Reporting Engine**:
   - Executes pre-configured or custom DLMS test suites (Communication & Optical Handshake, Electrical Telemetry, Load Profile & Clock).
   - Captures raw OBIS response values, test execution duration in ms, and detailed error trace logs.
   - Generates downloadable official PDF certificates and structured JSON/Excel reports.

3. **Failure Intelligence & Grounded AI Agent (RAG)**:
   - Captures failed test run metadata into PostgreSQL.
   - Computes deterministic & string similarity scores (e.g., 94.2% match) to pair newly detected failures against historical database incidents.
   - Integrates a pluggable AI Assistant (`AIService`) that generates answers strictly grounded in database evidence and knowledge base solutions, demarcating `[FACT]`, `[INFERENCE]`, and `[RECOMMENDATION]`.

4. **Firmware Regression & Impact Recommendation Engine**:
   - Compares test execution pass rates side-by-side between Firmware A and Firmware B.
   - Identifies fixed defect test cases, new regression failures, and unchanged failure patterns.
   - Calculates high-impact test suites based on changed component dependencies.

5. **Industrial Cyber Dashboard**:
   - Built with React, TypeScript, Vite, Recharts, Lucide Icons, and modern glassmorphism styling with vibrant cyber-cyan accents.
   - Features 11 views: Executive Dashboard, Testing Center, Live Meter, Meter Profile, Failure Intelligence, Analytics, Regression Center, AI Agent, Knowledge Base, Test Reports, and Settings.

---

## Directory Structure

```text
iskra/
├── Gurux.DLMS.Python/          # Vendor Gurux DLMS source (Isolated, GPL-2.0)
├── meter/                      # DLMS Meter Adapter Engine
│   ├── config.py               # MeterConfig, HDLC address math & Pydantic settings
│   ├── exceptions.py           # Classified exception hierarchy
│   ├── obis.py                 # OBIS Registry & lookup dictionary
│   ├── objects.py              # Association view descriptors
│   ├── connection.py           # Base Abstract MeterConnection
│   ├── mock_meter.py           # High-Fidelity Mock Meter Adapter
│   ├── reader.py               # DLMSMeterReader integrating Gurux DLMS
│   ├── cli.py                  # Meter CLI tool
│   └── tests/                  # Unit tests for meter communication engine
├── backend/                    # FastAPI Backend Application
│   └── app/
│       ├── main.py             # FastAPI entrypoint exposing REST endpoints
│       ├── db/                 # SQLAlchemy 2.x ORM models & database setup
│       ├── services/           # Core application services (Meter, Test, Failure, AI, etc.)
│       ├── schemas/            # Pydantic API schemas
│       └── core/               # App configuration & logging
├── frontend/                   # Cyber Industrial React Dashboard (Vite)
│   ├── src/                    # React components, pages, services, & CSS
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite proxy configuration
│   └── Dockerfile.frontend     # Frontend container definition
├── scripts/
│   └── seed_demo.py            # Demo dataset seeder script
├── docs/                       # Architecture, OBIS Registry, & API Documentation
├── docker-compose.yml          # Full-stack Docker Compose definition
├── Dockerfile.backend          # Backend container definition
├── Makefile                    # Operational commands
├── THIRD_PARTY_NOTICES.md      # Licensing & attribution
└── README.md                   # Platform documentation
```

---

## Quickstart & Installation

### 1. Requirements
- Python 3.10+
- Node.js 18+ (for local frontend execution)
- Docker & Docker Compose (optional for containerized deployment)

### 2. Environment Setup & Dependency Installation
```bash
# Install Python backend dependencies
pip install -r requirements.txt

# Install Node.js frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Seed Demo Dataset
Populate the database with 10 Iskraemeco meters, 150 test runs, failure logs, and knowledge base articles:
```bash
python scripts/seed_demo.py
```

### 4. Run CLI Meter Verification
Inspect connection settings and available ports:
```bash
python -m meter.cli status
```

Read Active Energy Import (+A):
```bash
python -m meter.cli read --obis 1.0.1.8.0.255 --attribute 2
```

---

## Running the Platform

### Start Backend API Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- System Health Check: `http://localhost:8000/health`

### Start Frontend Cyber Dashboard
In a separate terminal:
```bash
cd frontend && npm run dev
```
- Open your browser at: `http://localhost:3000`

---

## Docker Deployment

Launch PostgreSQL, FastAPI Backend, and React Frontend in isolated containers:
```bash
docker-compose up --build -d
```

To stop containers:
```bash
docker-compose down
```

---

## License & Attribution
- Gurux DLMS Python framework is provided under the GNU General Public License v2 (GPL-2.0). See `THIRD_PARTY_NOTICES.md` for full attribution.
