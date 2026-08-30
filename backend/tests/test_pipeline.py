import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from app.database.models import InspectionStatus
from app.services.pipeline_service import pipeline_service
from app.core.exceptions import PackWiseException

@pytest.fixture
def mock_get_inspection():
    with patch("app.services.pipeline_service.get_inspection", new_callable=AsyncMock) as m:
        # Return a fake inspection with one image
        fake_inspection = MagicMock()
        fake_img = MagicMock()
        fake_img.storage_path = "uploads/test.jpg"
        fake_inspection.images = [fake_img]
        m.return_value = fake_inspection
        yield m

@pytest.fixture
def mock_update_status():
    with patch("app.services.pipeline_service.update_inspection_status", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_ocr():
    with patch("app.services.pipeline_service.ocr_service.extract_text_from_images", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_nlp():
    with patch("app.services.pipeline_service.nlp_service.extract_from_ocr", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_compliance():
    with patch("app.services.pipeline_service.compliance_service.evaluate_rules", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_save_ocr():
    with patch("app.services.pipeline_service.save_ocr_result", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_save_nlp():
    with patch("app.services.pipeline_service.save_extracted_product", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_save_compliance():
    with patch("app.services.pipeline_service.save_compliance_result", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture
def mock_set_failed():
    with patch.object(pipeline_service, "_set_failed_status", new_callable=AsyncMock) as m:
        yield m

@pytest.mark.anyio
async def test_pipeline_ocr_failure(
    mock_get_inspection, mock_update_status, mock_ocr, mock_set_failed
):
    """
    Test that if OCR fails (or is not implemented), the pipeline catches it
    and marks the inspection as FAILED.
    """
    from unittest.mock import ANY
    mock_ocr.side_effect = PackWiseException(message="Not implemented", code="OCR_NOT_IMPLEMENTED", status_code=501)
    
    inspection_id = uuid.uuid4()
    await pipeline_service.run_inspection_pipeline(inspection_id)
    
    # Verify status changed to PROCESSING first
    mock_update_status.assert_any_call(ANY, inspection_id, InspectionStatus.PROCESSING)
    
    # Verify OCR was called
    mock_ocr.assert_called_once_with(["uploads/test.jpg"])
    
    # Verify failure handled
    mock_set_failed.assert_called_once_with(inspection_id)

@pytest.mark.anyio
async def test_pipeline_full_success(
    mock_get_inspection, mock_update_status, mock_ocr, mock_nlp, mock_compliance,
    mock_save_ocr, mock_save_nlp, mock_save_compliance, mock_set_failed
):
    """
    Test a fully mocked successful pipeline.
    """
    from unittest.mock import ANY
    mock_ocr.return_value = {"full_text": "Sample text", "regions": {}}
    
    fake_extracted = MagicMock()
    fake_extracted.confidence_score = 0.9
    mock_nlp.return_value = fake_extracted
    
    mock_compliance.return_value = {"status": "PASS", "violations": []}
    
    inspection_id = uuid.uuid4()
    await pipeline_service.run_inspection_pipeline(inspection_id)
    
    # Should save everything
    mock_save_ocr.assert_called_once()
    mock_save_nlp.assert_called_once()
    mock_save_compliance.assert_called_once()
    
    # Should update to COMPLETED
    mock_update_status.assert_any_call(ANY, inspection_id, InspectionStatus.COMPLETED)
    
    # Should NOT fail
    mock_set_failed.assert_not_called()

@pytest.mark.anyio
async def test_pipeline_nlp_failure(
    mock_get_inspection, mock_update_status, mock_ocr, mock_nlp,
    mock_save_ocr, mock_save_nlp, mock_set_failed
):
    """
    Test OCR success but NLP failure.
    """
    mock_ocr.return_value = {"full_text": "Sample text", "regions": {}}
    mock_nlp.side_effect = PackWiseException(message="NLP Failed", code="NLP_API_FAILURE", status_code=502)
    
    inspection_id = uuid.uuid4()
    await pipeline_service.run_inspection_pipeline(inspection_id)
    
    mock_save_ocr.assert_called_once()
    mock_save_nlp.assert_not_called()
    mock_set_failed.assert_called_once_with(inspection_id)
