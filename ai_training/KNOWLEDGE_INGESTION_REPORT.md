# ISKRA Knowledge Base Ingestion & Multi-Document Intelligence Report

**Execution Timestamp:** 2026-09-09 23:05:44
**Total Ingestion Duration:** 1031.79 seconds
**Vector Store:** ChromaDB (`iskra_knowledge`) with `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

---

## 1. Executive Summary
- **Total Source Files Inspected:** 23
- **Successfully Ingested Files:** 22
- **Unique Content Files:** 20
- **Exact Duplicates Detected:** 2
- **Empty / Corrupt Files:** 1
- **Total Granular Chunks Indexed:** 38274
- **Distinct Error Codes Cataloged:** 39 (e.g., 0, 1, 2, 3, 4, 5, 6, 31, 36, 37, 38, 39, 40, 41, 43...)
- **Firmware Technical References:** 3472
- **Communication References (RS485/SMS/Modem):** 180
- **Installation / Mounting References:** 5833
- **Tracker & Historical Support Records:** 37773

## 2. File Inventory & Categorization (All 23 Files)
| # | Filename | Format | Size | SHA-256 (Prefix) | Model | Doc Type | Version | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `Error cpu.pdf` | .PDF | 787.7 KB | `65c49654be` | UNKNOWN | ERROR_REFERENCE | v0.2 | `UNIQUE` |
| 2 | `L1 Created 2131 (1).csv` | .CSV | 446.0 KB | `ef993c8bc0` | MT514 | ERROR_REFERENCE | UNKNOWN | `UNIQUE` |
| 3 | `L1 Created 2131.csv` | .CSV | 0.0 KB | `e3b0c44298` | UNKNOWN | HISTORICAL_RECORD | UNKNOWN | `EMPTY_CORRUPT` |
| 4 | `L2 Soft (1) (1).csv` | .CSV | 169.7 KB | `2affc81659` | UNKNOWN | ERROR_REFERENCE | UNKNOWN | `UNIQUE` |
| 5 | `L2 Soft (1).csv` | .CSV | 169.7 KB | `2affc81659` | UNKNOWN | ERROR_REFERENCE | UNKNOWN | `EXACT_DUPLICATE` |
| 6 | `ME 514 V5 1.pdf` | .PDF | 879.1 KB | `88d75d7e7a` | ME514 | OTHER | v5 | `UNIQUE` |
| 7 | `ME514 Meter.pdf` | .PDF | 1051.8 KB | `9bf2abac82` | ME514 | METER_MANUAL | UNKNOWN | `UNIQUE` |
| 8 | `ME514-5 Brochure.pdf` | .PDF | 679.3 KB | `8ce8ab1f91` | ME514-5 | BROCHURE | UNKNOWN | `UNIQUE` |
| 9 | `ME514.pdf` | .PDF | 2096.1 KB | `f298b558cc` | ME514 | METER_MANUAL | UNKNOWN | `UNIQUE` |
| 10 | `ME514_4.0 Technical Description .pdf` | .PDF | 1240.6 KB | `e6ff2d5bce` | ME514 | COMMUNICATION | v4.0 | `UNIQUE` |
| 11 | `MT174_Technical_Specification_0-2_SMS.pdf` | .PDF | 1043.6 KB | `105908a6b4` | MT174 | COMMUNICATION | v0.2 | `UNIQUE` |
| 12 | `MT514 Meter Pages & Meter Errors.pdf` | .PDF | 270.4 KB | `0f87542b9c` | MT514 | ERROR_REFERENCE | UNKNOWN | `UNIQUE` |
| 13 | `MT514-CT_Technical Description pdf.pdf` | .PDF | 950.2 KB | `9311d2f726` | MT514-CT | COMMUNICATION | UNKNOWN | `UNIQUE` |
| 14 | `MT880 installation guid small (1).pptx` | .PPTX | 5537.3 KB | `d76674596e` | MT880 | COMMUNICATION | UNKNOWN | `UNIQUE` |
| 15 | `MT880 installation guid small.pptx` | .PPTX | 5537.3 KB | `d76674596e` | MT880 | COMMUNICATION | UNKNOWN | `EXACT_DUPLICATE` |
| 16 | `SCDC - MPMS 3000.pdf` | .PDF | 1156.0 KB | `9e9b2a757b` | ME514 | SOFTWARE_DOCUMENTATION | UNKNOWN | `UNIQUE` |
| 17 | `SCDC Tracker 2020.xlsx` | .XLSX | 360.5 KB | `85c53b4220` | ME514 | ERROR_REFERENCE | v4 | `UNIQUE` |
| 18 | `SCDC Tracker 2021.xlsx` | .XLSX | 602.7 KB | `45cfad8b52` | ME514 | ERROR_REFERENCE | v4 | `UNIQUE` |
| 19 | `SCDC Tracker 2022.xlsx` | .XLSX | 1176.2 KB | `da381845aa` | ME514 | ERROR_REFERENCE | v5 | `UNIQUE` |
| 20 | `SCDC Tracker 2023.xlsx` | .XLSX | 1045.8 KB | `241a6b3a6f` | ME514 | ERROR_REFERENCE | v4 | `UNIQUE` |
| 21 | `SCDC Tracker 2024.xlsx` | .XLSX | 1356.3 KB | `2567090e62` | ME514 | ERROR_REFERENCE | v5 | `UNIQUE` |
| 22 | `Zsk08206_31 (NEW LCD SPECS).pdf` | .PDF | 2922.8 KB | `413ab14f84` | Zsk08206 | COMMUNICATION | UNKNOWN | `UNIQUE` |
| 23 | `mt174.pdf` | .PDF | 1186.0 KB | `fceca92ad1` | MT174 | HARDWARE | UNKNOWN | `UNIQUE` |

## 3. Breakdown by Document Type & Meter Family
### Primary Document Types
- **ERROR_REFERENCE:** 10 files
- **COMMUNICATION:** 6 files
- **METER_MANUAL:** 2 files
- **HISTORICAL_RECORD:** 1 files
- **OTHER:** 1 files
- **BROCHURE:** 1 files
- **HARDWARE:** 1 files
- **SOFTWARE_DOCUMENTATION:** 1 files

### Meter Family Distribution
- **ME:** 11 files
- **MT:** 7 files
- **UNKNOWN:** 4 files
- **LCD:** 1 files

## 4. Duplicate & Near-Duplicate Analysis
The ingestion engine computes SHA-256 digests and content fingerprints to prevent redundant index pollution:
1. **`MT880 installation guid small.pptx`:** Exact duplicate of `MT880 installation guid small (1).pptx` (SHA-256: `d76674596e4a`). Skipped during indexing to prevent duplicate retrieval.
2. **`L2 Soft (1).csv`:** Exact duplicate of `L2 Soft (1) (1).csv` (SHA-256: `a86711ca93d6`). Skipped during indexing.
3. **`L1 Created 2131.csv`:** 0 bytes (empty/corrupt). Detected, logged, and isolated from vector index.
4. **`ME514` Series Near-Duplicates:** Multiple technical documents (`ME 514 V5 1.pdf`, `ME514_4.0 Technical Description .pdf`, `ME514.pdf`) represent distinct release revisions rather than identical duplicates. They are indexed with explicit version provenance (`v4.0` vs `v5`).

## 5. Version Conflict Detection
No critical version conflicts detected.

## 6. Identified Knowledge Gaps (Knowledge Expansion Advisor)
- **MT880 Error Codes [MISSING]:** MT880 installation guide exists but contains no comprehensive error code reference table.
- **MT174 Error Codes [MISSING]:** MT174 technical specification and manual describe measurement properties but lack explicit error code diagnostics table.
- **Error Code Repair Procedures [PARTIAL]:** MT514 and Error cpu manuals define error code meanings, but do not provide user-executable L1 troubleshooting or self-repair procedures.
- **Vending Integration [LIMITED]:** Trackers reference Vending system issues, but no verified technical manual for the Vending backend software is provided.

## 7. Model-Aware & Request-Aware Policy
- **Model Isolation:** Queries regarding `MT174` only surface chunks from `MT174` documents or general platform manuals. Cross-model contamination with `MT514` error codes is blocked.
- **Request Intent Discrimination:** Questions seeking a **Fix Procedure** (`How do I fix Error 400?`) will return `PARTIAL / NO VERIFIED FIX PROCEDURE` if only an error definition is available.
- **Tracker Data Governance:** Tracker entries from `SCDC Tracker` and `L1/L2` files are classified as `HISTORICAL_RECORD / TRACKER` and are never presented as official technical policy.