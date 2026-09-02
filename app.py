"""
app.py
FormAI - Next-Gen Dynamic Form Builder & AI Document Autofill.
Built with Streamlit, PyMuPDF, OCR, Pydantic, and Groq/Gemini AI.
"""
import os
import json
from datetime import datetime
import streamlit as st

from models.schemas import FormSchema, FormField, FieldExtraction
from services.document_parser import extract_text_from_document, validate_file_extension
from services.ai_extractor import run_schema_driven_extraction
from services.validator import validate_field_extraction
from utils.templates import BUILTIN_TEMPLATES, get_job_application_template
from utils.helpers import (
    save_submission,
    load_all_submissions,
    export_schema_to_json,
    import_schema_from_json,
    create_sample_pdf_documents
)

# Page configuration
st.set_page_config(
    page_title="FormAI | AI Schema Builder & Autofill",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End SaaS CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Banner / Hero */
    .hero-container {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.15) 0%, rgba(124, 58, 237, 0.08) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366F1 0%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.02rem;
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Stepper Navigation */
    .stepper-container {
        display: flex;
        gap: 10px;
        margin-bottom: 24px;
        background: rgba(30, 41, 59, 0.5);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(51, 65, 85, 0.6);
    }
    
    /* Metric & Action Cards */
    .saas-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .saas-card:hover {
        border-color: #6366F1;
    }
    
    .field-row-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .field-row-card:hover {
        border-color: #4F46E5;
        background: rgba(15, 23, 42, 0.85);
    }
    
    /* Type Chips */
    .type-chip {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-family: 'JetBrains Mono', monospace;
    }
    .chip-text { background: rgba(59, 130, 246, 0.18); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
    .chip-number { background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .chip-date { background: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .chip-dropdown { background: rgba(168, 85, 247, 0.18); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }
    .chip-checkbox { background: rgba(236, 72, 153, 0.18); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.3); }

    /* Status Badges */
    .badge-high {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-med {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Live Preview Container */
    .preview-canvas {
        background: #0F172A;
        border: 2px dashed #334155;
        border-radius: 14px;
        padding: 24px;
        min-height: 400px;
    }
    
    /* Stat Badge */
    .stat-pill {
        background: #1E293B;
        border: 1px solid #334155;
        padding: 12px 18px;
        border-radius: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Generate sample documents for quick evaluation
create_sample_pdf_documents()

# Initialize Session State
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

if "schema" not in st.session_state:
    st.session_state.schema = get_job_application_template()

if "uploaded_doc_bytes" not in st.session_state:
    st.session_state.uploaded_doc_bytes = None

if "uploaded_doc_name" not in st.session_state:
    st.session_state.uploaded_doc_name = None

if "document_text" not in st.session_state:
    st.session_state.document_text = ""

if "document_meta" not in st.session_state:
    st.session_state.document_meta = {}

if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None

if "form_values" not in st.session_state:
    st.session_state.form_values = {}

if "extraction_performed" not in st.session_state:
    st.session_state.extraction_performed = False

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 15px;'>
        <div style='background: linear-gradient(135deg, #4F46E5, #9333EA); padding: 8px 12px; border-radius: 10px; font-size: 1.3rem; font-weight: bold;'>⚡</div>
        <div>
            <div style='font-weight: 800; font-size: 1.25rem; color: #F8FAFC;'>FormAI Studio</div>
            <div style='font-size: 0.75rem; color: #94A3B8;'>Schema Extraction Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("🔑 AI Extraction Engine")
    default_groq = os.getenv("GROQ_API_KEY", "")
    default_gem = os.getenv("GEMINI_API_KEY", "")
    
    default_provider_idx = 1 if default_groq else (0 if default_gem else 1)
    
    api_provider = st.selectbox(
        "Active LLM Provider",
        ["Google Gemini API", "Groq API", "Offline Heuristic Mode"],
        index=default_provider_idx,
        help="Select your AI engine for document extraction."
    )

    gemini_key = ""
    groq_key = ""
    if api_provider == "Google Gemini API":
        gemini_key = st.text_input(
            "Gemini API Key",
            value=default_gem,
            type="password",
            help="Enter your Gemini API key or set in .env"
        )
        if not gemini_key:
            st.info("💡 No key? App automatically uses offline semantic parsing without crashing.")
    elif api_provider == "Groq API":
        groq_key = st.text_input(
            "Groq API Key",
            value=default_groq,
            type="password",
            help="Enter your Groq API key or set in .env"
        )
        if groq_key:
            st.success("⚡ Groq Engine active & ready!")

    st.divider()

    st.subheader("📑 Industry Form Templates")
    chosen_tmpl = st.selectbox("Select Schema Template", list(BUILTIN_TEMPLATES.keys()))
    if st.button("Apply Template 🪄", use_container_width=True):
        st.session_state.schema = BUILTIN_TEMPLATES[chosen_tmpl]()
        st.session_state.form_values = {}
        st.session_state.extraction_result = None
        st.session_state.extraction_performed = False
        st.success(f"Applied '{chosen_tmpl}' schema!")
        st.rerun()

    st.divider()
    st.subheader("💾 Schema Portability")
    col_exp, col_imp = st.columns(2)
    with col_exp:
        schema_json = export_schema_to_json(st.session_state.schema)
        st.download_button(
            "Export JSON",
            data=schema_json,
            file_name=f"form_schema_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    with col_imp:
        uploaded_schema = st.file_uploader("Import JSON", type=["json"], label_visibility="collapsed")
        if uploaded_schema is not None:
            try:
                content = uploaded_schema.read().decode("utf-8")
                st.session_state.schema = import_schema_from_json(content)
                st.success("Schema imported!")
                st.rerun()
            except Exception as e:
                st.error(f"Invalid schema: {e}")

    st.divider()
    st.caption("Tecnots AI Engineer Technical Assessment")


# ==========================================
# HERO HEADER & INTERACTIVE STEPPER
# ==========================================
st.markdown("""
<div class='hero-container'>
    <div class='hero-title'>AI-Powered Dynamic Form Builder & Document Autofill</div>
    <div class='hero-subtitle'>Build dynamic schemas at runtime, upload documents (PDF/images), extract data via multimodal LLMs with zero-guess policies, and review/save records.</div>
</div>
""", unsafe_allow_html=True)

steps = [
    ("1. Build Form", 1, "🛠️"),
    ("2. Upload Document", 2, "📄"),
    ("3. AI Extraction", 3, "⚡"),
    ("4. Review & Edit", 4, "✏️"),
    ("5. Submissions", 5, "📁")
]

step_cols = st.columns(len(steps))
for idx, (label, s_num, icon) in enumerate(steps):
    with step_cols[idx]:
        if st.session_state.current_step == s_num:
            st.button(f"{icon} {label}", key=f"step_nav_{s_num}", use_container_width=True, type="primary")
        else:
            if st.button(f"{icon} {label}", key=f"step_nav_{s_num}", use_container_width=True):
                st.session_state.current_step = s_num
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ==========================================
# STEP 1: DYNAMIC FORM BUILDER
# ==========================================
if st.session_state.current_step == 1:
    col_builder, col_preview = st.columns([1.15, 0.85], gap="large")

    with col_builder:
        st.markdown("### 🛠️ Schema Configuration")
        st.caption("Design custom fields dynamically. The application is completely schema-driven.")

        with st.container():
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.session_state.schema.title = st.text_input("Form Title", value=st.session_state.schema.title)
            st.session_state.schema.description = st.text_input("Form Description", value=st.session_state.schema.description or "")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("#### ➕ Add Dynamic Field")
        with st.form("add_field_form", clear_on_submit=True):
            f_label = st.text_input("Field Label *", placeholder="e.g. Total Amount / Candidate Name / Blood Group")
            c_type, c_req = st.columns([2, 1])
            with c_type:
                f_type = st.selectbox(
                    "Field Type *",
                    ["text", "textarea", "number", "date", "dropdown", "checkbox"],
                    format_func=lambda x: {
                        "text": "Single-line Text",
                        "textarea": "Multi-line Text",
                        "number": "Number (Numeric)",
                        "date": "Date (ISO Format)",
                        "dropdown": "Dropdown Selection",
                        "checkbox": "Checkbox (Boolean)"
                    }[x]
                )
            with c_req:
                st.write("")
                st.write("")
                f_required = st.checkbox("Required Field", value=False)

            f_placeholder = st.text_input("Placeholder / Prompt Hint (Optional)", placeholder="e.g. Enter value")
            f_options_str = st.text_input("Dropdown Options (comma-separated, if Dropdown)", placeholder="Option A, Option B, Option C")

            submit_field = st.form_submit_button("➕ Append Field to Schema", use_container_width=True, type="primary")
            if submit_field:
                if not f_label.strip():
                    st.error("Please provide a field label.")
                else:
                    options_list = [opt.strip() for opt in f_options_str.split(",") if opt.strip()] if f_type == "dropdown" else []
                    new_field = FormField(
                        label=f_label.strip(),
                        type=f_type,  # type: ignore
                        required=f_required,
                        placeholder=f_placeholder.strip() if f_placeholder else None,
                        options=options_list
                    )
                    st.session_state.schema.fields.append(new_field)
                    st.success(f"Added '{f_label}' to schema!")
                    st.rerun()

        st.markdown(f"#### 📋 Configured Fields ({len(st.session_state.schema.fields)})")
        if not st.session_state.schema.fields:
            st.info("No fields in current schema. Use the builder above or apply a template from the sidebar.")
        else:
            for idx, field in enumerate(st.session_state.schema.fields):
                with st.expander(f"{idx+1}. {field.label} {'*' if field.required else ''} — [{field.type.upper()}]", expanded=False):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        field.label = st.text_input("Label", value=field.label, key=f"edit_lbl_{field.id}")
                        field.required = st.checkbox("Required", value=field.required, key=f"edit_req_{field.id}")
                    with c2:
                        if field.type == "dropdown":
                            opts_val = ", ".join(field.options)
                            new_opts = st.text_input("Options", value=opts_val, key=f"edit_opts_{field.id}")
                            field.options = [o.strip() for o in new_opts.split(",") if o.strip()]
                    with c3:
                        c_up, c_down = st.columns(2)
                        with c_up:
                            if idx > 0 and st.button("⬆️", key=f"up_{field.id}"):
                                st.session_state.schema.fields[idx], st.session_state.schema.fields[idx-1] = (
                                    st.session_state.schema.fields[idx-1], st.session_state.schema.fields[idx]
                                )
                                st.rerun()
                        with c_down:
                            if idx < len(st.session_state.schema.fields) - 1 and st.button("⬇️", key=f"down_{field.id}"):
                                st.session_state.schema.fields[idx], st.session_state.schema.fields[idx+1] = (
                                    st.session_state.schema.fields[idx+1], st.session_state.schema.fields[idx]
                                )
                                st.rerun()
                        if st.button("🗑️ Remove", key=f"del_{field.id}", use_container_width=True):
                            st.session_state.schema.fields.pop(idx)
                            st.rerun()

    with col_preview:
        st.markdown("### 👁️ Live Form Preview")
        st.caption("Real-time visual rendering of the active schema.")
        
        with st.container(border=True):
            st.markdown(f"### {st.session_state.schema.title}")
            if st.session_state.schema.description:
                st.caption(st.session_state.schema.description)
            st.divider()

            if not st.session_state.schema.fields:
                st.markdown("<div style='text-align: center; color: #64748B; padding: 40px;'>No fields configured yet. Add fields on the left.</div>", unsafe_allow_html=True)
            else:
                for f in st.session_state.schema.fields:
                    req_star = " <span style='color:#EF4444;'>*</span>" if f.required else ""
                    chip_class = f"chip-{f.type}" if f.type in ["text", "number", "date", "dropdown", "checkbox"] else "chip-text"
                    
                    st.markdown(f"**{f.label}**{req_star} <span class='type-chip {chip_class}'>{f.type}</span>", unsafe_allow_html=True)
                    
                    if f.type == "text":
                        st.text_input(f.label, placeholder=f.placeholder or "Text value", key=f"prev_{f.id}", label_visibility="collapsed", disabled=True)
                    elif f.type == "textarea":
                        st.text_area(f.label, placeholder=f.placeholder or "Multi-line text", key=f"prev_{f.id}", label_visibility="collapsed", disabled=True)
                    elif f.type == "number":
                        st.number_input(f.label, value=0.0, key=f"prev_{f.id}", label_visibility="collapsed", disabled=True)
                    elif f.type == "date":
                        st.date_input(f.label, key=f"prev_{f.id}", label_visibility="collapsed", disabled=True)
                    elif f.type == "dropdown":
                        opts = f.options if f.options else ["No options"]
                        st.selectbox(f.label, opts, key=f"prev_{f.id}", label_visibility="collapsed", disabled=True)
                    elif f.type == "checkbox":
                        st.checkbox(f.description or "I confirm / agree to terms", key=f"prev_{f.id}", disabled=True)
                    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Proceed to Document Upload ➡️", type="primary", use_container_width=True):
            if not st.session_state.schema.fields:
                st.warning("⚠️ Please configure at least one field before proceeding.")
            else:
                st.session_state.current_step = 2
                st.rerun()

# ==========================================
# STEP 2: DOCUMENT UPLOAD
# ==========================================
elif st.session_state.current_step == 2:
    st.markdown("### 📄 Document Ingestion")
    st.caption("Upload structured or unstructured documents for automated text parsing.")

    if not st.session_state.schema.fields:
        st.error("⚠️ **Form Schema is Empty!** Please define schema fields in Step 1 before uploading documents.")
        if st.button("⬅️ Return to Step 1: Build Form", type="primary"):
            st.session_state.current_step = 1
            st.rerun()
    else:
        st.info(f"Target Schema: **{st.session_state.schema.title}** ({len(st.session_state.schema.fields)} fields defined)")

        col_up, col_samples = st.columns([1.1, 0.9], gap="large")

        with col_up:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("#### 📤 Upload File")
            uploaded_file = st.file_uploader(
                "Select PDF or Image Document",
                type=["pdf", "png", "jpg", "jpeg"],
                help="Accepts .pdf, .png, .jpg, .jpeg"
            )

            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name

                is_valid, val_msg = validate_file_extension(filename)
                if not is_valid:
                    st.error(f"❌ {val_msg}")
                else:
                    with st.spinner("Extracting text and structural metadata..."):
                        extracted_text, metadata, error = extract_text_from_document(file_bytes, filename)

                    if error:
                        st.error(f"❌ **Extraction Error**: {error}")
                    else:
                        st.session_state.uploaded_doc_bytes = file_bytes
                        st.session_state.uploaded_doc_name = filename
                        st.session_state.document_text = extracted_text
                        st.session_state.document_meta = metadata

                        st.success(f"✅ **{filename}** successfully parsed!")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Doc Format", metadata.get('type', 'PDF').upper())
                        with c2:
                            st.metric("Pages", metadata.get('page_count', 1))
                        with c3:
                            st.metric("Characters", metadata.get('character_count', len(extracted_text)))

                        if st.button("Proceed to AI Extraction ⚡", type="primary", use_container_width=True):
                            st.session_state.current_step = 3
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_samples:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("#### 🧪 Benchmark Sample Documents")
            st.caption("Load verified test documents to evaluate extraction accuracy instantly:")

            sample_dir = os.path.join(os.path.dirname(__file__), "data", "samples")
            sample_resume = os.path.join(sample_dir, "sample_resume.pdf")
            sample_invoice = os.path.join(sample_dir, "sample_invoice.pdf")
            sample_medical = os.path.join(sample_dir, "sample_medical_intake.pdf")

            if os.path.exists(sample_resume):
                with open(sample_resume, "rb") as f:
                    resume_bytes = f.read()
                if st.button("📄 Load Candidate Resume PDF", use_container_width=True):
                    extracted_text, metadata, _ = extract_text_from_document(resume_bytes, "sample_resume.pdf")
                    st.session_state.uploaded_doc_bytes = resume_bytes
                    st.session_state.uploaded_doc_name = "sample_resume.pdf"
                    st.session_state.document_text = extracted_text
                    st.session_state.document_meta = metadata
                    st.success("Loaded Candidate Resume!")
                    st.rerun()

            if os.path.exists(sample_invoice):
                with open(sample_invoice, "rb") as f:
                    inv_bytes = f.read()
                if st.button("🧾 Load Supplier Invoice PDF", use_container_width=True):
                    extracted_text, metadata, _ = extract_text_from_document(inv_bytes, "sample_invoice.pdf")
                    st.session_state.uploaded_doc_bytes = inv_bytes
                    st.session_state.uploaded_doc_name = "sample_invoice.pdf"
                    st.session_state.document_text = extracted_text
                    st.session_state.document_meta = metadata
                    st.success("Loaded Supplier Invoice!")
                    st.rerun()

            if os.path.exists(sample_medical):
                with open(sample_medical, "rb") as f:
                    med_bytes = f.read()
                if st.button("🏥 Load Medical Intake Receipt PDF", use_container_width=True):
                    extracted_text, metadata, _ = extract_text_from_document(med_bytes, "sample_medical_intake.pdf")
                    st.session_state.uploaded_doc_bytes = med_bytes
                    st.session_state.uploaded_doc_name = "sample_medical_intake.pdf"
                    st.session_state.document_text = extracted_text
                    st.session_state.document_meta = metadata
                    st.success("Loaded Medical Intake Receipt!")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.document_text:
            with st.expander("🔍 View Raw Extracted Document Text", expanded=False):
                st.text_area("Document Content", value=st.session_state.document_text, height=180, disabled=True)

# ==========================================
# STEP 3: AI EXTRACTION
# ==========================================
elif st.session_state.current_step == 3:
    st.markdown("### ⚡ Schema-Driven AI Extraction")
    st.caption("Extracts field-specific values dynamically without hallucination or hardcoding.")

    if not st.session_state.schema.fields:
        st.error("No schema fields defined. Please return to Step 1.")
    elif not st.session_state.document_text:
        st.warning("No document uploaded. Please return to Step 2.")
    else:
        st.markdown(f"**Target Schema:** `{st.session_state.schema.title}` | **Document:** `{st.session_state.uploaded_doc_name}`")

        c_exec, c_stats = st.columns([1.1, 0.9], gap="large")

        with c_exec:
            st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
            st.markdown("#### 🚀 Extraction Trigger")
            st.write("The LLM prompt is dynamically generated from your active schema definition.")
            
            use_mock_flag = (api_provider == "Offline Heuristic Mode")
            if st.button("🚀 Run AI Extraction Engine", type="primary", use_container_width=True):
                with st.spinner("AI analyzing document against dynamic schema fields..."):
                    extraction_result, notice = run_schema_driven_extraction(
                        schema=st.session_state.schema,
                        document_text=st.session_state.document_text,
                        document_name=st.session_state.uploaded_doc_name or "uploaded_doc",
                        gemini_key=gemini_key,
                        groq_key=groq_key,
                        use_mock=use_mock_flag
                    )
                    st.session_state.extraction_result = extraction_result
                    st.session_state.extraction_performed = True

                    for fid, fext in extraction_result.extracted_fields.items():
                        st.session_state.form_values[fid] = fext.extracted_value

                if notice:
                    st.warning(notice)
                else:
                    st.success("✅ Extraction completed successfully!")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_stats:
            if st.session_state.extraction_result:
                st.markdown("<div class='saas-card'>", unsafe_allow_html=True)
                st.markdown("#### 📊 Accuracy Metrics")
                ext_fields = st.session_state.extraction_result.extracted_fields
                total_f = len(ext_fields)
                missing_f = sum(1 for f in ext_fields.values() if f.is_missing)
                high_conf = sum(1 for f in ext_fields.values() if f.confidence == "high")
                
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Total Fields", total_f)
                    st.metric("High Confidence", high_conf)
                with m2:
                    st.metric("Missing / Null", missing_f)
                    acc = round((high_conf / total_f * 100) if total_f > 0 else 0, 1)
                    st.metric("Confidence Score", f"{acc}%")
                st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.extraction_performed and st.session_state.extraction_result:
            st.markdown("#### 📋 Extraction Result Matrix")
            table_rows = []
            for f in st.session_state.schema.fields:
                res = st.session_state.extraction_result.extracted_fields.get(f.id)
                val_display = res.extracted_value if res and res.extracted_value is not None else "(Blank / Null)"
                conf_display = res.confidence if res else "missing"
                status_badge = "🟢 HIGH" if conf_display == "high" else ("🟡 MEDIUM" if conf_display == "medium" else "🔴 MISSING")
                
                table_rows.append({
                    "Confidence": status_badge,
                    "Field Label": f.label,
                    "Type": f.type.upper(),
                    "Required": "Yes" if f.required else "No",
                    "Extracted Value": str(val_display)
                })
            
            st.dataframe(table_rows, use_container_width=True)
            
            if st.button("Proceed to Review & Edit ➡️", type="primary", use_container_width=True):
                st.session_state.current_step = 4
                st.rerun()

# ==========================================
# STEP 4: REVIEW & EDIT
# ==========================================
elif st.session_state.current_step == 4:
    st.markdown("### ✏️ Review, Edit & Submit")
    st.caption("Verify autofilled values, correct discrepancies, and complete missing required fields.")

    if not st.session_state.schema.fields:
        st.error("No form schema defined. Please return to Step 1.")
    else:
        # Check missing required fields
        missing_reqs = []
        for f in st.session_state.schema.fields:
            val = st.session_state.form_values.get(f.id)
            if f.required and (val is None or (isinstance(val, str) and not val.strip())):
                missing_reqs.append(f.label)

        if missing_reqs:
            st.warning(f"⚠️ **Attention:** {len(missing_reqs)} required field(s) are currently empty: {', '.join(missing_reqs)}")

        with st.form("review_and_save_form"):
            st.markdown(f"## {st.session_state.schema.title}")
            if st.session_state.schema.description:
                st.caption(st.session_state.schema.description)
            st.markdown("---")

            for f in st.session_state.schema.fields:
                ext_meta: FieldExtraction = None
                if st.session_state.extraction_result:
                    ext_meta = st.session_state.extraction_result.extracted_fields.get(f.id)

                curr_val = st.session_state.form_values.get(f.id)
                req_badge = " <span style='color:#EF4444;'>* (Required)</span>" if f.required else " *(Optional)*"

                if ext_meta:
                    if ext_meta.confidence == "high":
                        badge_html = "<span class='badge-high'>✅ High Confidence</span>"
                    elif ext_meta.confidence == "medium":
                        badge_html = "<span class='badge-med'>⚠️ Medium Confidence</span>"
                    else:
                        badge_html = "<span class='badge-missing'>❌ Missing from Document</span>"
                else:
                    badge_html = ""

                st.markdown(f"**{f.label}**{req_badge} &nbsp; {badge_html}", unsafe_allow_html=True)
                
                if ext_meta and ext_meta.validation_error:
                    st.caption(f"⚡ Notice: {ext_meta.validation_error}")

                if f.type == "text":
                    st.session_state.form_values[f.id] = st.text_input(
                        f.label,
                        value=str(curr_val) if curr_val is not None else "",
                        placeholder=f.placeholder or "Enter text",
                        key=f"input_{f.id}",
                        label_visibility="collapsed"
                    )

                elif f.type == "textarea":
                    st.session_state.form_values[f.id] = st.text_area(
                        f.label,
                        value=str(curr_val) if curr_val is not None else "",
                        placeholder=f.placeholder or "Enter multi-line text",
                        key=f"input_{f.id}",
                        label_visibility="collapsed"
                    )

                elif f.type == "number":
                    num_init = float(curr_val) if (isinstance(curr_val, (int, float))) else 0.0
                    st.session_state.form_values[f.id] = st.number_input(
                        f.label,
                        value=num_init,
                        key=f"input_{f.id}",
                        label_visibility="collapsed"
                    )

                elif f.type == "date":
                    date_init = None
                    if curr_val:
                        try:
                            date_init = datetime.strptime(str(curr_val), "%Y-%m-%d").date()
                        except Exception:
                            date_init = None
                    
                    selected_date = st.date_input(
                        f.label,
                        value=date_init,
                        key=f"input_{f.id}",
                        label_visibility="collapsed"
                    )
                    st.session_state.form_values[f.id] = selected_date.strftime("%Y-%m-%d") if selected_date else None

                elif f.type == "dropdown":
                    options = f.options if f.options else ["N/A"]
                    idx_default = 0
                    if curr_val in options:
                        idx_default = options.index(curr_val)
                    
                    st.session_state.form_values[f.id] = st.selectbox(
                        f.label,
                        options=options,
                        index=idx_default,
                        key=f"input_{f.id}",
                        label_visibility="collapsed"
                    )

                elif f.type == "checkbox":
                    bool_val = bool(curr_val) if curr_val is not None else False
                    st.session_state.form_values[f.id] = st.checkbox(
                        f.description or "I confirm / agree to terms",
                        value=bool_val,
                        key=f"input_{f.id}"
                    )

                st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

            submit_form = st.form_submit_button("💾 Save & Submit Completed Record", type="primary", use_container_width=True)

            if submit_form:
                errors = []
                for f in st.session_state.schema.fields:
                    val = st.session_state.form_values.get(f.id)
                    if f.required:
                        if val is None or (isinstance(val, str) and not val.strip()):
                            errors.append(f"Required field '{f.label}' cannot be empty.")

                if errors:
                    st.error("❌ Submission Blocked:\n" + "\n".join([f"- {e}" for e in errors]))
                else:
                    saved_path = save_submission(
                        schema=st.session_state.schema,
                        form_data=st.session_state.form_values,
                        document_name=st.session_state.uploaded_doc_name,
                        field_metadata={
                            k: v.model_dump() for k, v in (st.session_state.extraction_result.extracted_fields.items() if st.session_state.extraction_result else {}.items())
                        }
                    )
                    st.success("🎉 **Form successfully validated and saved!**")
                    st.session_state.current_step = 5
                    st.rerun()

# ==========================================
# STEP 5: SUBMISSIONS & RECORDS
# ==========================================
elif st.session_state.current_step == 5:
    st.markdown("### 📁 Saved Records Database")
    st.caption("View and export all structured JSON submissions stored locally.")

    submissions = load_all_submissions()
    if not submissions:
        st.info("No records stored yet. Complete a submission in Step 4.")
    else:
        st.markdown(f"Total Submissions: **{len(submissions)}**")
        for sub in submissions:
            sub_id = sub.get("submission_id", "Unknown")
            ts = sub.get("timestamp", "N/A")
            doc = sub.get("document_name", "None")
            title = sub.get("schema_snapshot", {}).get("title", "Submission")

            with st.expander(f"📑 {title} — ID: `{sub_id}` ({ts})", expanded=False):
                st.markdown(f"- **Document Source:** `{doc}`")
                st.markdown(f"- **Timestamp:** `{ts}`")
                st.markdown("#### Form Data Payload:")
                st.json(sub.get("form_data", {}))
                
                st.download_button(
                    label=f"📥 Download JSON Record ({sub_id})",
                    data=json.dumps(sub, indent=2),
                    file_name=f"submission_{sub_id}.json",
                    mime="application/json",
                    key=f"dl_sub_{sub_id}"
                )

    st.divider()
    if st.button("➕ Start New Dynamic Session", type="primary"):
        st.session_state.current_step = 1
        st.session_state.form_values = {}
        st.session_state.extraction_result = None
        st.session_state.extraction_performed = False
        st.session_state.document_text = ""
        st.session_state.uploaded_doc_bytes = None
        st.rerun()
