import logging
import argparse
import os

import logger_setup
logger_setup.setup_logging()

from database import setup_database, clear_database, drop_table, insert_document, get_db_summary
from processor import TextProcessor
from crawler import crawl_seeds
from extractor import fetch_url_content, read_local_file_content
from config import LOCAL_DOCS_PATH, SEED_URLS

logger = logging.getLogger(__name__)

def run_ingestion(substitute=False):
    logger.info("--- Iniciando Pipeline Híbrido ---")

    try:
        if substitute:
            logger.warning("Modo substituição: Excluindo tabela antiga para recriação do esquema...")
            drop_table()

        setup_database()
        
        processor = TextProcessor()
    except Exception:
        return

    logger.info("--- 1. Processando Arquivos Locais ---")
    if os.path.exists(LOCAL_DOCS_PATH):
        for filename in os.listdir(LOCAL_DOCS_PATH):
            filepath = os.path.join(LOCAL_DOCS_PATH, filename)
            if not os.path.isfile(filepath): continue
            
            logger.info(f"Arquivo: {filename}")
            text = read_local_file_content(filepath)
            if not text: continue
            
            keywords = processor.enrich_text(text)
            chunks = processor.create_chunks(text)
            
            for chunk in chunks:
                emb = processor.get_embedding(chunk)
                insert_document(chunk, f"local:{filename}", emb, metadados=keywords)

    logger.info("--- 2. Processando URLs (Crawler) ---")
    target_urls = crawl_seeds(SEED_URLS)
    logger.info(f"{len(target_urls)} URLs identificadas.")

    for url in target_urls:
        logger.info(f"URL: {url}")
        text = fetch_url_content(url)
        if not text: continue

        keywords = processor.enrich_text(text)
        chunks = processor.create_chunks(text)
        
        for chunk in chunks:
            emb = processor.get_embedding(chunk)
            insert_document(chunk, url, emb, metadados=keywords)

    logger.info("--- Concluído ---")
    get_db_summary()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--substitute', action='store_true')
    args = parser.parse_args()
    run_ingestion(substitute=args.substitute)