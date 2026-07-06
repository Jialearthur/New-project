from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("PROJECT_A_DATA_DIR", ROOT_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "index"
DB_PATH = DATA_DIR / "app.db"

APP_NAME = os.getenv("PROJECT_A_APP_NAME", "Project A QA Demo")
API_HOST = os.getenv("PROJECT_A_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PROJECT_A_API_PORT", "8000"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
DEFAULT_KB_NAME = os.getenv("DEFAULT_KB_NAME", "企业制度知识库")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

MIN_RETRIEVAL_SCORE = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.2"))
TOP_K = int(os.getenv("TOP_K", "5"))
CHUNK_MIN_CHARS = int(os.getenv("CHUNK_MIN_CHARS", "400"))
CHUNK_MAX_CHARS = int(os.getenv("CHUNK_MAX_CHARS", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
