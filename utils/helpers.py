"""
utils/helpers.py
Helper utilities for data persistence, schema export/import, and generating sample test documents.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF

from models.schemas import FormSchema, FormField, SubmissionRecord


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submissions")
SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")


def ensure_directories():
    """Ensures data and samples directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)


def save_submission(
    schema: Any,
    form_data: Dict[str, Any],
    document_name: Optional[str] = None,
    field_metadata: Optional[Dict[str, Dict[str, Any]]] = None
) -> str:
    """
    Saves the final completed form submission as a JSON record.
    Returns: file_path of saved submission.
    """
    ensure_directories()
    sub_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Serialize schema safely
    if hasattr(schema, "model_dump"):
        schema_data = schema.model_dump()
    elif hasattr(schema, "dict"):
        schema_data = schema.dict()
    elif isinstance(schema, dict):
        schema_data = schema
    else:
        schema_data = str(schema)

    record = SubmissionRecord(
        submission_id=sub_id,
        timestamp=timestamp,
        schema_snapshot=schema_data,
        document_name=document_name,
        form_data=form_data,
        field_metadata=field_metadata or {}
    )

    filename = f"submission_{file_timestamp}_{sub_id}.json"
    file_path = os.path.join(DATA_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2)

    return file_path


def load_all_submissions() -> List[Dict[str, Any]]:
    """Loads all saved submission records."""
    ensure_directories()
    records = []
    for fname in sorted(os.listdir(DATA_DIR), reverse=True):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records.append(data)
            except Exception:
                continue
    return records


def export_schema_to_json(schema: FormSchema) -> str:
    """Exports FormSchema model to a formatted JSON string."""
    return json.dumps(schema.model_dump(), indent=2)


def import_schema_from_json(json_str: str) -> FormSchema:
    """Imports and validates a FormSchema from JSON string."""
    data = json.loads(json_str)
    return FormSchema(**data)


def create_sample_pdf_documents():
    """Generates sample test PDF files for instant evaluation."""
    ensure_directories()
    
    # 1. Sample Resume
    resume_path = os.path.join(SAMPLE_DOCS_DIR, "sample_resume.pdf")
    if not os.path.exists(resume_path):
        doc = fitz.open()
        page = doc.new_page()
        text = """JOHN DOE
Software Engineer & AI Specialist
Email: john.doe@email.com | Phone: +1 (555) 019-2834
Location: San Francisco, CA

PROFESSIONAL SUMMARY
Experienced Software Engineer with 4 years of hands-on experience building scalable web applications and AI tools.

PROFESSIONAL SKILLS
- Languages: Python, JavaScript, TypeScript, SQL
- Frameworks & Libraries: React, Node.js, FastAPI, Streamlit, PyTorch
- Core Expertise: REST APIs, Document Processing, Dynamic UIs, Cloud Deployment

WORK EXPERIENCE
Senior Full Stack Developer — TechNova Solutions (2022 – Present)
- Designed and maintained microservices using Python and FastAPI.
- Built dynamic frontend dashboards in React.

PREVIOUS EXPERIENCE
Junior AI Developer — DataMinds Inc (2020 – 2022)
- Extracted and classified structured data from enterprise PDFs.

EDUCATION & PREFERENCES
- B.S. Computer Science — University of California (2020)
- Target Department: Engineering
- Available Start Date: 2026-10-01
- Terms & Conditions: I hereby confirm that all information provided in this document is accurate and truthful.
"""
        page.insert_text((50, 50), text, fontsize=11)
        doc.save(resume_path)
        doc.close()

    # 2. Sample Invoice
    invoice_path = os.path.join(SAMPLE_DOCS_DIR, "sample_invoice.pdf")
    if not os.path.exists(invoice_path):
        doc = fitz.open()
        page = doc.new_page()
        text = """INVOICE
Vendor: Apex Cloud Infrastructure LLC
Invoice Number: INV-2026-9814
Invoice Date: 2026-08-15
Payment Terms: Net 30

BILLED TO:
Enterprise Solutions Corp.
100 Innovation Way, Suite 400

DESCRIPTION OF SERVICES:
1. Enterprise Cloud Hosting & Cluster Storage (Q3) - $3,200.00
2. AI Inference Dedicated Gateway Setup - $1,300.00

TOTAL AMOUNT DUE: $4,500.00
Due Date: 2026-09-14
Tax ID: US-882910394
"""
        page.insert_text((50, 50), text, fontsize=11)
        doc.save(invoice_path)
        doc.close()

    # 3. Sample Medical Intake Record / Receipt
    medical_path = os.path.join(SAMPLE_DOCS_DIR, "sample_medical_intake.pdf")
    if not os.path.exists(medical_path):
        doc = fitz.open()
        page = doc.new_page()
        text = """METROPOLITAN GENERAL HOSPITAL
PATIENT ADMISSION & MEDICAL INTAKE RECEIPT
Date of Visit: 2026-08-20

PATIENT INFORMATION:
- Patient Full Name: Sarah Connor
- Date of Birth: 1985-05-14
- Blood Group: O+
- Gender: Female
- Emergency Contact Number: +1 555-0199 (John Connor - Relationship: Son)

CLINICAL & HEALTH HISTORY:
- Pre-existing Conditions: Mild asthma, seasonal pollen allergies, hypertension under observation.
- Current Medications: Albuterol inhaler as needed.
- Primary Physician: Dr. Robert Vance, MD

CONSENT & DECLARATION:
Consent to Treatment: I hereby grant full consent to Metropolitan General Hospital and attending medical staff for necessary clinical evaluation, diagnostics, and emergency treatment.
Patient Signature: [Confirmed / Signed Digitally]
"""
        page.insert_text((50, 50), text, fontsize=11)
        doc.save(medical_path)
        doc.close()

    return resume_path, invoice_path, medical_path
