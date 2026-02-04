import json
import os
from datetime import datetime

METADATA_PATH = os.path.join("data_collection", "metadata.json")

def initialize_metadata():
    """
    Initializes the metadata file if it doesn't exist.
    """
    if not os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)

def add_metadata(entry):
    """
    Adds a new entry to the metadata record.
    entry: dict following the structure defined in the prompt.
    """
    initialize_metadata()
    
    with open(METADATA_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        
        # Add common metadata fields if missing
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
