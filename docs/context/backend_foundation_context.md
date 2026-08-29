# PackWise Backend Foundation

## Backend Structure
```
backend/
├── app/
│   ├── api/          # HTTP routing and FastAPI endpoints
│   ├── schemas/      # Pydantic validation models
│   ├── services/     # Business logic, pipeline orchestration, and DB persistence
│   ├── database/     # SQLAlchemy models and connection factory
│   └── core/         # Configuration, exceptions, and logging
├── tests/            # Automated test suite (Pytest)
├── alembic/          # Database migrations
├── requirements.txt  # Python dependencies
├── Dockerfile        # Containerization configuration
└── .env.example      # Environment variable template
```

## Current Database Model

### Core Entities
- **Inspection**: The root entity representing a single compliance check.
- **Image**: Represents uploaded files (1 or more per inspection).
- **OCRResult**: The aggregated raw text and regions extracted by CV.
- **ExtractedProduct**: The structured data extracted by the NLP/LLM layer.
- **ComplianceResult**: The outcome of the deterministic rules engine.
- **ComplianceViolation**: Specific rule failures tied to a ComplianceResult.

### Relationships
- `Inspection` → `Images` = **1:M** (An inspection can have multiple images).
- `Inspection` → `OCRResult` = **1:1** (Aggregated multi-image text is stored here).
- `Inspection` → `ExtractedProduct` = **1:1**
- `Inspection` → `ComplianceResult` = **1:1**
- `ComplianceResult` → `ComplianceViolation` = **1:M**

> [!NOTE]
> The OCR unique-index migration (`b8a850f46936`) has already been applied successfully, strictly enforcing the 1:1 constraint for OCRResult.
