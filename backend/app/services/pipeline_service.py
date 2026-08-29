import uuid
from app.database.connection import async_session_factory
from app.database.models import InspectionStatus
from app.core.logging import logger
from app.core.exceptions import PackWiseException

from app.services.inspection_service import (
    update_inspection_status,
    get_inspection,
    save_ocr_result,
    save_extracted_product,
    save_compliance_result
)
from app.services.ocr_service import ocr_service
from app.services.nlp_service import nlp_service
from app.services.compliance_service import compliance_service

class PipelineService:
    async def run_inspection_pipeline(self, inspection_id: uuid.UUID) -> None:
        """
        Background orchestrator for the inspection pipeline.
        Obtains a fresh database session and executes the pipeline in stages.
        """
        logger.info(f"Starting pipeline for inspection {inspection_id}")
        
        try:
            async with async_session_factory() as db:
                # 1. Update status to PROCESSING
                await update_inspection_status(db, inspection_id, InspectionStatus.PROCESSING)
                
                # Retrieve the inspection to get the associated images
                inspection = await get_inspection(db, inspection_id)
                image_paths = [img.storage_path for img in inspection.images]
                
                if not image_paths:
                    logger.warning(f"Inspection {inspection_id} has no images. Continuing anyway.")
                
                # 2. OCR Stage
                logger.info(f"Running OCR on {len(image_paths)} images for {inspection_id}")
                ocr_data = await ocr_service.extract_text_from_images(image_paths)
                await save_ocr_result(db, inspection_id, ocr_data)
                
                # 3. NLP Stage
                logger.info(f"Running NLP extraction for {inspection_id}")
                full_text = ocr_data.get("full_text", "")
                extracted_data = await nlp_service.extract_from_ocr(full_text)
                await save_extracted_product(db, inspection_id, extracted_data)
                
                # 4. Compliance Stage
                logger.info(f"Running Compliance evaluation for {inspection_id}")
                compliance_data = await compliance_service.evaluate_rules(extracted_data)
                await save_compliance_result(db, inspection_id, compliance_data)
                
                # 5. Mark as COMPLETED
                await update_inspection_status(db, inspection_id, InspectionStatus.COMPLETED)
                logger.info(f"Pipeline COMPLETED successfully for {inspection_id}")
                
        except PackWiseException as e:
            logger.error(f"Pipeline failed for inspection {inspection_id} with known error [{e.code}]: {e.message}")
            await self._set_failed_status(inspection_id)
            
        except Exception as e:
            # We log exception to include the traceback for unexpected errors server-side
            logger.exception(f"Pipeline failed for inspection {inspection_id} with unexpected error: {str(e)}")
            await self._set_failed_status(inspection_id)

    async def _set_failed_status(self, inspection_id: uuid.UUID) -> None:
        """
        Safe method to update the inspection status to FAILED.
        Uses a completely new, clean database session to guarantee transaction safety,
        preventing any previous failed transaction from blocking the status update.
        """
        try:
            async with async_session_factory() as fresh_db:
                await update_inspection_status(fresh_db, inspection_id, InspectionStatus.FAILED)
                logger.info(f"Successfully marked inspection {inspection_id} as FAILED after pipeline error.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to update inspection {inspection_id} status to FAILED. {str(e)}")

pipeline_service = PipelineService()
