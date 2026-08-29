from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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
