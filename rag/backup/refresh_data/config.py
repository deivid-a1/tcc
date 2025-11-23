import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

DB_SETTINGS = {
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "unb_rag_db")
}

HF_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
VECTOR_DIMENSION = 768

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
LOCAL_DOCS_PATH = "documentos_locais/2026_01/"

SEED_URLS = [
    "https://boasvindas.unb.br/registro-academico",
    "https://boasvindas.unb.br/matricula",
    "https://boasvindas.unb.br/checklist"
]