"""
tests/test_all.py
Automated test suite verifying schemas, document parser, validator, AI prompt construction, and persistence.
"""
import pytest
import json
import os
from models.schemas import FormSchema, FormField
from services.document_parser import extract_text_from_document, validate_file_extension
from services.validator import (
    validate_number,
    validate_date,
    validate_dropdown,
    validate_checkbox,
    validate_field_extraction
)
from services.ai_extractor import build_dynamic_prompt, mock_heuristic_extraction
from utils.templates import get_job_application_template, get_supplier_invoice_template
from utils.helpers import (
    save_submission,
    load_all_submissions,
    export_schema_to_json,
    import_schema_from_json,
    create_sample_pdf_documents
)


def test_schema_creation_and_serialization():
    """Verify dynamic schema construction and JSON export/import."""
    schema = FormSchema(
        title="Custom Test Form",
        description="Testing schema",
        fields=[
            FormField(id="f1", label="Full Name", type="text", required=True),
            FormField(id="f2", label="Salary", type="number", required=False),
            FormField(id="f3", label="Status", type="dropdown", required=True, options=["Active", "Inactive"])
        ]
    )
    assert len(schema.fields) == 3
    assert schema.get_field_by_id("f1").label == "Full Name"
    assert schema.get_field_by_label("salary").type == "number"

    # Export & Import
    json_str = export_schema_to_json(schema)
    reloaded = import_schema_from_json(json_str)
    assert reloaded.title == "Custom Test Form"
    assert len(reloaded.fields) == 3
    assert reloaded.fields[2].options == ["Active", "Inactive"]


def test_document_validation_and_parsing():
    """Verify file extension validation and PDF extraction."""
    # Unsupported extension
    is_valid, err = validate_file_extension("archive.zip")
    assert not is_valid
    assert "Unsupported" in err

    # Valid extension
    is_valid, _ = validate_file_extension("document.pdf")
    assert is_valid

    # Generate and parse sample PDF
    resume_path, _, _ = create_sample_pdf_documents()
    with open(resume_path, "rb") as f:
        file_bytes = f.read()

    text, meta, error = extract_text_from_document(file_bytes, "sample_resume.pdf")
    assert error is None
    assert "JOHN DOE" in text
    assert meta["type"] == "pdf"


def test_validator_edge_cases():
    """Verify type-checking, edge-case number parsing, dates, dropdowns, and checkboxes."""
    # 1. Number validation
    num_val, err = validate_number("$4,500.50")
    assert num_val == 4500.50
    assert err is None

    num_val, err = validate_number("not a number")
    assert num_val is None
    assert err is not None

    num_val, err = validate_number(None)
    assert num_val is None

    # 2. Date validation
    d_val, err = validate_date("2026-08-15")
    assert d_val == "2026-08-15"
    assert err is None

    # 3. Dropdown validation
    drop_val, err = validate_dropdown("engineering", ["Engineering", "Product", "Sales"])
    assert drop_val == "Engineering"
    assert err is None

    drop_val, err = validate_dropdown("unknown_dept", ["Engineering", "Product"])
    assert drop_val is None
    assert err is not None

    # 4. Checkbox validation
    assert validate_checkbox("yes")[0] is True
    assert validate_checkbox("true")[0] is True
    assert validate_checkbox("no")[0] is False
    assert validate_checkbox("false")[0] is False


def test_dynamic_prompt_builder():
    """Verify prompt is generated dynamically without hardcoded fields."""
    schema = FormSchema(
        title="Custom Dynamic Form",
        fields=[
            FormField(id="x1", label="Custom Metric A", type="number", required=True),
            FormField(id="x2", label="Custom Notes B", type="textarea", required=False)
        ]
    )
    prompt = build_dynamic_prompt(schema, "Document text sample")
    assert "Custom Metric A" in prompt
    assert "Custom Notes B" in prompt
    assert "REQUIRED" in prompt


def test_offline_heuristic_extraction():
    """Verify fallback extractor populates schema fields."""
    schema = get_job_application_template()
    doc_text = """Candidate Name: Alice Smith
Years of Experience: 5
Department: Engineering
Agreement to Terms: agreed
"""
    raw_json = mock_heuristic_extraction(schema, doc_text)
    data = json.loads(raw_json)
    extracted = data["extracted_data"]
    assert len(extracted) == len(schema.fields)
    
    # Check Candidate Name extracted
    name_item = next(item for item in extracted if item["field_id"] == "cand_name")
    assert "Alice Smith" in name_item["value"]


def test_submission_persistence():
    """Verify saving and retrieving submissions."""
    schema = get_supplier_invoice_template()
    form_data = {
        "inv_num": "INV-TEST-001",
        "inv_vendor": "Test Vendor LLC",
        "inv_total": 999.99
    }
    saved_path = save_submission(schema, form_data, document_name="test_inv.pdf")
    assert os.path.exists(saved_path)

    submissions = load_all_submissions()
    assert len(submissions) >= 1
    latest = submissions[0]
    assert "submission_id" in latest
