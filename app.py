import streamlit as st
import google.genai as genai
from PIL import Image

# Page Configuration
st.set_page_config(page_title="RSU & Income Validator", layout="centered")

st.title("📄 Document & RSU Validator")
st.write("Upload your RSU holding screenshot or pay stub to extract key details.")

# Sidebar for API Key input or environment configuration
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

uploaded_file = st.file_uploader("Choose an image (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Document", use_column_width=True)

    if st.button("Validate Document"):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with st.spinner("Analyzing document with Gemini AI..."):
                try:
                    # Initialize Gemini Client
                    client = genai.Client(api_key=api_key)

                    prompt = (
                        "Analyze this screenshot/document and extract the following details:\n"
                        "1. Document Type (RSU Holding / Pay Stub / Other)\n"
                        "2. Total Shares or Gross/Net Income\n"
                        "3. Vesting Dates or Pay Period\n"
                        "4. Account Holder / Employee Name\n"
                        "5. Verification Status: Indicate if the document appears valid and legible."
                    )

                    # Send request to Gemini model
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[image, prompt]
                    )

                    st.success("Analysis Complete!")
                    st.markdown("### Extracted Information")
                    st.write(response.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")

