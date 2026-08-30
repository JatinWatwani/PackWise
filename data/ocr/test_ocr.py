import sys
import os
from pathlib import Path

# Ensure the current data/ocr directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ocr_engine import extract_ocr_data

# Default image fallback if none is provided via command line
DEFAULT_IMAGE = r"C:\Users\Pranav\Downloads\Screenshot 2026-08-30 164320.png"

def main():
    # If an image path was passed in the terminal, use it; otherwise use default
    if len(sys.argv) > 1:
        image_path = sys.argv[1].strip('"').strip("'")
    else:
        image_path = DEFAULT_IMAGE

    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found at:\n   {image_path}")
        return

    print(f"🔍 Processing Image with OCR Engine: {image_path}\n")
    result = extract_ocr_data(image_path)
    
    print("=" * 45)
    print(" 📝 FULL TEXT EXTRACTED:")
    print("=" * 45)
    if result.get("full_text", "").strip():
        print(result["full_text"])
    else:
        print("(No text detected with >50% confidence)")
        
    print("\n" + "=" * 45)
    print(f" 🎯 REGIONS FOUND ({len(result.get('regions', []))}):")
    print("=" * 45)
    for idx, r in enumerate(result.get("regions", []), 1):
        print(f"{idx:2d}. '{r['text']}' (Conf: {r['confidence']:.2f}) | BBox: {r['bbox']}")

if __name__ == "__main__":
    main()
