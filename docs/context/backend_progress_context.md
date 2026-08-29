# PackWise Backend Progress Context

## Completed Work
- FastAPI backend foundation
- API versioning
- Health endpoint
- Image upload
- MIME validation
- File-size validation
- Multi-image upload
- PostgreSQL/Supabase integration
- SQLAlchemy models
- Alembic migration
- OCR 1:1 database enforcement
- Inspection status lifecycle
- Background pipeline
- Fresh background DB sessions
- Transaction isolation
- Failure handling
- File cleanup
- OCR adapter boundary
- Compliance adapter boundary
- NLP integration
- Pydantic validation
- API retrieval endpoints
- Dockerfile
- Automated tests

## Current Status
- **Tests**: 41 passed
- **Database migration**: Applied
- **Current Alembic revision**: `b8a850f46936`
- **Production application data created by development work**: none

## Current Pipeline Flow
```
Upload
 ↓
Inspection CREATED
 ↓
Background task
 ↓
PROCESSING
 ↓
OCR (Aggregates multiple images into one OCRResult)
 ↓
NLP
 ↓
Compliance
 ↓
COMPLETED
```

### Failure Path
```
CREATED / PROCESSING
 ↓
FAILED
```

*Note: Multiple images belong to one inspection. The OCR pipeline strictly aggregates them into a single, inspection-level `OCRResult`.*

## AI Integration Roadmap
AI provider integration is **not** the same thing as OCR. The backend owner will evaluate available LLM providers and integrate the selected provider behind a clean provider boundary.

**Evaluated LLMs:**
- Google Gemini (Recommended for structured output + Indic script handling)
- Groq (Extremely fast, less optimal for strict structured constraints natively)
- OpenAI GPT-4o-mini
- Claude 3.5 Haiku

The chosen provider must be evaluated for structured output support, Pydantic compatibility, latency, and Indian text handling.

## Team Integration Roadmap
- **Pranav (OCR)**: Provide real OCR implementation mapping `image_path(s)` → `OCRService` → `OCRResult`. Expected boundary returns text, confidence, and bounding boxes.
- **Jatin (NLP)**: NLP code exists. Future work includes validating real OCR inputs and keeping the structured output contract stable.
- **Pradnya (Compliance)**: Provide the real deterministic compliance engine mapping `ExtractedProductData` → `ComplianceService` → `ComplianceResult`. No fabricated rules may be added by the backend.

## Future Features (NOT IMPLEMENTED)
- Nutrition intelligence
- Sustainability analysis
- Disposal guidance
- Nearby disposal locations
- Authentication
- Advanced evidence visualization
- Durable background queue (e.g. Celery/Redis)
- Production monitoring
- Full integration tests with real OCR
- Full integration tests with real compliance engine
