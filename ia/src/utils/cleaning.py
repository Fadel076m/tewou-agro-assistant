import re
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

def clean_text(text):
    if not text:
        return ""
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.,!?;:\(\)éèàâêîôûëïüç-]', '', text)
    return text.strip()

def detect_language(text):
    try:
        if not text or len(text) < 10:
            return "unknown"
        return detect(text)
    except:
        return "unknown"
