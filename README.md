# PackWise

PackWise is the solution for SIH 2026 Problem Statement 26034: "Software System to check compliance of Packaged Commodities under Legal Metrology Rules, 2011".

## Main Architecture
The system accepts uploaded images of packaging, passes them through OCR (Computer Vision) to extract text, interprets the text via an LLM to extract structured fields (e.g., MRP, weight), and finally validates the structured data against a deterministic Legal Metrology rules engine.

## Backend Technology
- **Python 3.11+**
- **FastAPI**
- **PostgreSQL** (via Supabase)
- **SQLAlchemy** (Async) + **Alembic**

## How to Run Locally

### Environment Configuration
Copy the `.env.example` file to `.env`:
```bash
cp backend/.env.example backend/.env
```
Ensure you have the required `DATABASE_URL` and provider keys configured.

### Running the App
1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```
2. Run the application:
```bash
uvicorn app.main:app --reload
```

### Migration Commands
To apply database migrations:
```bash
alembic upgrade head
```

### Running Tests
The suite leverages `pytest`. To run tests:
```bash
python -m pytest
```

## Current MVP Limitations & Integration Status
- **Limitations**: The pipeline uses in-memory `BackgroundTasks`. If the server crashes during an active inspection, it may stall in `PROCESSING`.
- **Team Integration Status**:
  - API, Database, Upload, Orchestration: **DONE**
  - NLP (Jatin): **DONE** (Integrated with Gemini)
  - OCR (Pranav): **BLOCKED** (Mocking `501 NotImplementedError`)
  - Compliance (Pradnya): **BLOCKED** (Mocking `501 NotImplementedError`)

For comprehensive technical context and roadmap details, see the `docs/context/` directory.
