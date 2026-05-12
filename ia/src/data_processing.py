import os
import json
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_documents(data_dir="../../web_scrapping/data_collection"):
    """
    Loads documents from extracted_text (txt) and web_content (json).
    """
    documents = []
    
    # Load TXT files from extracted_text
    txt_dir = os.path.join(data_dir, "extracted_text")
    if os.path.exists(txt_dir):
        for filename in os.listdir(txt_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(txt_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        if text.strip():
                            documents.append(Document(
                                page_content=text,
                                metadata={"source": filename, "type": "txt"}
                            ))
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

    # Load JSON files from web_content
    web_dir = os.path.join(data_dir, "web_content")
    if os.path.exists(web_dir):
        for filename in os.listdir(web_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(web_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        content = data.get("content", "")
                        if content.strip():
                            metadata = data.get("metadata", {})
                            metadata["source"] = data.get("source_url", filename)
                            metadata["type"] = "json"
                            documents.append(Document(
                                page_content=content,
                                metadata=metadata
                            ))
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
                    
    logger.info(f"Loaded {len(documents)} document(s).")
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=100):
    """
    Splits documents into smaller chunks for the vector store.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunk(s).")
    return chunks

if __name__ == "__main__":
    docs = load_documents()
    chunks = split_documents(docs)
    for i, chunk in enumerate(chunks[:3]):
        print(f"--- Chunk {i} ---")
        print(chunk.page_content[:200])
        print(chunk.metadata)
