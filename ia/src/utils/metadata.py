import json
import os
from datetime import datetime

# Path relative to the root of the 'ia' directory where app.py is run
METADATA_PATH = os.path.join("..", "web_scrapping", "data_collection", "metadata.json")

def initialize_metadata():
    """
    Initializes the metadata file if it doesn't exist.
    """
    if not os.path.exists(METADATA_PATH):
        # We probably shouldn't create it here if it's supposed to be in web_scrapping,
        # but for safety:
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)

def add_metadata(entry):
    """
    Adds a new entry to the metadata record.
    """
    initialize_metadata()
    
    with open(METADATA_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()

def get_all_metadata():
    """
    Returns the list of all metadata records.
    """
    if not os.path.exists(METADATA_PATH):
        return []
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
