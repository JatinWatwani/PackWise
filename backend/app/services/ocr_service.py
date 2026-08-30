"""
ocr_service.py — Member 2: Computer Vision + OCR
-------------------------------------------------
Responsibility:
  Accept a list of on-disk image paths, preprocess each one, run EasyOCR,
  and return the aggregated text + bounding-box regions.

Output contract (consumed by pipeline_service.py → nlp_service + DB):
  {
      "full_text": str,       # All region text joined by newline
      "regions": [
          {
              "text": str,
              "confidence": float,   # [0.0, 1.0]
              "bbox": [x1, y1, x2, y2]
          },
          ...
      ]
  }

Architecture notes:
  - EasyOCR Reader is initialised ONCE as a module-level singleton.
    Re-initialising per request would reload model weights every time.
  - The actual inference (reader.readtext()) is synchronous/CPU-bound.
    We wrap it with FastAPI's run_in_threadpool() to prevent blocking the
    async event loop.
  - This service only produces text + regions. It does NOT interpret meaning.

Engine choice:
  PaddleOCR was the original plan, but PaddlePaddle has no Python 3.14 wheel
  on PyPI. EasyOCR is fully compatible with Python 3.14 and provides equivalent
  accuracy for Indian product packaging text.
"""

from typing import List, Dict, Any
from fastapi.concurrency import run_in_threadpool

from app.core.logging import logger
from app.core.exceptions import PackWiseException
from app.services.image_preprocessor import preprocess_image


# ---------------------------------------------------------------------------
# EasyOCR Singleton Initialisation
# ---------------------------------------------------------------------------
# We initialise the Reader once at first call (lazy singleton) so model weights
# are only loaded once per process — not per request.
#
# Parameters:
#   lang_list=['en']  — English. Add 'hi' for Hindi, 'ta' for Tamil etc.
#   gpu=False         — CPU inference. Set to True if CUDA GPU is available.
#
# The import is deferred so that the rest of the application can start
# even if easyocr is not yet installed, giving a clear error at call time.

_easyocr_reader = None

def _get_reader():
    """
    Lazily initialises and returns the EasyOCR Reader singleton.
    Raises PackWiseException if the library is not installed.
    """
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            logger.info("Initialising EasyOCR Reader (first call — model weights loading)...")
            _easyocr_reader = easyocr.Reader(
                lang_list=['en'],
                gpu=False,
                verbose=False
            )
            logger.info("EasyOCR Reader ready.")
        except ImportError:
            raise PackWiseException(
                message="EasyOCR is not installed. Run: pip install easyocr",
                code="OCR_DEPENDENCY_ERROR",
                status_code=500
            )
    return _easyocr_reader


# ---------------------------------------------------------------------------
# Region Parsing Helper
# ---------------------------------------------------------------------------

def _parse_easyocr_output(raw_results: list, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
    """
    Convert EasyOCR's raw output into the flat OCRRegion contract.

    EasyOCR returns a list of tuples per detected text line:
      (bbox_polygon, text, confidence)

    Where bbox_polygon is a list of 4 [x, y] corner points (not [x1,y1,x2,y2]).
    We convert from polygon corners → axis-aligned bounding box [x1, y1, x2, y2].

    Args:
        raw_results: The direct output of reader.readtext(img_array)
        min_confidence: Regions below this threshold are discarded (noisy OCR).

    Returns:
        List of dicts matching the OCRRegion schema.
    """
    regions = []

    for item in raw_results:
        if not item or len(item) < 3:
            continue

        bbox_polygon, text, confidence = item

        # Filter out low-confidence detections
        if confidence < min_confidence:
            logger.debug(f"Discarding low-confidence region (conf={confidence:.2f}): '{text}'")
            continue

        # Convert 4-corner polygon → axis-aligned [x1, y1, x2, y2]
        # bbox_polygon: [[x0,y0], [x1,y0], [x1,y1], [x0,y1]] (clockwise)
        xs = [int(pt[0]) for pt in bbox_polygon]
        ys = [int(pt[1]) for pt in bbox_polygon]
        bbox = [min(xs), min(ys), max(xs), max(ys)]

        regions.append({
            "text": text.strip(),
            "confidence": round(float(confidence), 4),
            "bbox": bbox
        })

    return regions


# ---------------------------------------------------------------------------
# OCRService
# ---------------------------------------------------------------------------

class OCRService:
    """
    Member 2's OCR adapter.
    Implements the contract expected by pipeline_service.run_inspection_pipeline().
    """

    def _run_ocr_on_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Synchronous OCR execution for a single image.
        Called via run_in_threadpool to avoid blocking the async event loop.

        Returns a list of OCRRegion dicts for this image.
        """
        # 1. Preprocess: fix rotation, normalise colour, enhance contrast
        try:
            img_array = preprocess_image(image_path)
        except ValueError as e:
            raise PackWiseException(
                message=f"Image preprocessing failed: {e}",
                code="OCR_PREPROCESSING_ERROR",
                status_code=422
            )

        # 2. Run EasyOCR
        reader = _get_reader()
        try:
            # detail=1 returns bounding boxes + confidence (vs detail=0 which is text-only)
            # paragraph=False keeps individual word/line detections rather than merging
            raw_results = reader.readtext(img_array, detail=1, paragraph=False)
        except Exception as e:
            logger.error(f"EasyOCR inference failed on '{image_path}': {e}")
            raise PackWiseException(
                message="OCR engine failed during inference.",
                code="OCR_INFERENCE_ERROR",
                status_code=500
            )

        # 3. Parse raw EasyOCR output into flat region dicts
        regions = _parse_easyocr_output(raw_results)
        logger.info(f"OCR found {len(regions)} regions in '{image_path}'")
        return regions

    async def extract_text_from_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Public entry point — called by pipeline_service.

        Processes every image in image_paths, merges all regions, and builds
        the aggregated full_text string consumed by Member 3's NLP service.

        Args:
            image_paths: List of on-disk file paths saved by StorageService.

        Returns:
            {
                "full_text": str,
                "regions": List[OCRRegion dict]
            }
        """
        if not image_paths:
            logger.warning("extract_text_from_images called with no image paths.")
            return {"full_text": "", "regions": []}

        all_regions: List[Dict[str, Any]] = []

        for path in image_paths:
            logger.info(f"Running OCR on image: {path}")
            # Offload CPU-bound inference to a thread so we don't block the
            # async event loop for the duration of EasyOCR inference
            image_regions = await run_in_threadpool(self._run_ocr_on_image, path)
            all_regions.extend(image_regions)

        # Build the flat text string that Member 3's NLP service expects.
        # EasyOCR returns regions roughly in reading order (top-to-bottom).
        full_text = "\n".join(r["text"] for r in all_regions)

        logger.info(
            f"OCR complete. Total regions: {len(all_regions)}, "
            f"full_text length: {len(full_text)} chars"
        )

        return {
            "full_text": full_text,
            "regions": all_regions
        }


ocr_service = OCRService()
