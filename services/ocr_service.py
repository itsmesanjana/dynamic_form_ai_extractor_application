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


def _extract_text_via_ai_vision(image_bytes: bytes) -> Tuple[str, Optional[str]]:
    """Fallback OCR using Multimodal Vision (Groq / Gemini) when local OCR binary is unavailable."""
    import base64
    from dotenv import load_dotenv
    load_dotenv()

    # Try Gemini Vision
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            img = Image.open(io.BytesIO(image_bytes))
            response = model.generate_content([
                "Extract and transcribe all text from this image exactly as written. Return ONLY the transcribed text.",
                img
            ])
            if response.text:
                return response.text.strip(), None
        except Exception:
            pass

    # Try Groq Vision
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            base64_img = base64.b64encode(image_bytes).decode("utf-8")
            
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract and transcribe all readable text from this document image exactly as written. Return only the extracted text."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ]
            )
            if completion.choices and completion.choices[0].message.content:
                return completion.choices[0].message.content.strip(), None
        except Exception:
            pass

    return "", "OCR engine (pytesseract) is not found in system PATH, and no AI Vision fallback key was provided."


def perform_ocr_on_bytes(image_bytes: bytes) -> Tuple[str, Optional[str]]:
    """
    Performs OCR on raw image bytes.
    Tries Tesseract first, with automatic fallback to Multimodal Vision OCR.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return "", f"Could not load image file: {str(e)}"

    if not PYTESSERACT_AVAILABLE:
        return _extract_text_via_ai_vision(image_bytes)

    try:
        # Re-verify path before run
        _init_tesseract_path()

        # Convert image to RGB or L for optimal OCR recognition
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
            
        text = pytesseract.image_to_string(image)
        if text and text.strip():
            return text.strip(), None
    except Exception:
        pass

    # Fallback to AI Vision OCR if pytesseract failed or returned empty
    vision_text, vision_err = _extract_text_via_ai_vision(image_bytes)
    if vision_text:
        return vision_text, None

    return "", vision_err or "No readable text detected in image."


def perform_ocr_on_pdf_page(page_pixmap_bytes: bytes) -> Tuple[str, Optional[str]]:
    """OCR wrapper specifically for rendered PDF page pixmaps."""
    return perform_ocr_on_bytes(page_pixmap_bytes)
