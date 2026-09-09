from pathlib import Path
import os

# ============================================================
# DIRECTORY PATHS
# ============================================================

AGENT_DIR = Path(__file__).resolve().parent
AI_TRAINING_DIR = AGENT_DIR.parent
PROJECT_ROOT = AI_TRAINING_DIR.parent

VECTOR_STORE_DIR = AI_TRAINING_DIR / "vector_store"
KNOWLEDGE_DIR = AI_TRAINING_DIR / "data" / "knowledge"
TAXONOMY_FILE = AI_TRAINING_DIR / "taxonomy" / "l1_taxonomy.json"

# ============================================================
# VECTOR STORE & EMBEDDING
# ============================================================

COLLECTION_NAME = "iskra_knowledge"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5

# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_TAGS_URL = os.getenv("OLLAMA_TAGS_URL", "http://127.0.0.1:11434/api/tags")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "granite4.2:8b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "45"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.0"))
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "150"))

# ============================================================
# BUSINESS ROUTING CONFIGURATION
# ============================================================
# NOTE: Confirmed verified baseline rules from project taxonomy:
#   Software -> L2 Software
#   Hardware -> L2 Hardware
#   Firmware -> L2 Firmware
#
# IMPORTANT:
# Communication routing (and any category not explicitly proven by
# project documentation) is NOT a verified ISKRA company policy.
# It is provided solely as a DEFAULT CONFIGURATION VALUE and is fully
# configurable via environment variables or ROUTING_MAP.
# ============================================================

ROUTING_MAP = {
    "Software": os.getenv("ROUTING_SOFTWARE", "L2 Software"),
    "Hardware": os.getenv("ROUTING_HARDWARE", "L2 Hardware"),
    "Firmware": os.getenv("ROUTING_FIRMWARE", "L2 Firmware"),
    # DEFAULT CONFIGURATION VALUE (not verified company policy):
    "Communication": os.getenv("ROUTING_COMMUNICATION", "L2 Software"),
    # DEFAULT CONFIGURATION VALUE (not verified company policy):
    "Configuration": os.getenv("ROUTING_CONFIGURATION", "L2 Software"),
    # DEFAULT CONFIGURATION VALUE (not verified company policy):
    "Meter Data": os.getenv("ROUTING_METER_DATA", "L2 Software"),
    # DEFAULT CONFIGURATION VALUE (not verified company policy):
    "Testing": os.getenv("ROUTING_TESTING", "L2 Hardware"),
    # DEFAULT CONFIGURATION VALUE (not verified company policy):
    "Installation": os.getenv("ROUTING_INSTALLATION", "L2 Hardware"),
    "Unknown": os.getenv("ROUTING_UNKNOWN", "L1 Review"),
}

DEFAULT_ROUTING = os.getenv("DEFAULT_ROUTING", "L1 Review")
