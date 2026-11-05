# West Bengal BLLRO Land Mutation and Verification Assistant

A lightweight workflow management and AI assistance tool for field and extension-level revenue officers.

## Executive Summary

In rural and semi-urban West Bengal, citizens routinely submit applications for Land Mutation (Kharij / Namantaran) and Record of Rights (RoR / Porcha) updates following land purchases, inheritances, or family partitions.

Currently, Block Land and Land Reforms Office (BLLRO) field workers and revenue inspectors process these requests through paper-heavy files, manual data entry into systems such as Banglarbhumi, and physical document checks. This creates processing backlogs and administrative fatigue.

The BLLRO Land Mutation and Verification Assistant is a purpose-built, human-in-the-loop workflow management system designed specifically for extension-level officers. It simplifies daily queue management, provides targeted AI checks to spot document mismatches, and maintains a clean, transparent audit history for every land record application.

## Key Capabilities

- **Priority work queue dashboard.** Instant visual summary of pending items, high-priority discrepancies, and applications awaiting field checks.
- **Three-step enforced workflow.** Clear state progression from initial intake to field verification and final decisioning.
- **Targeted AI assistance.** High-yield tools for automated document parsing, ownership mismatch detection, and bilingual notice drafting.
- **Human-in-the-loop authority.** The AI advises; the revenue inspector retains final decision authority (approve, reject, or return with comments).
- **Complete audit trail.** Sequential event log capturing state changes, timestamps, officer remarks, and AI suggestions for regulatory compliance.

## Core Application Workflow

```text
[ 1. Intake & Digitization ] --> [ 2. Field & Chain Verification ] --> [ 3. Final BLLRO Decision ]
         |                                    |                                    |
  AI document OCR                      AI chain mismatch                    AI notice and
  and field pre-filling                discrepancy check                    remark generator
```

### Stage 1: Intake and Digitization (`SUBMITTED`)

**Officer action.** Logs incoming application metadata (Mouza, J.L. No., Khatian No., Plot/Dag No., applicant details) and uploads scanned copies of the Sale Deed (Dalil) and existing Porcha.

**AI assistance.** Extracts relevant metadata fields from unstructured Bengali/English PDF and image scans to auto-fill form fields and reduce manual typing errors.

### Stage 2: Field and Chain Verification (`FIELD_VERIFICATION`)

**Officer action.** Conducts physical and documentary checks to confirm the chain of ownership and land revenue tax (Khajna) payment status.

**AI assistance.** Compares the transferor named on the new deed against the recorded owner on the existing Porcha. Automatically flags discrepancies, for example: "Warning: Transferor 'Aparna Das' does not match recorded owner 'Bimal Das'. Check for inheritance link deed."

### Stage 3: Decision and Resolution (`READY_FOR_DECISION`)

**Officer action.** The officer makes the binding call:

- **Approve.** Mutates the land record.
- **Reject.** Denies invalid or fraudulent applications.
- **Return.** Sends the application back requesting specific missing documents (for example, a legal heir certificate or updated tax receipt).

**AI assistance.** Generates a pre-drafted official remark in English or Bengali detailing missing requirements when an application is marked returned.

Invalid jumps (for example, `SUBMITTED` directly to `APPROVED`) are rejected by a code-level state machine.

## Technology Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Frontend | Next.js, React, Tailwind CSS | Responsive UI tailored for low-bandwidth field environments |
| Backend | Python, FastAPI | Lightweight API with native asynchronous support |
| Database | PostgreSQL (SQLite for local bootstrap) | Application state and immutable audit logs |
| AI / OCR | Tesseract OCR, OpenAI GPT-4o, or a local LLM | Document extraction, discrepancy heuristics, and notice drafting |
| State machine | Explicit code-level enforcer | Prevents invalid status transitions |

## Data Model Overview

### `applications`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `applicant_name` | Text | |
| `mouza` | Text | |
| `jl_number` | Integer | |
| `dag_number` | Integer | |
| `khatian_number` | Integer | |
| `status` | Enum | `SUBMITTED`, `FIELD_VERIFICATION`, `READY_FOR_DECISION`, `APPROVED`, `REJECTED`, `RETURNED` |
| `assigned_officer_id` | UUID | |
| `created_at` | Timestamp | |

### `application_history`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `application_id` | UUID | Foreign key to `applications.id` |
| `previous_status` | Enum | |
| `new_status` | Enum | |
| `action_taken_by` | UUID | Officer ID |
| `ai_flags_triggered` | JSONB / Text | |
| `officer_remarks` | Text | |
| `timestamp` | Timestamp | |

## Getting Started Locally

### Prerequisites

- Python 3.10–3.12 (3.12 recommended; create the venv with `py -3.12 -m venv venv` on Windows)
- Node.js 18+
- PostgreSQL (optional; SQLite is used if `DATABASE_URL` is not set)

### Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env  # macOS / Linux

uvicorn app.main:app --reload --app-dir .
```

The API starts at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive docs are at `/docs`.

To use PostgreSQL instead of SQLite:

```bash
docker compose up -d db
```

Then set `DATABASE_URL` in `backend/.env` to the value in `.env.example`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI starts at [http://localhost:3000](http://localhost:3000) and talks to the API at `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).

## License

This project is open source under the [MIT License](LICENSE).
