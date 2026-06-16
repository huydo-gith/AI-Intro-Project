import json
from pathlib import Path

KB_FILE_PATH = Path(__file__).resolve().parent / "knowledge_base.json"

FACTS = {}
QUICK_FACT_KEYS = []
RULES = []
DIAGNOSIS_METADATA = {}

def load_kb() -> dict:
    """Load the knowledge base from JSON."""
    if not KB_FILE_PATH.exists():
        return {"FACTS": {}, "RULES": [], "DIAGNOSIS_METADATA": {}, "QUICK_FACT_KEYS": []}
    
    with open(KB_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_kb(data: dict) -> None:
    """Save the knowledge base to JSON."""
    with open(KB_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def reload_kb_in_memory() -> None:
    """Reload the knowledge base into memory in-place so all other modules see changes."""
    data = load_kb()
    
    FACTS.clear()
    FACTS.update(data.get("FACTS", {}))
    
    QUICK_FACT_KEYS.clear()
    QUICK_FACT_KEYS.extend(data.get("QUICK_FACT_KEYS", []))
    
    RULES.clear()
    RULES.extend(data.get("RULES", []))
    
    DIAGNOSIS_METADATA.clear()
    DIAGNOSIS_METADATA.update(data.get("DIAGNOSIS_METADATA", {}))

# Load immediately on module import
reload_kb_in_memory()
