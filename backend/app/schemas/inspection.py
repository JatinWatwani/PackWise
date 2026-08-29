from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID

# Import Enum to match database exactly without coupling to SQLAlchemy models
from app.database.models import InspectionStatus

class ImageResponse(BaseModel):
    id: UUID
    storage_path: str
    side: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OCRResultResponse(BaseModel):
    id: UUID
    image_id: Optional[UUID] = None
    full_text: Optional[str] = None
    regions: Optional[Any] = None
    processing_status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ComplianceViolationResponse(BaseModel):
    id: UUID
    rule_id: str
    rule_name: str
    severity: str
    message: str
    field: Optional[str] = None
    detected_value: Optional[str] = None
    expected_requirement: Optional[str] = None
    evidence: Optional[Any] = None
    
    model_config = ConfigDict(from_attributes=True)

class ComplianceResultResponse(BaseModel):
    id: UUID
    status: str
    evaluated_rules: Any
    passed_rules: Any
    violations: List[ComplianceViolationResponse] = []
    evaluated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InspectionResponse(BaseModel):
    id: UUID
    status: InspectionStatus
    created_at: datetime
    updated_at: datetime
    
    # We optionally include related models for the GET endpoint
    images: List[ImageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
