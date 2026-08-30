from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Member 2 — OCR Output Contract
# ---------------------------------------------------------------------------

class OCRRegion(BaseModel):
    """
    A single text region detected by the OCR engine.
    Produced by Member 2 (ocr_service) and consumed by:
      - Member 3 (nlp_service) via the aggregated full_text
      - The database (ocr_results.regions JSONB column)
      - Member 4 (compliance) via evidence bounding boxes
    """
    text: str                           # The recognised text string
    confidence: float = Field(ge=0.0, le=1.0)  # OCR confidence [0, 1]
    bbox: List[int] = Field(min_length=4, max_length=4)
    # bbox format: [x1, y1, x2, y2] — top-left to bottom-right pixel coords


class OCRResult(BaseModel):
    """
    Full aggregated OCR output for one inspection (may span multiple images).
    This is the return type of ocr_service.extract_text_from_images().
    """
    full_text: str                      # All regions joined — fed to Member 3 NLP
    regions: List[OCRRegion]            # Individual regions — stored as JSONB



class MetrologyData(BaseModel):
    # 1. Product Identity
    brand_name: Optional[str] = None
    generic_name_of_commodity: Optional[str] = None
    
    # 2. Price and Quantity
    mrp: Optional[float] = None
    mrp_height_px: Optional[int] = None
    net_quantity: Optional[str] = None
    net_quantity_height_px: Optional[int] = None
    
    # 3. Required Dates
    mfg_date: Optional[str] = None
    packing_date: Optional[str] = None
    import_date: Optional[str] = None
    expiry_date: Optional[str] = None
    
    # 4. Required Entities
    manufacturer_details: Optional[str] = None
    packer_details: Optional[str] = None
    importer_details: Optional[str] = None
    
    # 5. Other Prescribed Declarations
    country_of_origin: Optional[str] = None
    consumer_care_contact: Optional[str] = None

class NutritionData(BaseModel):
    serving_size: Optional[str] = None
    servings_per_pack: Optional[str] = None
    energy_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    total_sugars_g: Optional[float] = None
    added_sugars_g: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    dietary_fibre_g: Optional[float] = None

class PackagingData(BaseModel):
    fssai_license_number: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    packaging_material_declared: Optional[str] = None
    recycling_code: Optional[str] = None
    disposal_warning: Optional[str] = None

class ExtractedProductData(BaseModel):
    metrology: MetrologyData
    nutrition: Optional[NutritionData] = None
    packaging: Optional[PackagingData] = None
    
    confidence_score: float = 0.0
    raw_ocr_length: Optional[int] = None
    extracted_fields_count: Optional[int] = None
    total_supported_fields: Optional[int] = None
    warnings: List[str] = []
