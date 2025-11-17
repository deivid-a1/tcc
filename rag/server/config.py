import os
from dotenv import load_dotenv

load_dotenv()

DB_SETTINGS = {
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "unb_rag_db")
}

HF_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
VECTOR_DIMENSION = 768

DB_TABLE = "documentos_unb"
TEXT_COLUMN = "conteudo"
SOURCE_COLUMN = "fonte"
VECTOR_COLUMN = "embedding"

TOP_K_RESULTS = 5