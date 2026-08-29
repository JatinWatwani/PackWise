# PackWise: Master Project Context

## Project Purpose
PackWise is the solution for SIH 2026 Problem Statement 26034: "Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels."

## Overall System Architecture
The system employs a multi-stage pipeline combining Computer Vision, LLM-based Natural Language Processing, and a deterministic Rules Engine to evaluate the legal compliance of consumer packaging.

### Core Pipeline
1. **OCR/CV**: Extracts raw text and bounding boxes from uploaded images.
2. **NLP**: Uses an LLM to extract structured attributes (e.g., MRP, weight, manufacturer) from the OCR text.
3. **Compliance**: Uses deterministic logic to compare extracted attributes against Legal Metrology Rules.

### Future Architecture Subsystems
- **Nutrition**: Analyzes serving sizes and macros.
- **Sustainability**: Extracts recycling codes and material declarations.
- **Disposal**: Provides disposal guidance.
- **Location**: Suggests nearby disposal locations.

## Team Responsibilities & Ownership
- **Archit**: Backend, API architecture, database, orchestration, and AI/LLM integration.
- **Pranav**: Computer Vision + OCR.
- **Jatin**: NLP / information extraction.
- **Pradnya**: Legal Metrology compliance/rules engine.
- **Karunya**: Frontend.
- **Ajinkya**: Dataset, QA, evaluation, DevOps.

## Architectural Philosophies

### AI vs Deterministic Logic
- AI is strictly used for **information extraction** and interpretation of messy OCR text.
- AI must **never** make the final compliance decision or invent legal rules, medical claims, or fake product data.
- **Compliance is purely deterministic.**

### API & Database Philosophy
- The API is minimal and RESTful.
- The Database uses PostgreSQL via Supabase, interacting via SQLAlchemy and async sessions.

### Security, Testing & Deployment
- **Security**: No secrets in source control. Everything uses environment variables.
- **Testing**: Comprehensive tests must verify boundaries, failures, and schemas.
- **Docker**: The backend is fully containerized.

## Rules for AI Assistants
- AI must assist development but must **not** invent OCR results, compliance results, legal rules, environmental facts, medical claims, or fake product data.
- Respect ownership boundaries (e.g., do not implement the CV layer if it's Pranav's job).
