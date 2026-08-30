# 🚀 PackWise — Member 2 (Computer Vision & OCR)

## 🎯 Mission & Responsibility
Member 2 is responsible for converting **raw product packaging images** into **clean visual and textual information** (text, bounding boxes, and confidence scores).

> **Boundary Rule:**  
> Member 2 does **not** make compliance rulings, health claims, or sustainability judgments. Member 2 extracts high-fidelity OCR data for **Member 3 (NLP)** and **Member 4 (Compliance)**.

---

## 🧱 What Was Built

### 1. Image Preprocessing Pipeline (`image_preprocessor.py`)
Before running OCR, images undergo preprocessing to maximize recognition accuracy:
* **EXIF Orientation Correction**: Auto-rotates photos taken in portrait/sideways modes on mobile devices so text is always upright.
* **RGB Normalization**: Converts various color palettes (RGBA, palette mode, grayscale) into standard 3-channel RGB.
* **CLAHE Contrast Enhancement**: Applies OpenCV Contrast Limited Adaptive Histogram Equalization to make faded, low-contrast, or unevenly lit text on packaging readable without over-amplifying background noise.

### 2. OCR Engine Integration (`ocr_service.py` & `ocr_engine.py`)
* **Engine Choice**: **EasyOCR** (PyTorch-based, supports English + multilingual scripts, fully compatible with Python 3.14 on Windows).
* **Singleton Model Loading**: The EasyOCR Reader model weights are loaded once in memory upon first call, avoiding costly reload overhead on each request.
* **Async Threadpool Execution**: Model inference runs in a separate thread pool via `run_in_threadpool()` so it never blocks FastAPI's async event loop.
* **Bounding Box Normalization**: Converts polygon corner coordinates into standard axis-aligned bounding boxes `[x1, y1, x2, y2]`.
* **Confidence Filtering**: Discards noisy recognitions below the $50\%$ confidence threshold ($0.50$).

### 3. Formal Data Contracts & Schemas (`extraction.py`)
Defined strongly typed Pydantic models for OCR output:

```python
class OCRRegion(BaseModel):
    text: str                                  # Recognized text string
    confidence: float                          # Confidence score (0.0 to 1.0)
    bbox: List[int]                            # [x1, y1, x2, y2] pixel coordinates

class OCRResult(BaseModel):
    full_text: str                             # Newline-separated text for NLP
    regions: List[OCRRegion]                   # Bounding boxes for DB/UI evidence
```

---

## 📂 File Structure & Architecture

```text
PackWise/
├── data/
│   ├── nlp/                                   # Member 3 standalone NLP prototype
│   │   ├── nlp_engine.py
│   │   └── requirements.txt
│   └── ocr/                                   # Member 2 standalone OCR module
│       ├── ocr_engine.py                      # Standalone OCR & CV Engine
│       ├── requirements.txt                   # EasyOCR, OpenCV, Pillow, NumPy
│       └── test_ocr.py                        # CLI test runner for any image
│
└── backend/
    ├── requirements.txt                       # Backend dependencies (includes OCR)
    └── app/
        ├── schemas/
        │   └── extraction.py                  # OCRRegion & OCRResult models
        └── services/
            ├── image_preprocessor.py          # EXIF fix + RGB + CLAHE contrast
            ├── ocr_service.py                 # Backend OCR service adapter
            └── pipeline_service.py            # Pipeline orchestrator
```

---

## 🔗 Integration Handshake with Other Members

### 🗄️ Member 1 (Backend & DB)
* `pipeline_service.py` calls `ocr_service.extract_text_from_images(image_paths)`.
* Result is saved to the PostgreSQL/Supabase database in the `ocr_results` table (`full_text` as `Text`, `regions` as `JSONB`).

### 🧠 Member 3 (ML / NLP)
* NLP service directly consumes `result["full_text"]` into Gemini's prompt for Legal Metrology field extraction.
* Bounding box pixel heights `(y2 - y1)` provide the `mrp_height_px` and `net_quantity_height_px` hooks for font-height compliance checks.

### ⚖️ Member 4 (Compliance) & 🎨 Member 5 (Frontend)
* The `regions` array provides visual bounding boxes so the frontend can highlight where text was found on the original package image for evidence display.

---

## 🧪 How to Run & Test

From the repository root:

```powershell
# 1. Run with default test image
python data/ocr/test_ocr.py

# 2. Run with any custom product image
python data/ocr/test_ocr.py "C:\path\to\your\product_image.jpg"
```
