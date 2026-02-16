
import sys
import os
from src.analysis import analyze_content, synthesize_report_data

# Mock data
TEST_TEXT = """
Inspection Report
Date: 2024-02-15
Property: Flat 101, Test Building, Test City.
Observations:
1. Living Room: Severe dampness observed on the north wall (skirting level).
2. Kitchen: Leaking sink pipe.
"""

# Live Output Data Simulation
TEST_TEXT = """
Inspection Date: 27.09.2022 14:28 IST
Inspected By: Krushna & Mahesh
Property Type: Flat, Floors: 11
Score: 85.71%
Flagged Checklists: WC, External wall
Leakage due to concealed plumbing: Yes
Gaps/Blackish dirt Observed in tile joints: Yes
Impacted Areas from photos: 
- Master bedroom bathroom (positive side)
- Master bedroom wall dampness (negative side)
- External wall crack and Duct Issue (positive side)
"""

TEST_THERMAL_TEXT = """
Image 1: Hotspot 28.8 C, Coldspot 23.4 C, Delta 5.4 C
Image 2: Hotspot 27.4 C, Coldspot 22.4 C, Delta 5.0 C
"""

def test_system(api_key):
    print("1. Testing LLM Connection and Analysis Logic...")
    try:
        # Test Analysis (Text + Thermal)
        print("   Calling analyze_content...")
        result = analyze_content(api_key, TEST_TEXT, TEST_THERMAL_TEXT, image_files=[])
        
        print(f"   Analysis Result Snippet: {str(result)[:200]}...")

        if "85.71" in str(result) and "5.4" in str(result):
             print("   [SUCCESS] Data Extraction passed (Score/Delta detected).")
        else:
             print(f"   [WARNING] Data Extraction might have missed key fields: {result}")

        print("\n2. Testing Report Synthesis...")
        # Template
        with open("assets/main_ddr_template.txt", "r", encoding="utf-8") as f:
            template = f.read()
            
        report = synthesize_report_data(api_key, result, template)
        print(f"   Synthesis Response Snippet: {report[:200]}...")
        
        required_headers = [
            "1. PROPERTY ISSUE SUMMARY",
            "2. AREA-WISE OBSERVATIONS",
            "3. PROBABLE ROOT CAUSE",
            "4. SEVERITY ASSESSMENT",
            "5. RECOMMENDED ACTIONS",
            "6. ADDITIONAL NOTES",
            "7. MISSING OR UNCLEAR INFORMATION"
        ]
        
        missing_headers = [h for h in required_headers if h.upper() not in report.upper()]
        
        if not missing_headers:
            print("   [SUCCESS] Report Generation passed (All required sections present).")
        else:
            print(f"   [FAILURE] Report missing sections: {missing_headers}")
            print(f"   Report Content: {report[:500]}")
            # Optional: Don't exit here if we want to confirm OCR logic
            
        print("\n3. Testing Document Generation...")
        try:
             from src.generation import generate_pdf, generate_docx
             pdf_bytes = generate_pdf(report)
             if pdf_bytes and len(pdf_bytes) > 100:
                  print(f"   [SUCCESS] PDF Generation ({len(pdf_bytes)} bytes).")
             else:
                  print("   [FAILURE] PDF Generation result is empty or too small.")
                  
             docx_bytes = generate_docx(report)
             if docx_bytes and len(docx_bytes) > 100:
                  print(f"   [SUCCESS] DOCX Generation ({len(docx_bytes)} bytes).")
             else:
                  print("   [FAILURE] DOCX Generation result is empty or too small.")
                  
        except Exception as e:
             # traceback.print_exc()
             print(f"   [FAILURE] Document Generation crashed: {e}")
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   [ERROR] Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        
    if not api_key:
        print("Usage: python verify_installation.py [api_key] (or set OPENAI_API_KEY in .env)")
        sys.exit(1)
    
    test_system(api_key)
