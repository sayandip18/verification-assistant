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

### What a worker can do

| Requirement | How the app does it |
| --- | --- |
| See an overview of pending applications and what needs attention first | The **Priority work queue** dashboard ranks open files: ownership mismatches ready for decision first, then other decisions waiting, then flagged field checks, returned files, field checks and new intakes. Within each group, the longest-waiting file comes first. Each row says why it is there and what the next action is. Count cards filter by stage or show only flagged files. **Approved** and **Rejected** cards list decided files. |
| Move each application through the steps (at least three) | Intake → Field verification → Ready for decision → Approved / Rejected / Returned, enforced by a state machine. |
| Get AI assistance at each step, where it genuinely helps | OCR pre-fill at intake, an LLM ownership-chain check at verification, and an LLM-drafted return notice at decision (see below). |
| Approve, reject or return, with the worker making the final call | Only the officer's button press changes status. AI output is advisory, approving a flagged file asks for confirmation, and an AI-drafted notice must be reviewed and confirmed. |
| See a clear history of what happened to each application | Every application page has a **History** timeline: status changes with officer name and role, field edits (old → new), every AI run, the AI verdict at the moment of each decision, and the exact notice sent. It can be filtered by type. |

```text
[ 1. Intake & Digitization ] --> [ 2. Field & Chain Verification ] --> [ 3. Final BLLRO Decision ]
         |                                    |                                    |
  OCR + field                          LLM ownership-chain                  LLM return-notice
  pre-filling                          assessment                           draft (officer edits
                                                                            and confirms)
```

### Stage 1: Intake and Digitization (`SUBMITTED`)

**Officer action.** Logs application metadata (Mouza, J.L. No., Khatian No., Plot/Dag No., applicant details) and uploads scanned copies of the Sale Deed (Dalil) and existing Porcha.

**Automated assistance.** Runs OCR (Tesseract) on uploaded Dalil and Porcha scans (PDF, image, or pasted text), extracts labelled Bengali/English fields with pattern matching, and fills blank form fields. This step uses no LLM. The officer can edit every value before the file moves on.

### Stage 2: Field and Chain Verification (`FIELD_VERIFICATION`)

**Officer action.** Conducts physical and documentary checks to confirm the chain of ownership and land revenue tax (Khajna) payment status. The officer corrects the Transferor, Recorded owner and Khajna fields if needed, clicks **Save verification notes**, then clicks **Run AI chain check**. The check reads the saved values and the uploaded scans.

**AI assistance.** An OpenAI model reads the transferor on the new deed, the recorded owner on the existing Porcha, the khajna status and OCR excerpts from both scans. It returns a structured verdict: `MATCH`, `LIKELY_SAME_PERSON`, `POSSIBLE_LINK`, `MISMATCH` or `INSUFFICIENT_DATA`. With it come the reasons, what to check in the field, and which documents to ask for, plus a Bengali summary. Unlike an exact string comparison, it treats "বিমল দাস", "Bimol Kumar Das" and "Sri Bimal Das" as the same person. When the transferor shares a surname but not a given name, it says a link deed or legal heir certificate is needed. The officer runs it on demand from Stage 2; it also runs automatically when the file moves to decision, unless a current AI verdict already exists.

### Stage 3: Decision and Resolution (`READY_FOR_DECISION`)

**Officer action.** The officer makes the binding call:

- **Approve.** Records the mutation as approved. Updating the official record in Banglarbhumi stays outside this tool.
- **Reject.** Denies invalid or fraudulent applications.
- **Return.** Sends the application back requesting specific missing documents (for example, a legal heir certificate or updated tax receipt). When the citizen brings them, the officer clicks **Re-open at intake** and the file goes through the steps again.

**AI assistance.** When the officer chooses **Return**, they list what is missing. The list is pre-filled from the chain check's "documents to ask for". The model then drafts a short, plain-language notice in Bengali or English. The officer edits the draft and must click **Confirm notice and return file**; nothing is saved to the record until they do. The history records whether the notice was the AI draft as-is, an edited AI draft, or written by the officer.

Approving a file the chain check flagged asks the officer to confirm first.

Invalid jumps (for example, `SUBMITTED` directly to `APPROVED`) are rejected by a code-level state machine.

## Where AI helps and why

AI is used only where it saves officer time or surfaces risk early. The officer always retains final authority.

| Where | What AI does | Why it helps |
| --- | --- | --- |
| Intake | OCR (Tesseract) + pattern-based field extraction from Dalil / Porcha; no LLM | Cuts repetitive typing from Bengali/English scans and reduces keying errors. Labelled fields don't need a language model. |
| Field verification | LLM ownership-chain assessment (verdict, reasons, field checks, documents to request) | Name matching across Bengali/English spellings and spotting inheritance gaps is judgment work that exact string matching gets wrong in both directions |
| Decision / return | LLM-drafted return notice in Bengali or English, edited and confirmed by the officer | Citizens get clear, specific instructions in their language; officers stop retyping the same letter |
| Audit | Every AI run is logged (`ai_runs`) with inputs/outputs, and shown in the history | Keeps suggestions reviewable and accountable |

**Safeguards.** AI output is advisory and never changes status by itself. Document text is passed to the model as data inside `<document>` tags, never as instructions. Scans stay on the server; only the names, plot details, khajna status and up to 4,000 characters of OCR text per document are sent to the OpenAI API. A government deployment would need a data-processing agreement or a model hosted in India. If no `OPENAI_API_KEY` is set, or the API call fails, both features fall back to the earlier rules: exact name comparison and a fixed notice template. The UI labels such results "Rule-based" instead of "AI assessment", so the app still works offline. The queue reuses the latest stored AI verdict, so listing files never waits on a model call. If the officer edits the names, that verdict is marked stale.

The design is deliberately narrow: high-yield document and naming checks, not full case adjudication. That keeps the model useful in a regulated workflow without replacing inspector judgment.

## How you would measure the app's impact, and why you think it will work

**How to measure it.** Run a pilot in one block for 8–12 weeks. Record the same metrics from the paper register for the 3 months before the pilot as a baseline. Most metrics come straight from the app's own tables: `application_history` holds every status change and edit with a timestamp and officer, and `ai_runs` holds every AI suggestion.

| Metric | How it is measured | What success looks like |
| --- | --- | --- |
| **Cycle time** | Median days from `SUBMITTED` to `APPROVED` / `REJECTED` (`application_history` timestamps) | Clearly shorter than the paper baseline |
| **Repeat visits** | Share of files returned more than once (count of `RETURNED` entries per file) | Falls, because AI notices list every missing paper the first time |
| **Queue health** | Open backlog, age of the oldest open file, flagged files waiting | Oldest-file age stops growing |
| **Officer effort** | Intake time with vs without OCR pre-fill; share of pre-filled fields the officer then edits (`FIELD_UPDATE` entries) | Faster intake, with few corrections |
| **AI quality** | Of files the chain check flagged, the share the officer returned or rejected (flag confirmed) vs approved anyway (overridden); of AI notices, the share confirmed unedited (`notice_source`) | High confirmation rate; overrides reviewed monthly to tune the prompt |
| **Wrong approvals caught** | Approved files later challenged or reversed, flagged vs unflagged | Fewer reversals than baseline |
| **Adoption** | Active officers per week; share of files with at least one AI run | Officers keep using it after the first weeks |

**Why it should work**

- The pain is operational and repetitive (typing, comparing names across spellings, drafting return letters). That suits OCR plus a narrowly scoped language model.
- The workflow mirrors how officers already move files, so adoption does not require inventing a new process.
- Human-in-the-loop decisions plus an explicit state machine reduce the risk of AI overreach or invalid approvals.
- Early discrepancy flags and clearer return notices should cut rework loops for both officers and citizens.
- Every AI suggestion and every officer override is recorded, so the AI's usefulness can be checked from data rather than assumed.

## Your main technical decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| UI | Next.js, React, Tailwind CSS | Fast officer-facing UI; `/api` proxy keeps the login cookie first-party |
| API | Python FastAPI monolith | One service for auth, workflow, OCR, and AI pipelines; simple to deploy locally |
| Persistence | PostgreSQL | Structured applications, officers, history, document metadata, and AI run logs |
| Blob storage | Local object dir by default (MinIO/S3 optional) | Easy local demo; S3-compatible path when needed |
| OCR | Tesseract (`eng+ben`) + PDF text-layer extraction | Works offline for bilingual scans without a paid vision API dependency |
| LLM | OpenAI (`gpt-5.5` by default) via the official `openai` Python SDK, Chat Completions with strict JSON-schema structured output | Reliable, typed verdicts the UI can render; Bengali-capable; rule-based fallback when unavailable |
| Workflow control | Explicit code-level state machine | Prevents illegal status jumps and keeps decisions auditable |
| Auth model | Seeded / admin-created officers only | No public registration; matches staff-only BLLRO use |

### Key capabilities

- Priority work queue dashboard for pending items, high-priority discrepancies, and field checks, with Approved and Rejected cards for decided files
- Three-step enforced workflow from intake to decision
- Targeted AI for OCR, ownership mismatch detection, and bilingual notice drafting
- One history timeline per file: status changes with officer name and role, edits to the verification fields (old → new), every AI run, the ownership verdict at the time of each decision, and the exact notice sent. It can be filtered to status changes, edits, or AI activity.

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
| `ai_flags_triggered` | JSONB | Context for the event. `kind` is `FIELD_UPDATE` (field edits, `previous_status == new_status`), `RETURN_NOTICE` (confirmed notice text, language and source) or `DECISION` (chain verdict at decision time) |
| `officer_remarks` | Text | |
| `created_at` | Timestamp | |

#### `documents`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `application_id` | UUID | FK → `applications.id` |
| `document_type` | Enum | `SALE_DEED`, `PORCHA`, `OTHER` |
| `blob_key` | Text | Unique object key in blob storage (local folder or MinIO/S3) |
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

### AI (optional)

Set `OPENAI_API_KEY` in `backend/.env` to turn on the LLM chain check and notice drafting. `OPENAI_MODEL` defaults to `gpt-5.5`. Without a key, or with `LLM_ENABLED=false`, the app uses the rule-based fallbacks and labels them as such.

### Try it

[`test-docs/`](test-docs/) has sample Dalil and Porcha files for three scenarios (inheritance gap, spelling variant, clear mismatch), with the expected AI verdict for each. They are plain `.txt` files, so they work without Tesseract. See [`test-docs/README.md`](test-docs/README.md) for a step-by-step walkthrough.

### Tests

```bash
cd backend
venv\Scripts\python -m unittest discover -s tests   # Windows
# python -m unittest discover -s tests              # macOS / Linux, with the venv active
```

The AI tests mock the OpenAI API, so they need no key.

### OCR

On **New intake**, upload a Dalil and/or Porcha (PDF, image, or `.txt`). The API reads a PDF text layer when it exists; otherwise it rasterizes pages and runs Tesseract (`eng+ben`). Extracted labelled fields fill **blank** form fields only. Saving the application stores the scans and writes an `ai_runs` row (`pipeline=OCR`). Officers can re-run OCR from the application page.

`POST /ai/ocr` OCRs a file before an application exists. `POST /ai/extract` parses pasted text. Image OCR needs Tesseract on the machine; set `TESSERACT_CMD` if it is not on `PATH`.

## License

This project is open source under the [MIT License](LICENSE).
