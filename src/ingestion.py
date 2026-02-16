
import io
from typing import List, Union
import pypdf
from PIL import Image

def load_pdf(file) -> str:
    """Extracts text from a PDF file-like object."""
    try:
        reader = pypdf.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_images_from_pdf(file) -> List[Image.Image]:
    """Extracts images embedded in a PDF file."""
    images = []
    try:
        # Use pdfplumber for better image extraction
        import pdfplumber
        
        # Reset file pointer if needed, but pdfplumber handles bytes/file objects
        # We might need to copy the file to a temporary buffer if it's a stream
        if hasattr(file, 'seek'):
            file.seek(0)
            
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                for img_obj in page.images:
                    try:
                        # Extract the image bytes
                        # pdfplumber provides coordinates and object IDs
                        # We need to use the page's .to_image() cropped, OR extract raw bytes
                        # A robust way is to use page.crop(bbox).to_image().original
                        
                        bbox = (img_obj['x0'], img_obj['top'], img_obj['x1'], img_obj['bottom'])
                        cropped_page = page.crop(bbox)
                        img = cropped_page.to_image(resolution=300).original
                        
                        # Filter small images (likely icons/logos)
                        if img.width > 200 and img.height > 200:
                            images.append(img)
                    except Exception as img_err:
                        print(f"Skipping an image: {img_err}")
        return images
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")
        return []

def process_image(file) -> Image.Image:
    """Loads an image file-like object for further processing."""
    try:
        image = Image.open(file)
        return image
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def load_template(template_path: str = "assets/main_ddr_template.txt") -> str:
    """Loads the reference DDR template."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Template file not found."
