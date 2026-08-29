from typing import List, Dict, Any
from app.core.exceptions import PackWiseException
from app.core.logging import logger

class OCRService:
    async def extract_text_from_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Adapter boundary for Pranav's CV/OCR subsystem.
        Takes a list of image paths and returns aggregated OCR text and regions.
        """
        logger.warning("OCR Subsystem called but is not yet implemented.")
        raise PackWiseException(
            message="OCR Subsystem is not yet implemented.",
            code="OCR_NOT_IMPLEMENTED",
            status_code=501
        )

ocr_service = OCRService()
