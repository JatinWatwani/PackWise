# PackWise Backend Architecture

## Overview
The PackWise backend is built in **Python 3.11+** using **FastAPI**. It leverages **PostgreSQL** (hosted on Supabase) as the primary datastore and uses **SQLAlchemy** (async) for the ORM, managed by **Alembic** migrations.

## Pipeline Architecture
The system receives multiple images of a product and passes them through a linear pipeline:
1. **CV/OCR (Pranav)**: Images are processed to extract raw text and bounding boxes.
2. **NLP/LLM (Archit/Jatin)**: The raw text is passed to an LLM strictly for information extraction (structured via Pydantic).
3. **Compliance (Pradnya)**: The structured data is evaluated against deterministic Legal Metrology rules.

## Orchestration layer
The HTTP router handles validations, MIME checks, file sizing, and local storage. Upon successful DB persistence of an `Inspection` record, a FastAPI `BackgroundTasks` thread is spawned.
This background orchestrator (`PipelineService`):
- Fetches a **fresh AsyncSession** (isolated from the HTTP request).
- Updates the status to `PROCESSING`.
- Chains the adapter interfaces (`OCRService` -> `NLPService` -> `ComplianceService`).
- Commits results atomically at each stage.
- Transitions to `COMPLETED` on success, or rolls back and opens a safe fallback session to transition to `FAILED` on exception.

## AI integration
AI is specifically constrained to the NLP extraction phase. The backend interacts with the provider (e.g. Gemini 2.5 Flash) requesting a specific `response_schema`. All responses must natively parse into the defined Pydantic `MetrologyData` models before propagating downstream.

## Database Philosophy
Data is strictly structured. `Inspection` has a 1:M relationship with `Images`, but `OCRResult`, `ExtractedProduct`, and `ComplianceResult` are all strictly 1:1. The pipeline aggregates insights from multiple images to fulfill the 1:1 constraint for OCR text representation.
