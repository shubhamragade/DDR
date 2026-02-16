
import streamlit as st
import os
from src.ingestion import load_pdf, process_image, load_template
from src.analysis import analyze_content, synthesize_report_data
from src.generation import generate_ddr_markdown
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="AI DDR Generator", layout="wide")

st.title("🏗️ Automated Detailed Diagnostic Report (DDR) Generator")

# Sidebar for API Key and Configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key Handling
    env_api_key = os.getenv("OPENAI_API_KEY")
    if env_api_key:
        api_key = env_api_key
        st.success("API Key loaded from environment.")
    else:
        api_key = st.text_input("OpenAI API Key", type="password", help="Required for GPT-4o analysis.")
        if not api_key:
            st.warning("Please enter your API Key to proceed.")
            st.stop()
            
    # OCR Engine Selection
    ocr_engine = st.radio(
        "OCR Engine",
        ("GPT-4o Vision (High Accuracy)", "Tesseract (Local/Free)"),
        index=0,
        help="Use GPT-4o for best results on complex forms. Tesseract requires local installation."
    )

# File Upload Section
st.header("1. Upload Documents")
col1, col2 = st.columns(2)

with col1:
    uploaded_pdf = st.file_uploader("Upload Inspection Report (PDF)", type="pdf", key="inspection_pdf")
    uploaded_thermal_pdf = st.file_uploader("Upload Thermal Report (PDF - Optional)", type="pdf", key="thermal_pdf")
with col2:
    uploaded_images = st.file_uploader("Upload Additional Thermal/Site Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Main Processing Logic
if st.button("Generate DDR Report"):
    if not uploaded_pdf:
        st.error("Please upload the Sample Inspection Report PDF.")
    else:
        with st.spinner("Processing documents..."):
            # 1. Ingestion
            # -- Extract Text --
            text_content = load_pdf(uploaded_pdf)
            st.success(f"Inspection Report Loaded: {len(text_content)} chars.")
            
            thermal_text_content = ""
            if uploaded_thermal_pdf:
                thermal_text_content = load_pdf(uploaded_thermal_pdf)
                st.success(f"Thermal Report Loaded: {len(thermal_text_content)} chars.")
            
            # -- Extract Images --
            # We want to prioritize Manual Uploads -> Thermal PDF -> Inspection PDF
            # because we limit to 20 images, and Thermal/Manual are most critical.
            
            manual_images = []
            thermal_pdf_images = []
            inspection_pdf_images = []

            # 1. From Manual Uploads
            if uploaded_images:
                for img_file in uploaded_images:
                    img = process_image(img_file)
                    if img:
                        manual_images.append(img)
                st.success(f"Processed {len(manual_images)} manually uploaded images.")

            # 2. From Thermal PDF
            from src.ingestion import extract_images_from_pdf
            if uploaded_thermal_pdf:
                thermal_pdf_images = extract_images_from_pdf(uploaded_thermal_pdf)
                if thermal_pdf_images:
                     st.info(f"Extracted {len(thermal_pdf_images)} images from Thermal Report.")

            # 3. From Inspection PDF
            if uploaded_pdf:
                inspection_pdf_images = extract_images_from_pdf(uploaded_pdf)
                if inspection_pdf_images:
                    st.info(f"Extracted {len(inspection_pdf_images)} images from Inspection Report.")

            # Combine in priority order
            processed_images = manual_images + thermal_pdf_images + inspection_pdf_images

            # 2. Analysis
            st.info("Analyzing content with AI... (This may take a moment for large reports)")
            
            try:
                # Load template text for style guide
                template_text = load_template("assets/main_ddr_template.txt")
                
                # Analyze docs (Text + Images)
                use_tesseract = "Tesseract" in ocr_engine
                analysis_result = analyze_content(api_key, text_content, thermal_text_content, processed_images, use_tesseract=use_tesseract)
                
                # Synthesize final report based on template structure
                final_report_md = synthesize_report_data(api_key, analysis_result, template_text)
                
                # 3. Generation (Formatting wrapper)
                final_output = generate_ddr_markdown({'report_content': final_report_md}, "")
                
                # Generate Binary Formats
                from src.generation import generate_pdf, generate_docx
                pdf_bytes = generate_pdf(final_output)
                docx_bytes = generate_docx(final_output)
                
                # Display Result
                st.subheader("Generated Detailed Diagnostic Report")
                st.markdown(final_output)
                
                st.subheader("Download Options")
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    st.download_button(
                        label="Download Markdown",
                        data=final_output,
                        file_name="Generated_DDR.md",
                        mime="text/markdown"
                    )
                with col_dl2:
                    if pdf_bytes:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_bytes,
                            file_name="Generated_DDR.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("PDF generation failed.")
                with col_dl3:
                    if docx_bytes:
                        st.download_button(
                            label="Download Word (DOCX)",
                            data=docx_bytes,
                            file_name="Generated_DDR.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    else:
                        st.error("DOCX generation failed.")
                
            except Exception as e:
                st.error(f"An error occurred during generation: {str(e)}")
