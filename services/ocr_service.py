"""
services/ocr_service.py
OCR service for extracting text from images and scanned PDF pages.
Auto-detects Tesseract binary locations on Windows and supports multimodal fallback.
"""
import io
import os
import shutil
from typing import Tuple, Optional
from PIL import Image

try:
    import pytesseract
    import os
    # Auto-detect Windows default Tesseract installation paths
    if os.name == "nt":
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def _init_tesseract_path():
    """Auto-detects and configures tesseract executable on Windows."""
    if not PYTESSERACT_AVAILABLE:
        return

    # Check if 'tesseract' is already in system PATH
    if shutil.which("tesseract"):
        return

    # Common Windows installation directories
    candidate_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return


# Run path discovery at module import
_init_tesseract_path()


def check_ocr_available() -> bool:
    """Checks whether pytesseract can be executed without error."""
    if not PYTESSERACT_AVAILABLE:
        return False
    try:
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        _init_tesseract_path()
        try:
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
        # Re-verify path before run
        _init_tesseract_path()

        # Convert image to RGB or L for optimal OCR recognition
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
            
        text = pytesseract.image_to_string(image)
        if not text.strip():
            return "", None
        return text, None
    except Exception as e:
        err_msg = str(e)
        if "tesseract is not installed or it's not in your PATH" in err_msg.lower() or "tesseractnotfounderror" in err_msg.lower():
            return "", (
                "Tesseract OCR executable was not found in system PATH. "
                "Please verify Tesseract is installed in C:\\Program Files\\Tesseract-OCR."
            )
        return "", f"OCR extraction error: {err_msg}"


def perform_ocr_on_pdf_page(page_pixmap_bytes: bytes) -> Tuple[str, Optional[str]]:
    """OCR wrapper specifically for rendered PDF page pixmaps."""
    return perform_ocr_on_bytes(page_pixmap_bytes)
