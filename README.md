# West Bengal BLLRO Land Mutation and Verification Assistant

A lightweight workflow management and AI assistance tool for field and extension-level revenue officers.

## The problem you chose and who it affects

In rural and semi-urban West Bengal, citizens routinely submit applications for Land Mutation (Kharij / Namantaran) and Record of Rights (RoR / Porcha) updates after land purchases, inheritances, or family partitions.

Block Land and Land Reforms Office (BLLRO) field workers and revenue inspectors still process many of these requests through paper files, manual entry into systems such as Banglarbhumi, and physical document checks. That creates processing backlogs, repeated visits for citizens, and administrative fatigue for officers.

**Who it affects**

- **Citizens** waiting on mutation and RoR updates needed for ownership clarity, loans, and transfers
- **Revenue inspectors and extension officers** who intake files, verify ownership chains, and decide cases
- **BLLRO supervisors / block offices** that need transparent queues and auditable decisions

## What the application does and the steps in your workflow

The BLLRO Land Mutation and Verification Assistant is a human-in-the-loop workflow system for extension-level officers. It gives them a priority queue, an enforced three-step case flow, targeted AI checks for document mismatches, and a full audit history for every application.

```text
[ 1. Intake & Digitization ] --> [ 2. Field & Chain Verification ] --> [ 3. Final BLLRO Decision ]
         |                                    |                                    |
  AI document OCR                      AI chain mismatch                    AI notice and
  and field pre-filling                discrepancy check                    remark generator
```

### Stage 1: Intake and Digitization (`SUBMITTED`)

**Officer action.** Logs application metadata (Mouza, J.L. No., Khatian No., Plot/Dag No., applicant details) and uploads scanned copies of the Sale Deed (Dalil) and existing Porcha.

**AI assistance.** Runs OCR on uploaded Dalil and Porcha scans (PDF, image, or pasted text), extracts labelled Bengali/English fields, and fills blank form fields. The officer can edit every value before the file moves on.

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

## Where AI helps and why

AI is used only where it saves officer time or surfaces risk early. The officer always retains final authority.

| Where | What AI does | Why it helps |
| --- | --- | --- |
| Intake | OCR + labelled field extraction from Dalil / Porcha | Cuts repetitive typing from Bengali/English scans and reduces keying errors |
| Field verification | Ownership chain mismatch check (transferor vs recorded owner) | Catches inheritance / link-deed gaps before a bad approval |
| Decision / return | Bilingual notice and remark drafting | Speeds clear citizen-facing instructions when files are returned |
| Audit | Every AI run is logged (`ai_runs`) with inputs/outputs | Keeps suggestions reviewable and accountable |

The design is deliberately narrow: high-yield document and naming checks, not full case adjudication. That keeps the model useful in a regulated workflow without replacing inspector judgment.

## How you would measure the app's impact, and why you think it will work

**Impact metrics**

- **Cycle time:** median days from intake (`SUBMITTED`) to final status (`APPROVED` / `REJECTED` / `RETURNED`)
- **Queue health:** backlog size, age of oldest open file, share of high-priority discrepancy cases
- **Officer effort:** time to complete intake (with vs without OCR pre-fill); share of fields accepted vs manually corrected
- **Quality:** rate of chain-mismatch flags that officers confirm as real issues; return rate for missing documents after AI-assisted notices
- **Adoption:** active officers per week, applications processed per officer, % of cases with at least one AI assist used
- **Trust / compliance:** % of status transitions with officer remarks; audit completeness (history + AI run coverage)

**Why it should work**

- The pain is operational and repetitive (typing, comparing names, drafting return notes), which is a good fit for assistive OCR and rule-like checks.
- The workflow mirrors how officers already move files, so adoption does not require inventing a new process.
- Human-in-the-loop decisions plus an explicit state machine reduce the risk of AI overreach or invalid approvals.
- Early discrepancy flags and clearer return notices should cut rework loops for both officers and citizens.

## Your main technical decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| UI | Next.js, React, Tailwind CSS | Fast officer-facing UI; `/api` proxy keeps the login cookie first-party |
| API | Python FastAPI monolith | One service for auth, workflow, OCR, and AI pipelines; simple to deploy locally |
| Persistence | PostgreSQL | Structured applications, officers, history, document metadata, and AI run logs |
| Blob storage | Local object dir by default (MinIO/S3 optional) | Easy local demo; S3-compatible path when needed |
| OCR / AI | Tesseract (`eng+ben`) + PDF text-layer extraction | Works offline for bilingual scans without a paid vision API dependency |
| Workflow control | Explicit code-level state machine | Prevents illegal status jumps and keeps decisions auditable |
| Auth model | Seeded / admin-created officers only | No public registration; matches staff-only BLLRO use |

### Key capabilities

- Priority work queue dashboard for pending items, high-priority discrepancies, and field checks
- Three-step enforced workflow from intake to decision
- Targeted AI for OCR, ownership mismatch detection, and bilingual notice drafting
- Complete audit trail of state changes, timestamps, officer remarks, and AI suggestions

### Data model overview

PostgreSQL holds structured data. Raw files are not stored in the database; `documents.blob_key` points at object storage.

#### `officers`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `employee_id` | Text | Unique staff identifier |
| `email` | Text | Unique login identifier |
| `full_name` | Text | |
| `password_hash` | Text | bcrypt |
| `role` | Enum | `REVENUE_INSPECTOR`, `EXTENSION_OFFICER`, `SUPERVISOR`, `ADMIN` |
| `office_code` | Text | Optional BLLRO / block code |
| `is_active` | Boolean | Inactive officers cannot sign in |
| `last_login_at` | Timestamp | |
| `created_at` / `updated_at` | Timestamp | |

There is no public registration. Accounts are seeded or created by an administrator.

#### `applications`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `applicant_name` | Text | |
| `mouza` | Text | |
| `jl_number` | Integer | |
| `dag_number` | Integer | |
| `khatian_number` | Integer | |
| `transferor_name` | Text | Optional, used by chain check |
| `recorded_owner_name` | Text | Optional, used by chain check |
| `khajna_status` | Text | |
| `status` | Enum | `SUBMITTED`, `FIELD_VERIFICATION`, `READY_FOR_DECISION`, `APPROVED`, `REJECTED`, `RETURNED` |
| `assigned_officer_id` | UUID | FK → `officers.id` |
| `created_by_officer_id` | UUID | FK → `officers.id` |
| `created_at` / `updated_at` | Timestamp | |

#### `application_history`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `application_id` | UUID | FK → `applications.id` |
| `previous_status` | Enum | |
| `new_status` | Enum | |
| `action_taken_by` | UUID | FK → `officers.id` |
| `ai_flags_triggered` | JSONB | |
| `officer_remarks` | Text | |
| `created_at` | Timestamp | |

#### `documents`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `application_id` | UUID | FK → `applications.id` |
| `document_type` | Enum | `SALE_DEED`, `PORCHA`, `OTHER` |
| `blob_key` | Text | Unique object key in MinIO |
| `original_filename` | Text | |
| `content_type` | Text | |
| `size_bytes` | Integer | |
| `uploaded_by_officer_id` | UUID | FK → `officers.id` |
| `created_at` | Timestamp | |

#### `ai_runs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `application_id` | UUID | FK → `applications.id` |
| `document_id` | UUID | Optional FK → `documents.id` |
| `pipeline` | Enum | `OCR`, `CHAIN_CHECK`, `NOTICE` |
| `status` | Enum | `PENDING`, `SUCCEEDED`, `FAILED` |
| `input_payload` | JSONB | |
| `output_payload` | JSONB | |
| `created_at` | Timestamp | |

## How to run it locally

### Prerequisites

- Python 3.10–3.12 (3.12 recommended; create the venv with `py -3.12 -m venv venv` on Windows)
- Node.js 18+
- Docker (PostgreSQL and MinIO)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with English and Bengali traineddata (UB-Mannheim installer on Windows). Required for image scans and image-only PDFs. Digital PDFs with a text layer and `.txt` files still extract without it.

### Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL. Raw documents are stored under `backend/blob-data` by default (`BLOB_BACKEND=local`). To use MinIO instead, set `BLOB_BACKEND=s3` and run `docker compose --profile minio up -d`.

### Backend

```bash
cd backend
py -3.12 -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env  # macOS / Linux

uvicorn app.main:app --reload --reload-dir app --app-dir .
```

The API starts at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive docs are at `/docs`.

On first boot the API creates tables and a demo officer:

- Email: `officer@bllro.local`
- Password: `changeme`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI starts at [http://localhost:3000](http://localhost:3000). Browser calls go to `/api/*`, which Next.js proxies to the backend so the login cookie stays first-party.

Officers sign in at `/login`. Application and AI routes require a valid session.

### OCR

On **New intake**, upload a Dalil and/or Porcha (PDF, image, or `.txt`). The API reads a PDF text layer when it exists; otherwise it rasterizes pages and runs Tesseract (`eng+ben`). Extracted labelled fields fill **blank** form fields only. Saving the application stores the scans and writes an `ai_runs` row (`pipeline=OCR`). Officers can re-run OCR from the application page.

`POST /ai/ocr` OCRs a file before an application exists. `POST /ai/extract` parses pasted text. Image OCR needs Tesseract on the machine; set `TESSERACT_CMD` if it is not on `PATH`.

## License

This project is open source under the [MIT License](LICENSE).
