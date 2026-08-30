"""
image_preprocessor.py — Member 2: Computer Vision + OCR
---------------------------------------------------------
Responsibility:
  Convert a raw image file (any orientation, format, lighting) into a
  clean NumPy array suitable for the PaddleOCR engine.

Pipeline:
  disk path → Pillow load → EXIF rotation fix → RGB normalise
            → OpenCV CLAHE contrast enhance → NumPy array

This module does NOT make any compliance, nutrition, or sustainability
decisions. It only prepares image data for the OCR step.
"""

import numpy as np
import cv2
from PIL import Image, ImageOps
from app.core.logging import logger


def _apply_exif_rotation(img: Image.Image) -> Image.Image:
    """
    Apply the EXIF orientation tag so the image is always upright.
    Phone cameras embed rotation metadata rather than rotating pixel data.
    Without this step, OCR on portrait-mode photos will see sideways text.
    """
    try:
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        # Non-critical: if EXIF data is malformed or absent, keep image as-is
        logger.debug(f"EXIF transpose skipped (non-critical): {e}")
    return img


def _to_rgb(img: Image.Image) -> Image.Image:
    """
    Ensure the image is in RGB colour mode.
    Handles: RGBA (transparency), palette/P mode, L (greyscale), CMYK, etc.
    PaddleOCR expects a 3-channel NumPy array.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _enhance_contrast(img_np: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) per channel.

    Why CLAHE?
      - Standard histogram equalisation over-amplifies noise globally.
      - CLAHE works on local tiles, making faded text on product labels readable
        without blowing out already high-contrast regions.
      - Applied to each RGB channel independently so colour information is kept.

    Parameters tuned for typical product label photography:
      clipLimit=2.0  — prevents noise over-amplification
      tileGridSize=(8, 8) — 8x8 pixel tiles for local adaptation
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    channels = cv2.split(img_np)                     # Split into B, G, R channels
    enhanced = [clahe.apply(ch) for ch in channels]  # Enhance each independently
    return cv2.merge(enhanced)                        # Recombine


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Full preprocessing pipeline for a single product image file.

    Args:
        image_path: Absolute or relative path to the image on disk.

    Returns:
        A NumPy array of shape (H, W, 3) in RGB order, dtype uint8,
        ready to be passed directly to the PaddleOCR engine.

    Raises:
        ValueError: If the image cannot be loaded from the given path.
        Exception: Propagated from underlying libraries for unexpected failures.
    """
    logger.debug(f"Preprocessing image: {image_path}")

    # --- Load ---
    try:
        img = Image.open(image_path)
    except Exception as e:
        raise ValueError(f"Cannot open image at path '{image_path}': {e}") from e

    # --- Fix EXIF rotation (portrait phone photos) ---
    img = _apply_exif_rotation(img)

    # --- Normalise colour mode to RGB ---
    img = _to_rgb(img)

    # --- Convert to NumPy for OpenCV ---
    # PIL uses RGB order; OpenCV uses BGR order internally.
    # We convert: PIL RGB → NumPy → OpenCV BGR for CLAHE → back to RGB for PaddleOCR.
    img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # --- Adaptive contrast enhancement ---
    img_bgr_enhanced = _enhance_contrast(img_bgr)

    # --- Convert back to RGB for PaddleOCR ---
    img_rgb = cv2.cvtColor(img_bgr_enhanced, cv2.COLOR_BGR2RGB)

    logger.debug(f"Preprocessing complete. Shape: {img_rgb.shape}")
    return img_rgb
