"""
services/ocr_service.py
OCR service for extracting text from images and scanned PDF pages.
Handles Tesseract OCR if available, with graceful fallback and error reporting.
"""
import io
import logging
from typing import Tuple, Optional
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def check_ocr_available() -> bool:
    """Checks whether pytesseract can be executed without error."""
    if not PYTESSERACT_AVAILABLE:
        return False
    try:
        # Check version or run quick dummy test
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def perform_ocr_on_bytes(image_bytes: bytes) -> Tuple[str, Optional[str]]:
    """
    Performs OCR on raw image bytes.
    Returns: (extracted_text, error_message)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return "", f"Could not load image file: {str(e)}"

    if not PYTESSERACT_AVAILABLE:
        return "", "OCR engine (pytesseract) is not installed."

    try:
        # Convert to RGB or Grayscale if needed
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
            
        text = pytesseract.image_to_string(image)
        return text, None
    except Exception as e:
        # Check if tesseract binary is missing from PATH
        err_msg = str(e)
        if "tesseract is not installed or it's not in your PATH" in err_msg.lower() or "tesseractnotfounderror" in err_msg.lower():
            return "", (
                "Tesseract OCR executable is not found in system PATH. "
                "Digital text PDFs will work directly. For scanned images, please install Tesseract-OCR."
            )
        return "", f"OCR extraction error: {err_msg}"


def perform_ocr_on_pdf_page(page_pixmap_bytes: bytes) -> Tuple[str, Optional[str]]:
    """OCR wrapper specifically for rendered PDF page pixmaps."""
    return perform_ocr_on_bytes(page_pixmap_bytes)
