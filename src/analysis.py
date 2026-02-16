
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
import base64
import io

def get_llm(api_key: str):
    """Initializes the LLM with the provided API key."""
    return ChatOpenAI(temperature=0, openai_api_key=api_key, model_name="gpt-4o")

def analyze_content(api_key: str, text_content: str, thermal_text_content: str, image_files: list, use_tesseract: bool = False) -> dict:
    """
    Analyzes inspection text, thermal text, and images to extract structured data for the DDR.
    Returns a dictionary with keys corresponding to DDR sections.
    """
    llm = get_llm(api_key)
    
    # 1. Text Analysis (Sample Report + Thermal Report)
    text_prompt = PromptTemplate(
        input_variables=["text", "thermal_text"],
        template="""
        You are an expert structural engineer. Analyze the following inspection and thermal reports.
        
        INSPECTION REPORT TEXT:
        {text}
        
        THERMAL REPORT TEXT:
        {thermal_text}
        
        TASK:
        1. Extract specific details to fill the DDR Sections.
        2. **General Info**: Look for "Inspected By", "Score" (e.g. 85.71%), "Property Age", "Floors".
        3. **Observations**: Extract "Impacted Areas" and map them to findings (e.g. "Master Bedroom: Wall dampness").
        4. **Thermal**: Calculate Delta = Hotspot - Coldspot. If > 4.0C, flag as "Moisture Confirmed".
        5. **Root Causes**: Extract "Yes" items from checklists (e.g. "Concealed plumbing: Yes").
        
        OUTPUT FORMAT (JSON-like):
        {{
            "report_header": {{
                "Date": "DD.MM.YYYY", 
                "Inspected_By": "Name",
                "Report_ID": "ID or 'Not Available'"
            }},
            "issue_summary": "High-level summary of dampness, cracks, etc.",
            "observations": [
                {{ "Area": "Master Bedroom", "Issue": "Wall dampness (Negative Side)", "Thermal_Delta": "5.0C (Moisture Confirmed)" }}
            ],
            "root_causes": ["Leakage due to concealed plumbing", "Gaps in tile joints"],
            "severity_assessment": {{
                "score": "85.71%",
                "scale": "Moderate",
                "reasoning": "Score + Moderate cracks indicates periodic maintenance needed."
            }},
            "recommended_actions": ["Grouting", "Plumbing repair"],
            "additional_notes": "Any other key observations.",
            "missing_info": "Client address not found."
        }}
        """
    )
    
    combined_text_analysis = ""
    try:
        # Truncate to fit context if needed, but prioritizing both reports
        response = llm.invoke(text_prompt.format(
            text=text_content[:10000], 
            thermal_text=thermal_text_content[:5000]
        ))
        combined_text_analysis = response.content
    except Exception as e:
        combined_text_analysis = f"Error during text analysis: {str(e)}"
    
    # 2. Image Analysis (Thermal/Site Images)
    image_observations = []
    
    if image_files:
        if use_tesseract:
             # LOCAL OCR (Serial)
             try:
                 import pytesseract
                 # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
                 for img_file in image_files:
                     try:
                         text = pytesseract.image_to_string(img_file)
                         image_observations.append(f"[OCR Result]: {text.strip()}")
                     except Exception as e:
                         image_observations.append(f"Error analyzing image with Tesseract: {str(e)}")
             except ImportError:
                 image_observations.append("Error: pytesseract not installed.")
        else:
            # GPT-4o VISION (Parallel Batch)
            batch_messages = []
            for img_file in image_files:
                try:
                    # Convert PIL Image to base64
                    buffered = io.BytesIO()
                    img_file.save(buffered, format="PNG") 
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    msg = HumanMessage(content=[
                        {"type": "text", "text": "Analyze this image. If it's a thermal image, read the Max/Min temperatures and calculate the difference. If >4C, note moisture. If normal photo, note cracks/dampness. Return a concise observation string."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
                    ])
                    batch_messages.append([msg])
                except Exception as e:
                    image_observations.append(f"Error preparing image: {str(e)}")

            if batch_messages:
                try:
                    # Use batch processing with concurrency to speed up analysis
                    # 5 concurrent requests is a safe default to avoid rate limits
                    responses = llm.batch(batch_messages, config={"max_concurrency": 5})
                    for resp in responses:
                        image_observations.append(resp.content)
                except Exception as e:
                    image_observations.append(f"Error during batch analysis: {str(e)}")

    return {
        "text_analysis": combined_text_analysis,
        "image_analysis": image_observations
    }

def synthesize_report_data(api_key: str, analysis_results: dict, template_style: str) -> str:
    """
    Synthesizes the analyzed data into the final DDR structure using the template as a guide.
    """
    llm = get_llm(api_key)
    
    prompt = f"""
    You are a professional report writer for a structural engineering firm.
    Your task is to populate the following DDR TEMPLATE with the ANALYZED DATA.
    
    ANALYZED DATA:
    {analysis_results.get('text_analysis')}
    Image Observations: {analysis_results.get('image_analysis')}
    
    DDR TEMPLATE (Markdown):
    {template_style}
    
    INSTRUCTIONS:
    1. **Fill the Template**: Replace placeholders (like "Not Available" in the specific sections) ONLY if data exists.
    2. **Keep "Not Available"**: If data (like Client Name, Report ID) is missing, KEEP "Not Available".
    3. **Structure**: Follow the 7 sections strictly.
    4. **Formatting (CRITICAL)**: 
       - Every Header (e.g., ## 2. AREA-WISE OBSERVATIONS) MUST start on a NEW LINE with exactly TWO empty lines before it.
       - EVERY bullet point (e.g., - **Area**: ...) MUST be on its own line. Never merge bullet points into a single block of text.
       - Avoid truncating sentences. Complete every thought.
       - Do NOT output redundant '#' symbols or duplicate headers.
    5. **Tone**: Professional, client-friendly, no jargon.
    
    OUTPUT:
    Return the fully filled Markdown report. Do not change the Section Headers. Ensure there is no trailing truncated text.
    """
    
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error synthesizing report: {str(e)}"
