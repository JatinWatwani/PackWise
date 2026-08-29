import json
from typing import Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import PackWiseException
from app.schemas.extraction import MetrologyData, ExtractedProductData

class NLPService:
    def _extract_metrology_sync(self, raw_ocr_text: str) -> dict:
        """
        Synchronous extraction function using Google GenAI SDK. 
        """
        prompt = f"""
        You are a Legal Metrology assistant.
        Read this raw OCR text from a product packaging and fill in the requested schema.
        Fix optical typos (like '2O' -> 20.0 or '1OOg' -> '100g').
        If a field is not present on the package, leave it as null.

        OCR Text:
        {raw_ocr_text}
        """

        try:
            # We defer import to catch dependency errors cleanly at runtime
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except ImportError:
            logger.error("google-genai dependency is not installed.")
            raise PackWiseException(
                message="NLP dependencies are missing.",
                code="NLP_DEPENDENCY_ERROR",
                status_code=500
            )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', # Or whichever model is configured
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': MetrologyData
                }
            )
            result_dict = json.loads(response.text)
            
            # Calculate a basic confidence score
            found_fields = sum(1 for v in result_dict.values() if v is not None)
            total_fields = 15 # Based on MetrologyData schema size
            result_dict["confidence_score"] = round(found_fields / total_fields, 2)

            return result_dict

        except json.JSONDecodeError as e:
            logger.error(f"GenAI returned invalid JSON: {str(e)}")
            raise PackWiseException(
                message="NLP returned invalid structured output.",
                code="NLP_INVALID_OUTPUT",
                status_code=502 # Bad Gateway
            )
        except Exception as e:
            logger.error(f"GenAI API call failed: {str(e)}")
            raise PackWiseException(
                message="NLP extraction API call failed.",
                code="NLP_API_FAILURE",
                status_code=502
            )

    async def extract_from_ocr(
        self, 
        raw_ocr_text: str, 
        cv_font_hooks: Optional[Dict[str, int]] = None
    ) -> ExtractedProductData:
        """
        Asynchronous wrapper to extract data.
        """
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is not configured.")
            raise PackWiseException(
                message="NLP API key is missing. Extraction cannot proceed.",
                code="NLP_CONFIG_ERROR",
                status_code=500
            )
        
        # Run the synchronous SDK call in a separate thread
        raw_result = await run_in_threadpool(self._extract_metrology_sync, raw_ocr_text)
        
        # Merge CV hooks if provided
        if cv_font_hooks:
            raw_result.update(cv_font_hooks)
            
        try:
            # Validate against the Pydantic schema
            metrology = MetrologyData(**raw_result)
        except Exception as e:
            logger.error(f"Validation failed for NLP result: {str(e)}")
            raise PackWiseException(
                message="NLP result failed schema validation.",
                code="NLP_VALIDATION_ERROR",
                status_code=500
            )
        
        # Construct the final nested response
        return ExtractedProductData(
            metrology=metrology,
            confidence_score=raw_result.get("confidence_score", 0.0),
            raw_ocr_length=len(raw_ocr_text),
            extracted_fields_count=sum(1 for v in metrology.model_dump().values() if v is not None),
            total_supported_fields=15
        )

nlp_service = NLPService()
