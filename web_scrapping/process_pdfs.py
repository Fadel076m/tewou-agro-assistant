import os
import json
from utils.pdf_extractor import extract_text_from_pdf, save_extracted_text
from utils.metadata import add_metadata

def process_existing_pdfs():
    raw_dir = os.path.join("data_collection", "raw_pdfs")
    extracted_dir = os.path.join("data_collection", "extracted_text")
    
    if not os.path.exists(raw_dir):
        print(f"Directory {raw_dir} not found.")
        return

    pdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDFs to process.")

    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(raw_dir, pdf_file)
        print(f"[{i+1}/{len(pdf_files)}] Extracting: {pdf_file}")
        
        try:
            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                save_extracted_text(text, pdf_file, extracted_dir)
                
                # Add to metadata if not already there
                add_metadata({
                    "source_url": f"local://raw_pdfs/{pdf_file}",
                    "file_type": "pdf",
                    "content": f"extracted_text/{pdf_file}.txt",
                    "metadata": {
                        "title": pdf_file.replace(".pdf", "").replace("_", " "),
                        "date": "N/A",
                        "language": "fr", # Defaulting to fr for now
                        "category": "document_local",
                        "region": "Sénégal",
                        "file_size": f"{os.path.getsize(pdf_path)/1024:.2f} KB"
                    }
                })
            else:
                print(f"Warning: No text extracted from {pdf_file}")
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    print("PDF processing completed.")

if __name__ == "__main__":
    process_existing_pdfs()
