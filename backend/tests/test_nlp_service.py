import pytest
from app.services.nlp_service import nlp_service
from app.core.exceptions import PackWiseException
from app.core.config import settings
from pydantic import ValidationError

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_nlp_missing_api_key(monkeypatch):
    """Test that missing API key raises NLP_CONFIG_ERROR"""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    
    with pytest.raises(PackWiseException) as exc_info:
        await nlp_service.extract_from_ocr("Sample OCR text")
        
    assert exc_info.value.code == "NLP_CONFIG_ERROR"
    assert exc_info.value.status_code == 500

@pytest.mark.anyio
async def test_nlp_dependency_missing(monkeypatch):
    """Test that missing google-genai dependency raises NLP_DEPENDENCY_ERROR"""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake_key")
    
    # We mock sys.modules to simulate missing google dependency if it's not installed
    import sys
    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.genai", None)

    with pytest.raises(PackWiseException) as exc_info:
        await nlp_service.extract_from_ocr("Sample OCR text")
        
    assert exc_info.value.code == "NLP_DEPENDENCY_ERROR"
    assert exc_info.value.status_code == 500

@pytest.mark.anyio
async def test_nlp_api_failure(monkeypatch):
    """Test that an API failure (like bad key) raises NLP_API_FAILURE"""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake_key")
    
    # If the dependency IS installed but the key is bad, it should raise API_FAILURE
    # If it's NOT installed, this test would theoretically hit DEPENDENCY_ERROR.
    # To reliably test API failure, we mock the sync function to just raise an Exception
    def mock_extract_sync(*args, **kwargs):
        raise PackWiseException(message="Google API unavailable", code="NLP_API_FAILURE", status_code=502)
    
    monkeypatch.setattr(nlp_service, "_extract_metrology_sync", mock_extract_sync)

    with pytest.raises(PackWiseException) as exc_info: 
        await nlp_service.extract_from_ocr("Sample OCR text")
    
    assert exc_info.value.code == "NLP_API_FAILURE"

@pytest.mark.anyio
async def test_nlp_validation_error(monkeypatch):
    """Test that if the LLM returns completely wrong data types, it raises NLP_VALIDATION_ERROR"""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake_key")
    
    # Mock the LLM returning completely invalid data (e.g. dict for a string field, string for a float)
    def mock_extract_sync_invalid(*args, **kwargs):
        return {
            "mrp": "This is a string, not a float"
        }
    
    monkeypatch.setattr(nlp_service, "_extract_metrology_sync", mock_extract_sync_invalid)

    with pytest.raises(PackWiseException) as exc_info:
        await nlp_service.extract_from_ocr("Sample OCR text")
        
    assert exc_info.value.code == "NLP_VALIDATION_ERROR"

@pytest.mark.anyio
async def test_nlp_valid_output_accepted(monkeypatch):
    """Test that a valid mock LLM response is cleanly parsed into ExtractedProductData"""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake_key")
    
    def mock_extract_sync_valid(*args, **kwargs):
        return {
            "brand_name": "Test Brand",
            "mrp": 50.0,
            "confidence_score": 0.95
        }
    
    monkeypatch.setattr(nlp_service, "_extract_metrology_sync", mock_extract_sync_valid)
    
    result = await nlp_service.extract_from_ocr("Valid raw text")
    
    assert result.metrology.brand_name == "Test Brand"
    assert result.metrology.mrp == 50.0
    assert result.confidence_score == 0.95
