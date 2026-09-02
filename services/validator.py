"""
services/validator.py
Validates and standardizes extracted values against dynamic schema definitions and field types.
Implements edge case logic for missing numbers, dates, dropdown options, and booleans.
"""
import re
from datetime import datetime
from typing import Any, Optional, Tuple, List
from models.schemas import FormField, FieldExtraction, ConfidenceLevel


def clean_string_value(val: Any) -> Optional[str]:
    """Cleans and strips text string values."""
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in {"null", "none", "n/a", "not available", "unknown", "nil", "missing", ""}:
        return None
    return s


def validate_number(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Validates and extracts a numeric value.
    If non-numeric or missing, returns (None, error_notice).
    """
    if val is None:
        return None, "No numeric value found in document."
    
    # If already int or float
    if isinstance(val, (int, float)):
        return val, None
    
    s = str(val).strip()
    if not s or s.lower() in {"null", "none", "n/a", "not available"}:
        return None, "No numeric value found in document."

    # Remove currency signs, commas, spaces (e.g., "$1,250.50" -> "1250.50")
    cleaned = re.sub(r"[^\d.-]", "", s)
    
    if not cleaned:
        return None, f"Expected a number, but extracted non-numeric text: '{s}'"

    try:
        if "." in cleaned:
            return float(cleaned), None
        return int(cleaned), None
    except ValueError:
        return None, f"Could not parse numeric value from '{s}'"


def validate_date(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates and formats a date string to ISO YYYY-MM-DD.
    """
    if val is None:
        return None, "No date found in document."
    
    s = str(val).strip()
    if not s or s.lower() in {"null", "none", "n/a", "not available"}:
        return None, "No date found in document."

    # List of supported date formats
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y/%m/%d"
    ]

    for fmt in date_formats:
        try:
            parsed = datetime.strptime(s, fmt)
            return parsed.strftime("%Y-%m-%d"), None
        except ValueError:
            continue

    # If regex matches standard YYYY-MM-DD
    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if match:
        y, m, d = match.groups()
        try:
            parsed = datetime(int(y), int(m), int(d))
            return parsed.strftime("%Y-%m-%d"), None
        except Exception:
            pass

    # If we couldn't strictly parse, return cleaned string with notice
    return s, f"Date format '{s}' may need manual review."


def validate_dropdown(val: Any, options: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates value against dropdown options.
    Matches case-insensitively or fuzzy.
    """
    if val is None:
        return None, "No selection found in document."
    
    s = str(val).strip()
    if not s or s.lower() in {"null", "none", "n/a", "not available"}:
        return None, "No selection found in document."

    if not options:
        return s, None

    # Exact match
    for opt in options:
        if s.lower() == opt.strip().lower():
            return opt, None

    # Partial/Sub-string match
    for opt in options:
        if opt.strip().lower() in s.lower() or s.lower() in opt.strip().lower():
            return opt, None

    return None, f"Extracted '{s}' is not among configured options: {', '.join(options)}"


def validate_checkbox(val: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates boolean checkbox values.
    """
    if val is None:
        return False, None
    
    if isinstance(val, bool):
        return val, None
    
    s = str(val).strip().lower()
    truthy = {"true", "yes", "1", "agreed", "checked", "y", "accept", "accepted", "positive"}
    falsy = {"false", "no", "0", "disagreed", "unchecked", "n", "decline", "declined", "negative", "none", "null"}

    if s in truthy:
        return True, None
    if s in falsy:
        return False, None

    return False, f"Could not determine boolean state from '{val}'"


def validate_field_extraction(
    field: FormField, 
    raw_val: Any, 
    confidence: Optional[str] = None,
    explanation: Optional[str] = None
) -> FieldExtraction:
    """
    Validates raw LLM extraction against a FormField definition.
    Returns a structured FieldExtraction instance.
    """
    clean_raw = clean_string_value(raw_val)
    field_type = field.type
    extracted_val = None
    validation_err = None

    if clean_raw is None and field_type != "checkbox":
        return FieldExtraction(
            field_id=field.id,
            field_label=field.label,
            extracted_value=None,
            raw_value=None,
            confidence="missing",
            explanation=explanation or "Field value not present in the document.",
            validation_error="Missing value in document." if field.required else None,
            is_missing=True,
            is_valid=not field.required
        )

    # Validate according to field type
    if field_type in ("text", "textarea"):
        extracted_val = clean_raw
        validation_err = None

    elif field_type == "number":
        extracted_val, validation_err = validate_number(clean_raw)

    elif field_type == "date":
        extracted_val, validation_err = validate_date(clean_raw)

    elif field_type == "dropdown":
        extracted_val, validation_err = validate_dropdown(clean_raw, field.options)

    elif field_type == "checkbox":
        extracted_val, validation_err = validate_checkbox(clean_raw if clean_raw is not None else raw_val)

    # Determine confidence
    conf: ConfidenceLevel
    if extracted_val is None:
        conf = "missing"
    elif confidence in ("high", "medium", "low"):
        conf = confidence  # type: ignore
    else:
        conf = "high" if validation_err is None else "medium"

    is_missing = extracted_val is None or (field_type == "text" and not str(extracted_val).strip())
    is_valid = validation_err is None and not (field.required and is_missing)

    return FieldExtraction(
        field_id=field.id,
        field_label=field.label,
        extracted_value=extracted_val,
        raw_value=str(raw_val) if raw_val is not None else None,
        confidence=conf,
        explanation=explanation,
        validation_error=validation_err,
        is_missing=is_missing,
        is_valid=is_valid
    )
