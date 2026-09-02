"""
services/document_parser.py
Extracts text and metadata from PDF and image files using PyMuPDF and OCR.
Handles corrupted files, format validation, and digital vs scanned PDF detection.
"""
import io
import os
from typing import Tuple, Optional, Dict, Any
import fitz  # PyMuPDF
from services.ocr_service import perform_ocr_on_bytes, perform_ocr_on_pdf_page


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """
    Validates if the uploaded file has a supported extension.
    Returns (is_valid, error_or_success_message).
    """
    if not filename:
        return False, "No file provided."
    
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Supported formats: PDF, PNG, JPG, JPEG."
    
    return True, "File type is valid."


def extract_text_from_document(
    file_bytes: bytes, 
    filename: str
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    """
    Extracts text from PDF or image document.
    
    Returns:
        (extracted_text, metadata_dict, error_message)
        If error_message is not None, extraction failed.
    """
    if not file_bytes or len(file_bytes) == 0:
        return "", {}, "The uploaded file is empty (0 bytes). Please upload a valid document."

    is_valid, msg = validate_file_extension(filename)
    if not is_valid:
        return "", {}, msg

    _, ext = os.path.splitext(filename.lower())

    # Case 1: Image files (PNG, JPG, JPEG)
    if ext in {".png", ".jpg", ".jpeg"}:
        try:
            ocr_text, ocr_err = perform_ocr_on_bytes(file_bytes)
            if ocr_err:
                return "", {}, f"OCR processing failed for image: {ocr_err}"
            
            clean_text = ocr_text.strip()
            if not clean_text:
                return "", {"type": "image", "pages": 1, "ocr_used": True}, "Image parsed, but no readable text was detected."
            
            return clean_text, {"type": "image", "pages": 1, "ocr_used": True}, None
        except Exception as e:
            return "", {}, f"Corrupted or unreadable image file: {str(e)}"

    # Case 2: PDF Document
    if ext == ".pdf":
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            return "", {}, f"Corrupted PDF file could not be opened: {str(e)}"

        if doc.page_count == 0:
            doc.close()
            return "", {}, "The PDF document contains no pages."

        extracted_pages = []
        ocr_pages_count = 0

        try:
            total_pages = doc.page_count
            for page_index in range(total_pages):
                page = doc.load_page(page_index)
                page_text = page.get_text("text").strip()

                # If text is very sparse (< 25 chars), check if page is a scanned image
                if len(page_text) < 25:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    page_ocr_text, _ = perform_ocr_on_bytes(img_bytes)
                    
                    if len(page_ocr_text.strip()) > len(page_text):
                        page_text = page_ocr_text.strip()
                        ocr_pages_count += 1
                
                if page_text:
                    extracted_pages.append(f"--- Page {page_index + 1} ---\n{page_text}")
            
            doc.close()

            full_text = "\n\n".join(extracted_pages).strip()
            metadata = {
                "type": "pdf",
                "page_count": len(extracted_pages),
                "total_pages": total_pages,
                "ocr_pages": ocr_pages_count,
                "character_count": len(full_text)
            }

            if not full_text:
                return "", metadata, "Document appears empty or contains only non-extractable graphics."

            return full_text, metadata, None

        except Exception as e:
            try:
                if not doc.is_closed:
                    doc.close()
            except Exception:
                pass
            return "", {}, f"Error reading PDF content: {str(e)}"

    return "", {}, f"Unsupported file extension: {ext}"
