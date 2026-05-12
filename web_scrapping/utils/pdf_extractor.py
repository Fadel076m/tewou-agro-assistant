import fitz  # PyMuPDF
import os
from .cleaning import clean_text

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF.
    """
    if not os.path.exists(pdf_path):
        return ""
    
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        full_text += page.get_text()
    
    doc.close()
    return clean_text(full_text)

def save_extracted_text(text, filename, output_dir=None):
    """
    Saves extracted text to a text file.
    """
    if output_dir is None:
        output_dir = os.path.join("data_collection", "extracted_text")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, filename + ".txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return output_path
