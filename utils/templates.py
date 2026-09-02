"""
utils/templates.py
Pre-configured schema templates for common real-world use cases:
1. Job Application
2. Supplier Invoice
3. Medical Intake
"""
from models.schemas import FormSchema, FormField


def get_job_application_template() -> FormSchema:
    """Returns standard Job Application form schema matching assessment example."""
    return FormSchema(
        title="Job Application Form",
        description="Candidate evaluation and screening intake form",
        fields=[
            FormField(id="cand_name", label="Candidate Name", type="text", required=True, placeholder="e.g. John Doe"),
            FormField(id="cand_email", label="Email Address", type="text", required=True, placeholder="e.g. john.doe@email.com"),
            FormField(id="cand_skills", label="Professional Skills", type="textarea", required=False, placeholder="e.g. Python, Streamlit, Machine Learning"),
            FormField(id="cand_exp", label="Years of Experience", type="number", required=True, placeholder="e.g. 3"),
            FormField(id="cand_start", label="Start Date", type="date", required=False, placeholder="YYYY-MM-DD"),
            FormField(id="cand_dept", label="Department", type="dropdown", required=True, options=["Engineering", "Product", "Data Science", "Design", "Sales"]),
            FormField(id="cand_terms", label="Agreement to Terms", type="checkbox", required=True, description="Candidate confirms accuracy of submitted information")
        ]
    )


def get_supplier_invoice_template() -> FormSchema:
    """Returns standard Supplier Invoice form schema."""
    return FormSchema(
        title="Supplier Invoice Entry",
        description="Accounts payable invoice verification schema",
        fields=[
            FormField(id="inv_num", label="Invoice Number", type="text", required=True, placeholder="e.g. INV-2026-089"),
            FormField(id="inv_vendor", label="Vendor / Company Name", type="text", required=True, placeholder="e.g. Acme Cloud Corp"),
            FormField(id="inv_total", label="Total Amount", type="number", required=True, placeholder="e.g. 4500.00"),
            FormField(id="inv_date", label="Invoice Date", type="date", required=True, placeholder="YYYY-MM-DD"),
            FormField(id="inv_terms", label="Payment Terms", type="dropdown", required=False, options=["Net 30", "Net 60", "Due on Receipt", "Advance"]),
            FormField(id="inv_notes", label="Itemized Description", type="textarea", required=False, placeholder="Services or products billed")
        ]
    )


def get_medical_intake_template() -> FormSchema:
    """Returns standard Medical Intake form schema."""
    return FormSchema(
        title="Patient Medical Intake",
        description="Clinical registration and health history schema",
        fields=[
            FormField(id="med_patient", label="Patient Full Name", type="text", required=True, placeholder="e.g. Sarah Connor"),
            FormField(id="med_dob", label="Date of Birth", type="date", required=True, placeholder="YYYY-MM-DD"),
            FormField(id="med_blood", label="Blood Group", type="dropdown", required=False, options=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
            FormField(id="med_history", label="Pre-existing Conditions", type="textarea", required=False, placeholder="e.g. Hypertension, Asthma"),
            FormField(id="med_emergency", label="Emergency Contact Number", type="text", required=True, placeholder="e.g. +1 555-0199"),
            FormField(id="med_consent", label="Consent to Treatment", type="checkbox", required=True, description="Patient confirms consent for medical evaluation")
        ]
    )


BUILTIN_TEMPLATES = {
    "Job Application": get_job_application_template,
    "Supplier Invoice": get_supplier_invoice_template,
    "Medical Intake": get_medical_intake_template
}
