"""
services/ai_extractor.py
Schema-driven AI extraction service.
Constructs dynamic extraction prompts directly from user-defined FormSchema.
Supports Google Gemini API, Groq API, and offline fallback mock extraction.
"""
import os
import json
import re
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

from models.schemas import FormSchema, FormExtractionResult, FieldExtraction
from services.validator import validate_field_extraction

load_dotenv()


def build_dynamic_prompt(schema: FormSchema, document_text: str) -> str:
    """
    Dynamically generates the extraction prompt based entirely on user-defined schema fields.
    Does NOT hardcode any fields.
    """
    fields_spec = []
    for f in schema.fields:
        opts_info = f", Options: {f.options}" if f.options else ""
        req_info = " (REQUIRED)" if f.required else " (Optional)"
        desc_info = f" - Description/Context: {f.description}" if f.description else ""
        fields_spec.append(
            f"- Field ID: '{f.id}' | Label: '{f.label}' | Type: {f.type}{req_info}{opts_info}{desc_info}"
        )

    fields_str = "\n".join(fields_spec)

    prompt = f"""You are an accurate, schema-driven document data extraction engine.

Your task is to analyze the provided DOCUMENT CONTENT and extract values ONLY for the user-specified form fields listed below.

### TARGET FORM SCHEMA:
{fields_str}

### EXTRACTION RULES:
1. **Never guess or hallucinate.** If a field's value is not clearly present in the document, set "value" to null.
2. **Handle uncertainty:** If the information is ambiguous, set "value" to null or flag confidence as "low".
3. **Strict Type Matching:**
   - Single-line text / Multi-line text: Return clear string or null.
   - Number: Extract strictly the numeric quantity (e.g. 5, 1250.50). Do not include words or symbols if possible.
   - Date: Extract the date formatted as YYYY-MM-DD or readable date string.
   - Dropdown: Choose the closest matching option from the field's allowed options list, or null if no match.
   - Checkbox: Return true if document explicitly affirms/agrees/confirms this, otherwise false.
4. **Confidence Assessment:**
   - "high": Clear, explicit mention with direct match.
   - "medium": Inferred from context or slight ambiguity.
   - "low" or "missing": Value not found or highly uncertain.

### OUTPUT FORMAT:
You MUST respond with a valid JSON object only. Do not include markdown codeblocks or extra conversational text outside the JSON.
Structure:
{{
  "extracted_data": [
    {{
      "field_id": "<field_id_from_schema>",
      "field_label": "<field_label>",
      "value": <extracted_value_or_null>,
      "confidence": "high" | "medium" | "low" | "missing",
      "explanation": "<brief rationale or snippet from doc>"
    }}
  ]
}}

### DOCUMENT CONTENT:
{document_text}
"""
    return prompt


def clean_json_response(raw_text: str) -> str:
    """Strips markdown code blocks ```json ... ``` and cleans response string."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def extract_with_gemini(prompt: str, api_key: str) -> Tuple[Optional[str], Optional[str]]:
    """Calls Google Gemini API to extract structured JSON data."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try gemini-1.5-flash or gemini-2.5-flash / gemini-pro
        model_names = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-pro"]
        last_err = None

        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                if response.text:
                    return response.text, None
            except Exception as e:
                last_err = e
                continue

        return None, f"Gemini API request failed: {str(last_err)}"
    except Exception as e:
        return None, f"Gemini client initialization error: {str(e)}"


def extract_with_groq(prompt: str, api_key: str) -> Tuple[Optional[str], Optional[str]]:
    """Calls Groq API to extract structured JSON data with fallback model options."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        models_to_try = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "groq/compound"
        ]
        last_err = None
        for model in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a precise data extraction engine. Always output pure valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model,
                    response_format={"type": "json_object"}
                )
                if chat_completion.choices and chat_completion.choices[0].message.content:
                    return chat_completion.choices[0].message.content, None
            except Exception as e:
                last_err = e
                continue

        return None, f"Groq API extraction error: {str(last_err)}"
    except Exception as e:
        return None, f"Groq API client initialization error: {str(e)}"


def mock_heuristic_extraction(schema: FormSchema, document_text: str) -> str:
    """
    Offline smart heuristic extractor used when no API key is provided.
    Ensures complete end-to-end functionality and testing without network dependency.
    """
    doc_lower = document_text.lower()
    extracted_data = []

    for field in schema.fields:
        label_lower = field.label.lower()
        val = None
        conf = "missing"
        explanation = "Extracted via offline semantic parser."

        # Search for label in text
        lines = document_text.splitlines()
        found_line = None
        for line in lines:
            if label_lower in line.lower() or any(word in line.lower() for word in label_lower.split() if len(word) > 3):
                found_line = line
                break

        if found_line:
            # Extract portion after colon or separator
            if ":" in found_line:
                val = found_line.split(":", 1)[1].strip()
            elif "-" in found_line:
                val = found_line.split("-", 1)[1].strip()
            else:
                val = found_line.strip()
            conf = "medium"

        # Regex heuristics for common types if label match was not clean
        if field.type == "number" and val is None:
            num_match = re.search(r"\b\d+(\.\d+)?\b", document_text)
            if num_match:
                val = num_match.group(0)
                conf = "low"

        elif field.type == "date" and val is None:
            date_match = re.search(r"\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b", document_text)
            if date_match:
                val = date_match.group(0)
                conf = "medium"

        elif field.type == "checkbox":
            val = any(term in doc_lower for term in ["agree", "accepted", "confirmed", "true", "yes", label_lower])
            conf = "high"

        elif field.type == "dropdown" and field.options:
            for opt in field.options:
                if opt.lower() in doc_lower:
                    val = opt
                    conf = "high"
                    break

        if val is None:
            conf = "missing"
            explanation = "Field not found in document content."

        extracted_data.append({
            "field_id": field.id,
            "field_label": field.label,
            "value": val,
            "confidence": conf,
            "explanation": explanation
        })

    return json.dumps({"extracted_data": extracted_data})


def run_schema_driven_extraction(
    schema: FormSchema,
    document_text: str,
    document_name: str,
    gemini_key: Optional[str] = None,
    groq_key: Optional[str] = None,
    use_mock: bool = False
) -> Tuple[FormExtractionResult, Optional[str]]:
    """
    Main orchestration function for dynamic schema extraction.
    Parses LLM response, validates against field types, and formats into FormExtractionResult.
    """
    if not schema.fields:
        return FormExtractionResult(schema_title=schema.title), "Form schema has no fields. Please add fields first."

    prompt = build_dynamic_prompt(schema, document_text)
    raw_response = None
    error_msg = None

    # Priority 1: Gemini API Key
    effective_gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
    effective_groq_key = groq_key or os.getenv("GROQ_API_KEY")

    if use_mock:
        raw_response = mock_heuristic_extraction(schema, document_text)
    elif effective_gemini_key:
        raw_response, error_msg = extract_with_gemini(prompt, effective_gemini_key)
        if error_msg and effective_groq_key:
            # Fallback to Groq
            raw_response, error_msg = extract_with_groq(prompt, effective_groq_key)
    elif effective_groq_key:
        raw_response, error_msg = extract_with_groq(prompt, effective_groq_key)
    else:
        # Graceful fallback to offline smart heuristic
        raw_response = mock_heuristic_extraction(schema, document_text)

    if not raw_response:
        # Fallback to heuristic to prevent total crash
        raw_response = mock_heuristic_extraction(schema, document_text)
        notice = f"AI API call encountered an issue ({error_msg}). Switched to local heuristic parser."
    else:
        notice = None

    # Parse JSON
    try:
        cleaned_json = clean_json_response(raw_response)
        parsed_json = json.loads(cleaned_json)
    except Exception as e:
        # If JSON parsing failed, use mock fallback
        cleaned_json = mock_heuristic_extraction(schema, document_text)
        parsed_json = json.loads(cleaned_json)

    # Process items into FieldExtraction map
    items = parsed_json.get("extracted_data", [])
    extracted_map: Dict[str, FieldExtraction] = {}

    # Index LLM output by field_id and label
    llm_by_id = {}
    llm_by_label = {}
    for item in items:
        fid = item.get("field_id")
        lbl = item.get("field_label", "").strip().lower()
        if fid:
            llm_by_id[fid] = item
        if lbl:
            llm_by_label[lbl] = item

    # Build validated extraction per schema field
    for field in schema.fields:
        match_item = llm_by_id.get(field.id) or llm_by_label.get(field.label.strip().lower())
        
        raw_val = match_item.get("value") if match_item else None
        confidence = match_item.get("confidence", "missing") if match_item else "missing"
        explanation = match_item.get("explanation") if match_item else None

        field_result = validate_field_extraction(
            field=field,
            raw_val=raw_val,
            confidence=confidence,
            explanation=explanation
        )
        extracted_map[field.id] = field_result

    result = FormExtractionResult(
        schema_title=schema.title,
        extracted_fields=extracted_map,
        raw_llm_response=raw_response,
        document_name=document_name
    )

    return result, notice
