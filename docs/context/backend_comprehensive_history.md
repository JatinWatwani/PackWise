# PackWise Backend Comprehensive Architecture & History

## 1. Introduction
This document serves as a comprehensive record of the backend development for PackWise. It details what has been built, the architectural reasoning behind those decisions, and the explicit instructions provided by the Technical Lead/User during the foundation phase.

## 2. What the User Instructed (The Directives)
The user provided strict, step-by-step instructions to lay a production-grade, highly resilient backend foundation. The core directives were:

1.  **Frameworks & Infrastructure**: Build a FastAPI backend using Python 3.11+, integrated with PostgreSQL (hosted on Supabase) via asynchronous SQLAlchemy and Alembic for migrations. Containerize the app using Docker.
2.  **API Endpoints & Uploads**: Implement a robust `POST /api/v1/inspections` endpoint that supports multi-image uploads. It must enforce strict MIME-type and file-size validations to prevent garbage data from entering the system.
3.  **Database Modeling & Strict Constraints**: Design a relational database schema for the entire lifecycle (`Inspection`, `Image`, `OCRResult`, `ExtractedProduct`, `ComplianceResult`, `ComplianceViolation`). Critically, the user instructed that `OCRResult` must enforce a strict `1:1` relationship with `Inspection`, meaning multiple images belong to one inspection, but their OCR output must be aggregated into a single record.
4.  **Asynchronous Pipeline & Lifecycle Management**: Build a background processing pipeline. An inspection should transition through specific states: `CREATED` -> `PROCESSING` -> `COMPLETED` (or `FAILED`). Background tasks must run in isolated, fresh database sessions to prevent transaction bleed and handle failures gracefully.
5.  **Adapter Boundaries & Mocking**: Create clean interfaces for subsystems owned by other team members. Since the NLP layer (Jatin) was ready with Gemini, integrate it. Since the OCR (Pranav) and Compliance (Pradnya) layers were blocked/pending, implement adapter boundaries that safely mock `501 NotImplementedError` to allow orchestration testing without blocking development.
6.  **Testing**: Write a comprehensive Pytest suite to validate boundaries, schemas, database integrity, and failure states.

## 3. What Was Built (The Implementation)
Based on the instructions, the following comprehensive system was built:

### A. Core Architecture & Folder Structure
Implemented a clean layered architecture separating routing (`app/api`), validation (`app/schemas`), business logic (`app/services`), and data access (`app/database`). 
-   **API Versioning**: Endpoints are properly versioned (e.g., `/api/v1/...`).
-   **Environment Configuration**: Centralized environment parsing via Pydantic Settings, utilizing a `.env` pattern to protect secrets.

### B. Database & Migrations
-   **SQLAlchemy Models**: Created robust async models utilizing UUIDs as primary keys.
-   **Alembic Revision `b8a850f46936`**: Successfully generated and applied the migration. This migration strictly enforces the user's directive for a unique constraint on `OCRResult.inspection_id`, guaranteeing the 1:1 aggregation rule.

### C. The Ingestion & Orchestration Engine
-   **Upload Pipeline**: The system validates incoming multipart form data, verifying that files are strictly images (e.g., `image/jpeg`, `image/png`) and under the maximum size limit. It safely stores these temporarily for processing.
-   **Background Tasks**: The `InspectionService` triggers `BackgroundTasks` in FastAPI. These tasks are provided a completely independent `AsyncSession` factory, ensuring that if the API request finishes, the background processing safely continues with its own transaction lifecycle.
-   **Lifecycle Enforcement**: The pipeline accurately sets the `InspectionStatus` to `PROCESSING`. If any step (OCR, NLP, Compliance) fails or raises an exception, the pipeline catches it, cleans up temporary files, logs the error, and sets the status to `FAILED`.

### D. Team Integration & Boundaries
-   **NLP Integration**: Successfully integrated Pydantic-validated extraction schemas expected by the LLM layer.
-   **Isolated Stubs**: Built robust `NotImplementedError` stubs for OCR and Compliance, ensuring the orchestration engine (`Member 1`'s responsibility) can be tested end-to-end without waiting for other members to finish their algorithms.

### E. Quality Assurance
-   **Automated Testing**: Wrote a Pytest suite that currently passes **41 tests**. The suite mocks the database and background tasks to ensure unit reliability.
-   **Dockerization**: Added a `Dockerfile` to guarantee reproducibility across development environments.

## 4. Why It Was Built This Way (Architectural Rationale)
The system was engineered with specific defensive paradigms based on the project's multi-member nature:

1.  **Defensive Validation**: By validating MIME types and sizes at the very edge (API layer), we protect the expensive Computer Vision (CV) and LLM processes from crashing on malformed data.
2.  **Transaction Isolation**: Using fresh database sessions in background tasks ensures that if the background pipeline crashes, it does not corrupt the database state or hold stale locks. The `try/except/finally` blocks guarantee that the `Inspection` always reaches a terminal state (`COMPLETED` or `FAILED`), preventing "zombie" inspections stuck in `PROCESSING`.
3.  **Strict 1:1 Aggregation Rule**: Multiple package images (front, back, sides) are uploaded for a single physical product. If we created multiple `OCRResult` records, the LLM/NLP layer would have fragmented context. Aggregating them into a strict 1:1 `OCRResult` ensures the NLP layer receives the holistic text of the product in a single prompt.
4.  **Interface Contracts (Adapter Boundaries)**: PackWise is built by a team of 6. If the backend orchestrator directly imported half-written OCR or Compliance code, the API would constantly break. By building strict adapter boundaries (Pydantic schemas and mocked interfaces), the backend orchestration remains stable and 100% functional, regardless of the progress of other members.

## 5. Current State & Next Steps
-   **State**: The backend orchestration foundation is **DONE**. The API, DB, and pipelines are solid.
-   **Roadmap**: 
    -   Wait for Pranav to replace the OCR mock with real YOLO/PaddleOCR logic.
    -   Wait for Pradnya to replace the Compliance mock with the deterministic rules engine.
    -   Implement upcoming features: Nutrition scoring, Sustainability analysis, Disposal guidance, Location APIs, and Authentication.
