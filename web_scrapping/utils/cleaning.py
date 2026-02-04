import re
import unicodedata
from langdetect import detect, DetectorFactory

# Ensure reproducible language detection
DetectorFactory.seed = 0

def clean_text(text):
    """
    Cleans extracted text by removing extra whitespaces, 
    normalizing unicode characters and basic filtering.
    """
    if not text:
        return ""
    
    # Normalize unicode (decompose combined characters)
    text = unicodedata.normalize('NFKC', text)
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove repetitive headers/footers (basic heuristic)
    # This can be expanded based on observed patterns
    
    return text

def detect_language(text):
    """
    Detects the language of the provided text.
    Returns 'fr', 'en', 'wo' (if possible), etc.
    """
    if not text or len(text.strip()) < 10:
        return "unknown"
    
    try:
        lang = detect(text)
        return lang
    except:
        return "unknown"

def extract_tables_from_html(soup):
    """
    Basic helper to extract table data from a BeautifulSoup object.
    """
    tables = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            rows.append(cols)
        tables.append(rows)
    return tables
