import streamlit as st
import google.genai as genai
from PIL import Image

# Page Configuration
st.set_page_config(page_title="RSUnits | Document Validator", layout="centered", page_icon="📈")

# Custom Styling to match RSUnits dark fintech aesthetic
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0b0b0b;
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Headers & Accent Colors */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    .highlight {
        color: #a3e635;
    }
    
    /* Instructions Banner */
    .instruction-card {
        background-color: #141414;
        border: 1px solid #262626;
        border-left: 4px solid #a3e635;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 25px;
    }
    .instruction-card h4 {
        margin-0 0 8px 0;
        color: #a3e635;
        font-size: 1.1rem;
    }
    .instruction-card ul {
        margin: 5px 0 0 18px;
        padding: 0;
        color: #d1d5db;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    /* Customizing Streamlit Buttons */
    .stButton > button {
        background-color: #a3e635 !important;
        color: #0b0b0b !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #bef264 !important;
        color: #0b0b0b !important;
        transform: translateY(-1px);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #262626;
    }
    </style>
""", unsafe_allow_allowed_html=True, unsafe_allow_html=True)

# Application Header
st.markdown("# <span class='highlight'>RSUnits</span> Document Validator", unsafe_allow_html=True)

# Custom Instructions Block
st.markdown("""
<div class="instruction-card">
    <h4>📋 Required Documents for Prequalification</h4>
    <p>To verify your equity liquidity request, please upload clean screenshots or PDFs of:</p>
    <ul>
        <li><b>Most Recent RSU Details:</b> Must clearly show total share counts, scheduled vest dates, and current valuation/amounts.</li>
        <li><b>Most Recent Paystub:</b> Must display overall earnings, deductions, and current employment details.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# API Key Sidebar Input
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

uploaded_file = st.file_uploader("Upload RSU Schedule or Paystub (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Document Preview", use_column_width=True)

    if st.button("Validate Document"):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.spinner("Analyzing document with Gemini AI..."):
                try:
                    client = genai.Client(api_key=api_key)

                    prompt = (
                        "Analyze this document and extract the following details:\n"
                        "1. Document Type (RSU Holding/Schedule vs Paystub)\n"
                        "2. Total Shares, Grant Amounts, or Gross/Net Income\n"
                        "3. Upcoming Vesting Dates or Pay Period Dates\n"
                        "4. Account Holder / Employee Name\n"
                        "5. Document Legibility & Validity: Confirm if all required vesting/income metrics are clearly visible."
                    )

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[image, prompt]
                    )

                    st.success("Analysis Complete!")
                    st.markdown("### Extracted Verification Details")
                    st.write(response.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
