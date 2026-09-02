# AI-Powered Dynamic Form Builder & Document Autofill Application

An enterprise-ready, schema-driven web application built for the **Tecnots AI Engineer Intern Assessment**. The application allows users to dynamically design custom forms at runtime, upload documents (PDF, PNG, JPG, JPEG), extract field-specific data using Gemini AI (with PyMuPDF and OCR support), validate types and constraints, highlight missing or low-confidence data, and review/edit/save the final records.

---

## 🌟 Key Features

### 1. Dynamic Form Builder (15 Marks)
- **Zero Hardcoding**: Every form field is dynamically configured at runtime. The same application supports Job Applications, Invoices, Medical Intakes, or any custom domain without changing a single line of code.
- **6 Supported Field Types**:
  - `Single-line text`
  - `Multi-line text`
  - `Number` (with float/integer validation)
  - `Date` (ISO format validation & normalization)
  - `Dropdown` (custom comma-separated choices)
  - `Checkbox` (boolean affirm/agree toggles)
- **Field Controls**: Mark required/optional, add custom placeholders/hints, reorder fields (⬆️/⬇️), and delete fields.
- **Live Real-time Preview**: Form preview updates instantaneously as fields are added or modified.
- **Bonus Capabilities**:
  - Pre-built templates (Job Application, Supplier Invoice, Medical Intake).
  - Schema portability: Full JSON schema Export and Import.

### 2. Document Upload & Text Extraction (5 Marks)
- Supports `.pdf`, `.png`, `.jpg`, `.jpeg`.
- **Format Validation**: Strict file type validation and error reporting.
- **PyMuPDF Engine**: Fast, accurate extraction of digital PDF text blocks and metadata.
- **OCR Engine Fallback**: Automatically processes scanned PDFs and image files via OCR.
- **Edge Case Protection**: Instant warning banner if a user attempts to upload a document before defining form schema fields.

### 3. Schema-Driven AI Extraction (20 Marks)
- **Dynamic Prompt Generation**: The LLM prompt is constructed dynamically from whatever fields, types, descriptions, and dropdown options currently exist in the schema.
- **Extraction Rules Enforced**:
  - **No Guessing / Zero Hallucination**: Missing information is returned as `null`.
  - **Uncertainty Flagging**: Returns confidence scores (`high`, `medium`, `low`, `missing`) with contextual explanations.
  - **Structured JSON Output**: Guarantees parseable output conforming to the dynamic schema.
- **Multi-Provider & Offline Fallback**:
  - Primary: **Google Gemini API** (`gemini-1.5-flash` / `gemini-pro`).
  - Secondary: **Groq API** (`llama-3.3-70b-versatile`).
  - Offline Mode: Smart semantic fallback parser for local testing without active API keys.

### 4. Review, Edit & Submit Flow (5 Marks)
- **Interactive Pre-filled Form**: Displays all extracted values mapped directly into form controls.
- **Visual Status Badges**:
  - `[✅ High Confidence]` (Green)
  - `[⚠️ Medium Confidence]` (Orange)
  - `[❌ Missing / Not Found]` (Red)
  - `[⚡ Type Check Notice]` (Amber)
- **Full Manual Editing**: Edit any field, complete missing required fields, and correct AI values before submission.
- **Validation on Save**: Blocks submission if any required fields remain unfilled.
- **Local Persistence**: Saves completed submissions as timestamped JSON files in `data/submissions/`.

### 5. Edge Cases Handled (5 Marks)
| Edge Case Scenario | Handled Behavior |
| :--- | :--- |
| **Required field has no data in document** | Value left blank, field flagged with red `[❌ Missing]` badge and submission blocked until filled. |
| **Upload attempted before creating schema** | Step 2 alerts the user and displays a 1-click button to return to Step 1. |
| **Corrupted or unsupported file** | Catches parsing exceptions, shows a descriptive error message, and provides retry capability. |
| **Number expected but text extracted** | Validator strips non-numeric characters; if invalid, sets value to `null` and shows a type mismatch notice. |
| **AI uncertain about a field** | AI returns `null` or flags `low` confidence rather than hallucinating an inaccurate guess. |

---

## 🏗️ Architecture & Project Structure

```
ai/
├── app.py                      # Main Streamlit UI and stepped workflow orchestration
├── requirements.txt            # Project dependencies
├── .env.example                # API key template (GEMINI_API_KEY, GROQ_API_KEY)
├── .gitignore                  # Security rules (ignores .env, bytecode, local data)
├── README.md                   # Full documentation & interview prep guide
│
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic schemas (FormField, FormSchema, FieldExtraction, SubmissionRecord)
│
├── services/
│   ├── __init__.py
│   ├── document_parser.py      # PyMuPDF text parser & digital vs scanned detection
│   ├── ocr_service.py          # OCR engine for image and scanned PDF extraction
│   ├── ai_extractor.py         # Dynamic prompt generator & LLM API client (Gemini/Groq/Offline)
│   └── validator.py            # Type validation, date normalization, dropdown matching, edge cases
│
├── utils/
│   ├── __init__.py
│   ├── helpers.py              # Persistence, schema export/import, sample PDF generators
│   └── templates.py            # Built-in industry templates (Job App, Invoice, Medical)
│
├── tests/
│   └── test_all.py             # Automated pytest suite verifying all components
│
└── data/
    ├── samples/                # Benchmark test documents (sample_resume.pdf, sample_invoice.pdf)
    └── submissions/            # Saved JSON form submissions
```

---

## ⚙️ Tech Stack Justification

| Technology | Purpose | Why Chosen |
| :--- | :--- | :--- |
| **Python 3.10+** | Core Language | Clean syntax, rich ecosystem for AI, OCR, and document processing. |
| **Streamlit** | Frontend UI | Rapid development of interactive, reactive web apps with native session state. |
| **Google Gemini API** | AI Extraction | Industry-leading multimodal reasoning, fast inference, and native JSON mode. |
| **PyMuPDF (`fitz`)** | PDF Parsing | Up to 10x faster than traditional PDF parsers; preserves text layout and blocks. |
| **Pydantic v2** | Data Modeling | Strict schema validation, automatic serialization, and robust type safety. |
| **Pytesseract / PIL** | OCR Engine | Reliable optical character recognition for scanned receipts, IDs, and images. |

---

## 🚀 Quickstart & Installation

### 1. Clone the repository & navigate to directory
```bash
cd ai
```

### 2. Create and activate a virtual environment (Recommended)
```bash
# Windows:
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Gemini API Key:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
```
*(Note: You can also enter the API key directly into the Streamlit sidebar at runtime, or use the built-in Offline Heuristic Mode without an API key!)*

### 5. Run the Automated Tests
```bash
pytest tests/test_all.py -v
```

### 6. Launch the Application
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 🌐 Cloud Deployment Guide (Free 1-Click Hosting)

### Method 1: Streamlit Community Cloud (Fastest & Free — Recommended)
1. Push this repository to **GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - AI Form Builder & Autofill"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with GitHub.
3. Click **"New app"** ➔ Select your repository, branch `main`, and main file `app.py`.
4. Under **"Advanced settings"** ➔ **Secrets**, add your API key:
   ```toml
   GROQ_API_KEY = "gsk_..."
   GEMINI_API_KEY = "AIza..."
   ```
5. Click **"Deploy"**! You will get a live public URL like `https://ai-form-autofill.streamlit.app` in under 2 minutes.

### Method 2: Render.com (Web Service)
1. Link your GitHub repo to **[render.com](https://render.com)**.
2. Select **"Web Service"** (Python environment).
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add `GROQ_API_KEY` in Environment Variables.

---

## 🧠 How Schema-Driven AI Extraction Works

1. **Schema Definition**: The user builds a form or loads a template. Each field has an `id`, `label`, `type`, `required` flag, and optional `options`/`description`.
2. **Dynamic Prompt Assembly**: `services/ai_extractor.py` parses the `FormSchema` object and iterates over `schema.fields`. It constructs a targeted extraction prompt specifying the exact fields, data types, and strict extraction rules.
3. **Structured Inference**: The prompt and raw document text are sent to Gemini AI with `response_mime_type="application/json"`. Gemini returns a structured JSON payload with extracted values and confidence levels.
4. **Validation & Normalization Pipeline**: `services/validator.py` processes each field through type-specific validators (converting date formats, stripping non-numeric symbols for numbers, matching dropdown options).
5. **Autofill State**: Validated values populate `st.session_state.form_values` and are presented in an editable UI with color-coded status badges.

---

## ⚖️ Assumptions & Trade-offs

- **Text-First Extraction**: Digital PDFs are parsed directly via PyMuPDF for maximum speed and accuracy. OCR is only invoked when text density is low or for raster image files.
- **Local JSON Storage**: Form submissions are stored locally in `data/submissions/`. This keeps the application self-contained and zero-dependency (no external database server required), while remaining easy to upgrade to SQLite or PostgreSQL.
- **Zero-Guessing AI Policy**: If a field is ambiguous or absent in the document, it is intentionally returned as `null` to prevent hallucinations in mission-critical forms (e.g. medical intake or invoicing).

---

## 🎯 Technical Assessment Interview Preparation (15 Deep Q&A)

### Q1: How did you ensure the AI extraction is completely dynamic and not hardcoded?
> **Answer**: In `services/ai_extractor.py`, the function `build_dynamic_prompt()` accepts the Pydantic `FormSchema` object. It dynamically iterates through `schema.fields`, generating field descriptors, expected types, and validation constraints at runtime. No field names (such as "Name" or "Email") are hardcoded in the system prompt.

### Q2: Why choose PyMuPDF over PyPDF2 or pdfplumber?
> **Answer**: PyMuPDF (based on MuPDF C-library) is significantly faster (5-10x) than pure Python libraries like PyPDF2. It accurately extracts structural layout blocks, handles character encodings properly, and allows fast rendering of page pixmaps for OCR fallback.

### Q3: How does the application handle scanned PDFs or image uploads?
> **Answer**: In `services/document_parser.py`, if an image (`.png`, `.jpg`, `.jpeg`) is uploaded, it routes directly to `services/ocr_service.py`. For PDFs, it checks character density per page; if a page contains fewer than 25 characters, it renders a high-DPI pixmap and runs OCR to extract the visual text.

### Q4: How is type validation implemented for extracted values?
> **Answer**: In `services/validator.py`, each field type has a dedicated validation function:
> - `validate_number`: Strips currency signs and commas using regex, casting to `int` or `float`. If non-numeric text is provided, it returns `(None, "Notice: expected number")`.
> - `validate_date`: Tries multiple common date patterns (`YYYY-MM-DD`, `DD/MM/YYYY`, `Month DD, YYYY`) and normalizes to standard ISO `YYYY-MM-DD`.
> - `validate_dropdown`: Performs case-insensitive and fuzzy matching against allowed options.
> - `validate_checkbox`: Maps truthy/falsy terms (`yes`, `agreed`, `true`, `1`) to booleans.

### Q5: What happens if a required field is missing from the uploaded document?
> **Answer**: The AI returns `null` with confidence `missing`. The validator marks `is_missing=True` and sets a validation notice. In Step 4 (Review & Edit), the field is highlighted in red with `[❌ Missing / Not Found]`, an alert banner summarizes the count of empty required fields, and the form submit button validates that the user manually fills it before saving.

### Q6: What prevents the AI from hallucinating or guessing values?
> **Answer**: The system prompt explicitly enforces 3 strict negative constraints: (1) Never hallucinate or guess, (2) If a field is absent or ambiguous, return `null`, and (3) Provide a confidence score (`high`, `medium`, `low`, `missing`). Furthermore, low-confidence extractions are flagged in the UI for mandatory human review.

### Q7: How does the application prevent crashing if the LLM API fails or rate-limits?
> **Answer**: `ai_extractor.py` wraps API calls in try-catch blocks and checks multiple fallback model endpoints. If the API key is missing, invalid, or rate-limited, it automatically falls back to `mock_heuristic_extraction()`, displaying a non-blocking warning notice to the user so the workflow continues seamlessly.

### Q8: How is state managed between steps in Streamlit?
> **Answer**: We utilize Streamlit's native `st.session_state` dictionary to preserve the current step index (`current_step`), the active `FormSchema`, uploaded document bytes, extracted text, AI extraction results, and user-edited form values across UI reruns.

### Q9: How does the dynamic form builder handle adding, reordering, and deleting fields?
> **Answer**: The schema holds a list of `FormField` instances. Adding appends a new model with a unique UUID. Reordering swaps adjacent indices in the list (`st.session_state.schema.fields[idx], fields[idx-1]`). Deleting pops the item at the selected index. Every action triggers `st.rerun()`, which updates both the builder and the live preview simultaneously.

### Q10: How are completed submissions saved and structured?
> **Answer**: In `utils/helpers.py`, `save_submission()` wraps the final form values, a snapshot of the schema at submission time, the document name, and extraction confidence metadata into a `SubmissionRecord` Pydantic model. It serializes this record as a formatted JSON file in `data/submissions/`.

### Q11: How do you handle schema export and import?
> **Answer**: `export_schema_to_json()` uses Pydantic's `.model_dump()` to serialize the schema to JSON. `import_schema_from_json()` reads the uploaded JSON file and deserializes it back into a validated `FormSchema` instance, allowing users to save and reuse complex schemas.

### Q12: What edge case occurs if a user uploads a document before creating any form fields?
> **Answer**: In Step 2 (`app.py`), the application checks if `st.session_state.schema.fields` is empty. If so, it renders a warning explaining that fields must be defined first and provides a button to redirect to Step 1.

### Q13: What design patterns are used in this codebase?
> **Answer**:
> - **Schema/Configuration Pattern**: Dynamic UI and prompt generation driven by data models.
> - **Strategy Pattern**: Multi-provider extraction (Gemini, Groq, Offline Heuristic) under a unified interface.
> - **Pipeline Pattern**: Document Input -> PyMuPDF/OCR Text Extraction -> Dynamic Prompt Assembly -> LLM Inference -> Type Validation & Normalization -> Form State Population.

### Q14: If you had another week, what architectural enhancements would you add?
> **Answer**:
> 1. Add bounding-box visual grounding (highlighting where in the PDF text was extracted from).
> 2. Support multi-page table extraction (dynamic grid/tabular field types).
> 3. Add database integration (PostgreSQL with SQLAlchemy) and user authentication.
> 4. Add webhook integrations to forward completed forms to Slack, Zapier, or CRM systems.

### Q15: How can you test the application quickly without configuring external credentials?
> **Answer**:
> 1. Select **Offline Heuristic Mode** in the sidebar.
> 2. Load the built-in **Job Application** or **Supplier Invoice** template in Step 1.
> 3. Click **Load Sample Resume** or **Load Sample Invoice** in Step 2.
> 4. Click **Run AI Extraction** in Step 3. All fields will be extracted, validated, and pre-filled into the form for review and submission in Step 4.
