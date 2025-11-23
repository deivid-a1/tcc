import logging
import argparse
import os
from src.common.logger import setup_logging
from src.common.database import setup_database, drop_table, get_db_connection
from src.common.config import LOCAL_DOCS_PATH, SEED_URLS
from src.ingestor.processor import TextProcessor
from src.ingestor.crawler import crawl_seeds
from src.ingestor.extractor import fetch_url_content, read_local_file_content

setup_logging("ingestor")
logger = logging.getLogger(__name__)

def insert_document(conteudo, fonte, embedding, metadados):
    from pgvector.psycopg2 import register_vector
    try:
        with get_db_connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documentos_unb (conteudo, fonte, embedding, metadados, search_vector)
                    VALUES (%s, %s, %s, %s, setweight(to_tsvector('portuguese', %s), 'A') || setweight(to_tsvector('portuguese', %s), 'B'));
                """, (conteudo, fonte, embedding, metadados, metadados, conteudo))
            conn.commit()
    except Exception as e:
        logger.error(f"Erro insert: {e}")

def run_ingestion(substitute=False):
    logger.info("--- Pipeline Unificado Iniciado ---")
    if substitute: drop_table()
    setup_database()
    
    try:
        processor = TextProcessor()
    except Exception: return

    if os.path.exists(LOCAL_DOCS_PATH):
        for f in os.listdir(LOCAL_DOCS_PATH):
            path = os.path.join(LOCAL_DOCS_PATH, f)
            if os.path.isfile(path):
                text = read_local_file_content(path)
                if text:
                    meta = processor.enrich_text(text)
                    for chunk in processor.create_chunks(text):
                        insert_document(chunk, f"local:{f}", processor.get_embedding(chunk), meta)

    for url in crawl_seeds(SEED_URLS):
        text = fetch_url_content(url)
        if text:
            meta = processor.enrich_text(text)
            for chunk in processor.create_chunks(text):
                insert_document(chunk, url, processor.get_embedding(chunk), meta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--substitute', action='store_true')
    args = parser.parse_args()
    run_ingestion(args.substitute)