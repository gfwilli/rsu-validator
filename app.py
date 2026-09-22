import streamlit as st
import google.genai as genai
from PIL import Image

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

# Header
st.markdown("# <span class='highlight'>RSUnits</span> Verification Upload", unsafe_allow_html=True)

# Capture URL Parameters (e.g. ?applicant_id=123)
query_params = st.query_params
applicant_id = query_params.get("applicant_id", None)

if applicant_id:
    st.caption(f"Application Ref ID: **{applicant_id}**")

# Instructions
st.markdown("""
<div class="instruction-card">
    <h4>📋 Required Verification Documents</h4>
    <p>To finalize your prequalification review, please upload both required verification documents below:</p>
    <ul>
        <li><b>1. Most Recent RSU Details:</b> Must show total share counts, upcoming vest dates, and current market value.</li>
        <li><b>2. Most Recent Paystub:</b> Must show gross earnings, deductions, and employer name.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Separate Uploaders
rsu_file = st.file_uploader("1. Upload RSU Statement / Vesting Schedule", type=["png", "jpg", "jpeg"])
paystub_file = st.file_uploader("2. Upload Most Recent Paystub", type=["png", "jpg", "jpeg"])

# Preview Uploads
col1, col2 = st.columns(2)
if rsu_file:
    with col1:
        st.image(Image.open(rsu_file), caption="RSU Statement Preview", use_column_width=True)
if paystub_file:
    with col2:
        st.image(Image.open(paystub_file), caption="Paystub Preview", use_column_width=True)

# Validation & Submission
if st.button("Submit & Validate Documents"):
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("System configuration error: Missing API Key.")
    elif not rsu_file or not paystub_file:
        st.warning("Please upload both your RSU statement and your paystub before submitting.")
    else:
        with st.spinner("Analyzing uploaded documents with Gemini AI..."):
            try:
                client = genai.Client(api_key=api_key)

                rsu_img = Image.open(rsu_file)
                paystub_img = Image.open(paystub_file)

                prompt = (
                    "You are an automated underwriting document validator for RSUnits.\n"
                    "Analyze the provided image(s) and extract key verification data:\n\n"
                    "For RSU Statement:\n"
                    "- Total Shares / Grant Amounts\n"
                    "- Next Scheduled Vesting Dates & Amounts\n"
                    "- Brokerage / Platform Name\n\n"
                    "For Paystub:\n"
                    "- Employer Name\n"
                    "- Gross and Net Pay\n"
                    "- Pay Period Dates\n\n"
                    "Provide a clear, structured summary verifying if both documents meet prequalification criteria."
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[rsu_img, paystub_img, prompt]
                )

                st.success("Documents successfully processed!")
                st.markdown("### Verification Summary")
                st.write(response.text)

            except Exception as e:
                st.error(f"Processing error: {e}")
