"""
ocr_engine.py — Member 2: Computer Vision + OCR Subsystem
==========================================================
Standalone OCR and Computer Vision pipeline for PackWise.

Converts product packaging images into clean visual and textual information
with bounding boxes and confidence scores.

Output Contract:
  {
      "full_text": str,
      "regions": [
          {
              "text": str,
              "confidence": float,
              "bbox": [x1, y1, x2, y2]
          },
          ...
      ]
  }
"""

import os
import json
from typing import List, Dict, Any, Union
import numpy as np
import cv2
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
import easyocr


# ==========================================================
# STEP 1: Define Your Data Blueprint (Output Contracts)
# ==========================================================

class OCRRegion(BaseModel):
    """A single text region detected on the packaging image."""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: List[int] = Field(min_length=4, max_length=4) # [x1, y1, x2, y2]


class OCRResult(BaseModel):
    """Aggregated OCR output ready for Member 3 NLP consumption."""
    full_text: str
    regions: List[OCRRegion]


# ==========================================================
# STEP 2: Computer Vision Preprocessing Pipeline
# ==========================================================

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Prepares a raw image for optimal OCR extraction:
      1. Corrects EXIF phone camera rotation.
      2. Normalizes color channels to RGB.
      3. Applies CLAHE adaptive contrast enhancement for faded packaging.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    # Load with PIL for EXIF handling
    img = Image.open(image_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Ensure standard RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    # OpenCV CLAHE Contrast Enhancement
    img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    channels = cv2.split(img_bgr)
    enhanced = [clahe.apply(ch) for ch in channels]
    img_bgr_enhanced = cv2.merge(enhanced)

    # Return RGB NumPy array for EasyOCR
    return cv2.cvtColor(img_bgr_enhanced, cv2.COLOR_BGR2RGB)


# ==========================================================
# STEP 3: Initialize the OCR Engine Singleton
# ==========================================================

_reader = None

def get_reader() -> easyocr.Reader:
    """Lazily initialises EasyOCR Reader once to reuse model weights."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(
            lang_list=['en'],
            gpu=False,
            verbose=False
        )
    return _reader


# ==========================================================
# STEP 4: The Extraction Function
# ==========================================================

def extract_ocr_data(
    image_paths: Union[str, List[str]], 
    min_confidence: float = 0.5
) -> Dict[str, Any]:
    """
    Extracts text regions and aggregated full_text from one or more images.

    Args:
        image_paths: A single image path (str) or a list of image paths.
        min_confidence: Threshold below which noisy OCR is discarded.

    Returns:
        dict matching the OCRResult schema:
        {
            "full_text": "...",
            "regions": [{"text": "...", "confidence": 0.95, "bbox": [x1, y1, x2, y2]}, ...]
        }
    """
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    all_regions: List[Dict[str, Any]] = []
    reader = get_reader()

    for path in image_paths:
        try:
            img_array = preprocess_image(path)
            raw_results = reader.readtext(img_array, detail=1, paragraph=False)
        except Exception as e:
            return {
                "error": str(e),
                "full_text": "",
                "regions": []
            }

        # Parse bounding boxes
        for item in raw_results:
            if not item or len(item) < 3:
                continue

            bbox_polygon, text, confidence = item

            if confidence < min_confidence:
                continue

            # Convert 4-point polygon to axis-aligned [x1, y1, x2, y2]
            xs = [int(pt[0]) for pt in bbox_polygon]
            ys = [int(pt[1]) for pt in bbox_polygon]
            bbox = [min(xs), min(ys), max(xs), max(ys)]

            all_regions.append({
                "text": text.strip(),
                "confidence": round(float(confidence), 4),
                "bbox": bbox
            })

    full_text = "\n".join(r["text"] for r in all_regions)

    return {
        "full_text": full_text,
        "regions": all_regions
    }


# ==========================================================
# STEP 5: Test Run
# ==========================================================

if __name__ == "__main__":
    # Test path — replace with any sample image to test
    sample_image = r"C:\Users\Pranav\Downloads\Screenshot 2026-08-30 164320.png"

    if os.path.exists(sample_image):
        print(f"Running OCR Engine on: {sample_image}\n")
        output = extract_ocr_data(sample_image)
        print(json.dumps(output, indent=2))
    else:
        print(f"Sample image not found at: {sample_image}")
        print("Please provide a valid image path to test.")
