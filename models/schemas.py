"""
models/schemas.py
Pydantic schemas and data models for Dynamic Form Builder and AI Document Autofill.
"""
from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid


# Supported field types matching the technical assessment specification
FieldType = Literal[
    "text",          # Single-line text
    "textarea",      # Multi-line text
    "number",        # Number
    "date",          # Date
    "dropdown",      # Dropdown
    "checkbox"       # Checkbox
]

# Supported confidence levels
ConfidenceLevel = Literal["high", "medium", "low", "missing"]


class FormField(BaseModel):
    """Represents a single dynamic field in a form schema."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    type: FieldType = "text"
    required: bool = False
    options: List[str] = Field(default_factory=list)  # Used for dropdown choices
    placeholder: Optional[str] = None
    description: Optional[str] = None


class FormSchema(BaseModel):
    """Container for the full form schema definition."""
    title: str = "Dynamic Document Form"
    description: Optional[str] = "Auto-generated schema-driven form"
    fields: List[FormField] = Field(default_factory=list)

    def get_field_by_id(self, field_id: str) -> Optional[FormField]:
        for f in self.fields:
            if f.id == field_id:
                return f
        return None

    def get_field_by_label(self, label: str) -> Optional[FormField]:
        for f in self.fields:
            if f.label.strip().lower() == label.strip().lower():
                return f
        return None


class FieldExtraction(BaseModel):
    """Extraction output metadata for a single field."""
    field_id: str
    field_label: str
    extracted_value: Any = None
    raw_value: Optional[str] = None
    confidence: ConfidenceLevel = "missing"
    explanation: Optional[str] = None
    validation_error: Optional[str] = None
    is_missing: bool = True
    is_valid: bool = True


class FormExtractionResult(BaseModel):
    """Aggregate result from schema-driven AI document extraction."""
    schema_title: str
    extracted_fields: Dict[str, FieldExtraction] = Field(default_factory=dict)
    unmatched_keys: List[str] = Field(default_factory=list)
    raw_llm_response: Optional[str] = None
    document_name: Optional[str] = None
    extraction_timestamp: Optional[str] = None


class SubmissionRecord(BaseModel):
    """Data model for saved form submissions."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    submission_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str
    schema_snapshot: Any
    document_name: Optional[str] = None
    form_data: Dict[str, Any] = Field(default_factory=dict)
    field_metadata: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
