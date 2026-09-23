import streamlit as st
import google.genai as genai
from google.genai import types
from PIL import Image
from google.cloud import storage
from google.oauth2 import service_account
import datetime
import json

# Page Configuration
st.set_page_config(page_title="RSUnits | Document Upload", layout="centered", page_icon="📈")

# Custom Styling (RSUnits Dark Theme)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0b0b;
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    h1, h2, h3 { color: #ffffff !important; font-weight: 700; }
    .highlight { color: #a3e635; }
    
    .instruction-card {
        background-color: #141414;
        border: 1px solid #262626;
        border-left: 4px solid #a3e635;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 25px;
    }
    .instruction-card h4 { margin: 0 0 8px 0; color: #a3e635; font-size: 1.1rem; }
    .instruction-card ul { margin: 5px 0 0 18px; padding: 0; color: #d1d5db; font-size: 0.95rem; line-height: 1.5; }
    
    .stButton > button {
        background-color: #a3e635 !important;
        color: #0b0b0b !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.5rem !important;
        width: 100%;
        margin-top: 10px;
    }
    .stButton > button:hover {
        background-color: #bef264 !important;
    }
    </style>
""", unsafe_allow_html=True)

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Helper function to upload files or raw string/JSON data to GCS
def upload_to_gcs(file_obj_or_bytes, blob_name, content_type="application/octet-stream"):
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = storage.Client(credentials=credentials)
        bucket_name = st.secrets.get("GCS_BUCKET_NAME", "rsunits_uploads")
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if hasattr(file_obj_or_bytes, 'seek'):
            file_obj_or_bytes.seek(0)
            blob.upload_from_file(file_obj_or_bytes, content_type=content_type)
        else:
            blob.upload_from_string(file_obj_or_bytes, content_type=content_type)
            
        return True
    except Exception as e:
        st.error(f"Failed to upload {blob_name} to GCS: {e}")
        return False

# Helper function to convert uploaded files into Gemini Part objects
def prepare_part_for_gemini(uploaded_file):
    uploaded_file.seek(0)
    bytes_data = uploaded_file.read()
    return types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type)

# Header
st.markdown("# <span class='highlight'>RSUnits</span> Verification Upload", unsafe_allow_html=True)

# Capture URL Parameters
query_params = st.query_params
applicant_id = query_params.get("applicant_id", "anonymous")

if applicant_id != "anonymous":
    st.caption(f"Application Ref ID: **{applicant_id}**")

# Instructions
st.markdown("""
<div class="instruction-card">
    <h4>📋 Required Verification Documents</h4>
    <p>To finalize your prequalification review, please upload the three required verification documents below (Max 20MB per file; PNG, JPG, or PDF):</p>
    <ul>
        <li><b>1. Photo Identification:</b> Government-issued Driver's License or Passport (used strictly for CIP/KYC compliance).</li>
        <li><b>2. RSU Statement / Vesting Schedule:</b> Must show total share counts, upcoming vest dates, and current market value.</li>
        <li><b>3. Most Recent Paystub:</b> Must show gross earnings, deductions, and employer name.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Uploaders (PNG, JPG, JPEG, PDF)
allowed_types = ["png", "jpg", "jpeg", "pdf"]
id_file = st.file_uploader("1. Upload Photo Identification (Driver's License or Passport)", type=allowed_types)
rsu_file = st.file_uploader("2. Upload RSU Statement / Vesting Schedule", type=allowed_types)
paystub_file = st.file_uploader("3. Upload Most Recent Paystub", type=allowed_types)

# Document Previews
col1, col2, col3 = st.columns(3)

if id_file:
    with col1:
        if id_file.type == "application/pdf":
            st.info(f"📄 Photo ID PDF attached ({id_file.name})")
        else:
            st.image(Image.open(id_file), caption="Photo ID Preview", use_container_width=True)

if rsu_file:
    with col2:
        if rsu_file.type == "application/pdf":
            st.info(f"📄 RSU Statement PDF attached ({rsu_file.name})")
        else:
            st.image(Image.open(rsu_file), caption="RSU Statement Preview", use_container_width=True)

if paystub_file:
    with col3:
        if paystub_file.type == "application/pdf":
            st.info(f"📄 Paystub PDF attached ({paystub_file.name})")
        else:
            st.image(Image.open(paystub_file), caption="Paystub Preview", use_container_width=True)

# Submission Handling
if st.button("Submit & Validate Documents"):
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("System configuration error: Missing Gemini API Key.")
    elif not id_file or not rsu_file or not paystub_file:
        st.warning("Please upload all three required documents before submitting.")
    elif (id_file.size > MAX_FILE_SIZE_BYTES or 
          rsu_file.size > MAX_FILE_SIZE_BYTES or 
          paystub_file.size > MAX_FILE_SIZE_BYTES):
        st.error(f"One or more files exceed the maximum size limit of {MAX_FILE_SIZE_MB}MB. Please select smaller files.")
    else:
        with st.spinner("Uploading documents to storage and running automated validation..."):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save files to Google Cloud Storage
            id_uploaded = upload_to_gcs(id_file, f"applicants/{applicant_id}/{timestamp}_id_{id_file.name}", content_type=id_file.type)
            rsu_uploaded = upload_to_gcs(rsu_file, f"applicants/{applicant_id}/{timestamp}_rsu_{rsu_file.name}", content_type=rsu_file.type)
            paystub_uploaded = upload_to_gcs(paystub_file, f"applicants/{applicant_id}/{timestamp}_paystub_{paystub_file.name}", content_type=paystub_file.type)
            
            if id_uploaded and rsu_uploaded and paystub_uploaded:
                try:
                    client = genai.Client(api_key=api_key)
                    
                    id_part = prepare_part_for_gemini(id_file)
                    rsu_part = prepare_part_for_gemini(rsu_file)
                    paystub_part = prepare_part_for_gemini(paystub_file)

                    prompt = (
                        "You are an automated underwriting document validator for RSUnits.\n"
                        "Analyze the provided Photo ID, RSU Statement, and Paystub documents.\n"
                        "Extract the required details and output exclusively valid JSON with this exact structure:\n"
                        "{\n"
                        '  "identity_details": {\n'
                        '    "full_name": "string or null",\n'
                        '    "address": "string or null",\n'
                        '    "document_type": "Driver License / Passport / State ID / Unknown",\n'
                        '    "id_expiration_date": "YYYY-MM-DD or null"\n'
                        '  },\n'
                        '  "rsu_details": {\n'
                        '    "brokerage_platform": "string or null",\n'
                        '    "total_unvested_shares": "string or null",\n'
                        '    "next_vest_date": "YYYY-MM-DD or null",\n'
                        '    "next_vest_amount": "string or null"\n'
                        '  },\n'
                        '  "paystub_details": {\n'
                        '    "employer_name": "string or null",\n'
                        '    "gross_pay_period": "string or null",\n'
                        '    "net_pay_period": "string or null",\n'
                        '    "pay_period_dates": "string or null"\n'
                        '  },\n'
                        '  "prequalification_flags": {\n'
                        '    "name_match_across_docs": true,\n'
                        '    "id_is_valid_and_unexpired": true,\n'
                        '    "underwriter_notes": "string summary"\n'
                        '  }\n'
                        "}"
                    )

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[id_part, rsu_part, paystub_part, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )

                    # Persist extracted JSON summary to GCS alongside raw files
                    json_summary_name = f"applicants/{applicant_id}/{timestamp}_underwriting_summary.json"
                    upload_to_gcs(response.text, json_summary_name, content_type="application/json")

                    parsed_json = json.loads(response.text)

                    st.success("Documents successfully saved to Cloud Storage and verified!")
                    
                    # Clean UI rendering of extracted verification fields
                    st.markdown("### Verification Summary")
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.markdown("**Identity Metrics**")
                        id_info = parsed_json.get("identity_details", {})
                        st.write(f"- **Name:** {id_info.get('full_name', 'N/A')}")
                        st.write(f"- **Type:** {id_info.get('document_type', 'N/A')}")
                        st.write(f"- **Exp Date:** {id_info.get('id_expiration_date', 'N/A')}")

                    with col_b:
                        st.markdown("**RSU Metrics**")
                        rsu_info = parsed_json.get("rsu_details", {})
                        st.write(f"- **Brokerage:** {rsu_info.get('brokerage_platform', 'N/A')}")
                        st.write(f"- **Unvested Shares:** {rsu_info.get('total_unvested_shares', 'N/A')}")
                        st.write(f"- **Next Vest Date:** {rsu_info.get('next_vest_date', 'N/A')}")

                    with col_c:
                        st.markdown("**Paystub Metrics**")
                        pay_info = parsed_json.get("paystub_details", {})
                        st.write(f"- **Employer:** {pay_info.get('employer_name', 'N/A')}")
                        st.write(f"- **Gross Pay:** {pay_info.get('gross_pay_period', 'N/A')}")
                        st.write(f"- **Period:** {pay_info.get('pay_period_dates', 'N/A')}")

                    flags = parsed_json.get("prequalification_flags", {})
                    st.info(f"**Underwriting Note:** {flags.get('underwriter_notes', 'Documents received and logged successfully.')}")

                except Exception as e:
                    st.error(f"Processing error during document validation: {e}")
