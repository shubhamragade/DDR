import os
import sys
from src.generation import generate_pdf

# Worst-case malformed Markdown based on user reports
WORST_CASE_MARKDOWN = """
# DETAILED DIAGNOSTIC REPORT
**Date:** 27.09.2022
---
#
# 1. PROPERTY ISSUE SUMMARY
The inspection revealed multiple areas with dampness at skirting levels, tile hollowness, #
# 2. AREA-WISE OBSERVATIONS
- **Hall:** Skirting level dampness (Negative Side), Thermal Delta: 5.4C (Moisture Confirm- **Bedroom:** Skirting level dampness (Negative Side), Thermal Delta: 5.0C (Moisture Conf- **Master Bedroom:** Skirting level dampness (Negative Side), Thermal Delta: 5.0C (Moistu- **Kitchen:** Skirting level dampness (Negative Side), Thermal Delta: 5.0C (Moisture Conf- **Master Bedroom:** Wall dampness (Negative Side), Thermal Delta: 5.0C (Moisture Confirm- **Parking Area:** Seepage (Negative Side), Thermal Delta: 5.0C (Moisture Confirmed)
- **Common Bathroom:** Ceiling dampness (Negative Side)

## 3. PROBABLE ROOT CAUSE
- Leakage due to concealed plumbing- Gaps in tile joints- Damage in Nahani trap## 4. SEVERITY ASSESSMENT
**Score:** 85.71%
"""

def test_pdf():
    print("Generating PDF from worst-case malformed Markdown...")
    pdf_bytes = generate_pdf(WORST_CASE_MARKDOWN)
    
    if pdf_bytes:
        with open("test_advanced_fix.pdf", "wb") as f:
            f.write(pdf_bytes)
        print(f"Success! Test PDF generated: {os.path.abspath('test_advanced_fix.pdf')}")
        print(f"Size: {len(pdf_bytes)} bytes")
    else:
        print("Failure: PDF generation returned empty bytes.")

if __name__ == "__main__":
    test_pdf()
