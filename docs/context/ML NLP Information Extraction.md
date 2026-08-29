# Context: ML / NLP / Information Extraction

> **Subsystem**: Information Extraction & Natural Language Processing  
> **Owner**: Jatin Watwani
> **Status**: Active / Initial Architecture Implemented  
> **Last Updated**: August 2026

---

## 1. 🎯 Subsystem Overview & Responsibilities

Member 3 is responsible for converting raw, unstructured OCR text and bounding-box metadata from packaging into **clean, structured, and schema-validated product intelligence**.

```
    ┌─────────────────────────┐
    │       Member 2:         │
    │    Computer Vision      │
    │ (Raw OCR Text + BBoxes) │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │       Member 3:         │
    │    ML / NLP Service     │
    │  (Google GenAI / LLM)   │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │  ExtractedProductData   │
    │ (Pydantic Data Contract)│
    └────────────┬────────────┘
                 │
        ┌────────┴────────┬───────────────────┐
        ▼                 ▼                   ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────────┐
│   Member 4    │ │   Member 1    │ │ Intelligence      │
│  Compliance   │ │ Orchestration │ │ Nutrition &       │
│ Rules Engine  │ │  & Database   │ │ Sustainability    │
└───────────────┘ └───────────────┘ └───────────────────┘
```

### ✅ What Member 3 OWNS:
1. **Information Extraction**: Parsing raw OCR text into distinct fields (Legal Metrology, Nutrition, Packaging).
2. **Text Cleaning & OCR Error Correction**: Correcting optical ambiguities (e.g., `2O` $\rightarrow$ `20.0`, `1OOg` $\rightarrow$ `100g`, stripping currency symbols for numeric values).
3. **Entity Normalization**: Standardizing dates (`YYYY-MM`), separating numbers from measurement units (`100` + `g`), parsing addresses.
4. **Structured Schema Enforcement**: Returning strictly validated Pydantic models (`ExtractedProductData`).
5. **Confidence & Quality Scoring**: Providing confidence metrics based on extraction completeness and signal strength.
6. **CV Integration Hooks**: Hooking font pixel heights from Member 2's bounding boxes into field metadata (e.g., `mrp_height_px`, `net_quantity_height_px`).

### ❌ What Member 3 DOES NOT OWN:
- **Image Preprocessing / OCR execution** (Owned by Member 2).
- **Final Legal Compliance Judgments / Rule logic** (Owned by Member 4 — LLMs extract facts; deterministic rules evaluate legality).
- **FastAPI Endpoints & Database Persistence** (Owned by Member 1).

---

## 2. 📂 File & Directory Structure

All Member 3 deliverables are modularized within the backend architecture:

```
PackWise/
├── data/
│   └── nlp/
│       ├── nlp_engine.py               # Legal Metrology extraction engine
│       └── requirements.txt            # Module dependencies (google-genai, pydantic)
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py               # Central environment & API key loader
│   │   ├── schemas/
│   │   │   ├── __init__.py             # Exports extraction schemas
│   │   │   └── extraction.py           # Pydantic schemas (LegalMetrologyData, NutritionData, etc.)
│   │   └── services/
│   │       ├── __init__.py             # Exports nlp_service singleton
│   │       └── nlp_service.py          # NLPService class with Google GenAI integration
│   ├── tests/
│   │   └── test_nlp_service.py         # Standalone unit & integration test
│   ├── .env.example                    # Sample environment variables
│   └── requirements.txt                # Dependencies (google-genai, pydantic, etc.)
└── docs/
    └── context/
        ├── Project Master Context.txt  # Project Master Context
        └── ML NLP Information Extraction.md # This context file
```

---

## 3. 📦 Data Contracts & Interfaces

### 3.1 Input Contract (From Member 2 / Orchestrator)
```python
raw_ocr_text: str
cv_font_hooks: Optional[Dict[str, int]] = {
    "mrp_height_px": 28,
    "net_quantity_height_px": 22
}
```

### 3.2 Output Contract (`ExtractedProductData`)
```json
{
  "metrology": {
    "brand_name": "Britannia",
    "generic_name_of_commodity": "Biscuits",
    "mrp": 20.0,
    "mrp_raw_text": "Rs. 2O.OO (Incl. of all taxes)",
    "mrp_height_px": 28,
    "net_quantity": "100 g",
    "net_quantity_value": 100.0,
    "net_quantity_unit": "g",
    "net_quantity_height_px": 22,
    "unit_sale_price": "Rs. 0.20 / g",
    "mfg_date": "2026-08",
    "packing_date": null,
    "import_date": null,
    "expiry_date": "Best before 6 months from packaging",
    "batch_number": "B402",
    "manufacturer_details": "Britannia Industries Ltd., Kolkata - 700017",
    "packer_details": null,
    "importer_details": null,
    "country_of_origin": "India",
    "consumer_care_contact": "1800-425-4449 / feedback@britindia.com"
  },
  "nutrition": {
    "serving_size": "100g",
    "servings_per_pack": null,
    "energy_kcal": 490.0,
    "protein_g": 7.0,
    "carbohydrates_g": 68.0,
    "total_sugars_g": 24.0,
    "added_sugars_g": 22.0,
    "total_fat_g": 21.0,
    "saturated_fat_g": 10.0,
    "trans_fat_g": null,
    "cholesterol_mg": null,
    "sodium_mg": 320.0,
    "dietary_fibre_g": null
  },
  "packaging": {
    "fssai_license_number": "10015043001129",
    "is_vegetarian": true,
    "packaging_material_declared": "Multilayer Flexible Laminate",
    "recycling_code": "07 OTHER",
    "disposal_warning": "Dispose responsibly"
  },
  "confidence_score": 0.87,
  "raw_ocr_length": 450,
  "extracted_fields_count": 13,
  "total_supported_fields": 15,
  "warnings": []
}
```

---

## 4. 🤝 How Team Members Use This Subsystem

### For Member 1 (Lead & Backend Orchestrator)
Call `nlp_service.extract_from_ocr` in your FastAPI pipeline:
```python
from app.services.nlp_service import nlp_service

# Inside your inspection pipeline:
extracted_data = nlp_service.extract_from_ocr(
    raw_ocr_text=ocr_result.full_text,
    cv_font_hooks={
        "mrp_height_px": ocr_result.mrp_bbox_height,
        "net_quantity_height_px": ocr_result.net_qty_bbox_height
    }
)
```

### For Member 4 (Compliance & Rules Engine)
Directly evaluate fields against Legal Metrology Rules:
```python
# Check mandatory fields deterministically:
if not extracted_data.metrology.mrp:
    report_violation(rule_id="LM_MRP_001", message="MRP declaration missing")

if not extracted_data.metrology.country_of_origin:
    report_violation(rule_id="LM_COO_001", message="Country of Origin missing")

# Check font height compliance with CV hook:
if extracted_data.metrology.net_quantity_height_px:
    check_font_height_compliance(
        declared_net_weight=extracted_data.metrology.net_quantity_value,
        font_height_px=extracted_data.metrology.net_quantity_height_px
    )
```

---

## 5. ⚙️ Setup & Testing

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   Create or edit `.env` in `backend/` or project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Run Extraction Test**:
   ```bash
   python backend/tests/test_nlp_service.py
   ```

---

## 6. 📝 Changelog & Next Milestones

- [x] Initial `LegalMetrologyData`, `NutritionData`, and `PackagingData` Pydantic schemas.
- [x] Google GenAI SDK (`google-genai`) integration with strict JSON structured outputs.
- [x] Font height hooks for CV bounding boxes (Pranav's integration).
- [x] Standalone test runner and mock schema validation.
- [ ] Multilingual OCR text translation/transliteration support (Hindi, regional languages).
- [ ] Groq / Llama-3-70B fallback connector for high-throughput batch evaluations.
