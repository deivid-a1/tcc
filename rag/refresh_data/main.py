import logging
import argparse
import os

import logger_setup
logger_setup.setup_logging()

from database import (
    setup_database, 
    clear_database, 
    insert_document, 
    get_db_summary
)
from processor import TextProcessor
from data_source import get_updated_information
from extractor import fetch_url_content, read_local_file_content
from config import LOCAL_DOCS_PATH

logger = logging.getLogger(__name__)

def run_ingestion(substitute=False):
    
    logger.info("--- 🚀 Iniciando pipeline de ingestão RAG UnB ---")

    try:
        logger.info("1. Configurando o banco de dados (pgvector)...")
        setup_database()
    except Exception as e:
        logger.critical("Pipeline interrompido: Não foi possível configurar o banco de dados.")
        return

    if substitute:
        logger.warning("[FLAG] --substitute detetada. Limpando dados antigos...")
        clear_database()
        logger.info("Banco de dados limpo.")

    try:
        logger.info("2. Carregando processador de texto (Modelo Hugging Face)...")
        processor = TextProcessor()
    except Exception as e:
        logger.critical("Pipeline interrompido: Não foi possível carregar o modelo de embedding.")
        return

    logger.info("3. Buscando fontes de dados atualizadas (Gemini Search)...")
    sources = get_updated_information()
    if not sources:
        logger.warning("Nenhuma fonte de dados da web encontrada na busca.")
    logger.info(f"{len(sources)} URLs únicas encontradas.")

    logger.info("4. Iniciando pipeline de ingestão (Arquivos Locais e Web)...")
    total_chunks_ingested = 0
    total_urls_processed = 0
    total_urls_failed = 0
    
    if os.path.exists(LOCAL_DOCS_PATH):
        logger.info(f"--- 4a. Processando Arquivos Locais de '{LOCAL_DOCS_PATH}' ---")
        for filename in os.listdir(LOCAL_DOCS_PATH):
            filepath = os.path.join(LOCAL_DOCS_PATH, filename)
            
            if not os.path.isfile(filepath):
                continue

            logger.info(f"Processando arquivo local: {filename}")
            text = read_local_file_content(filepath)
            
            if not text:
                logger.warning(f"Não foi possível extrair conteúdo de {filename}. Pulando.")
                total_urls_failed += 1
                continue
            
            total_urls_processed += 1
            chunks = processor.create_chunks(text)
            logger.debug(f"Texto dividido em {len(chunks)} chunks.")
            
            chunks_inserted_count = 0
            for chunk in chunks:
                embedding = processor.get_embedding(chunk)
                if embedding:
                    try:
                        insert_document(chunk, f"local:{filename}", embedding)
                        chunks_inserted_count += 1
                    except Exception as e:
                        logger.error(f"Falha ao inserir chunk (Arquivo: {filename}) no DB: {e}", exc_info=True)
            
            total_chunks_ingested += chunks_inserted_count
            logger.info(f"{chunks_inserted_count} chunks inseridos no banco para o arquivo {filename}.")
    else:
        logger.warning(f"Pasta de documentos locais '{LOCAL_DOCS_PATH}' não encontrada. Pulando etapa de arquivos locais.")

    
    logger.info(f"--- 4b. Processando URLs da Web ---")
    for idx, source in enumerate(sources):
        url = source['url']
        logger.info(f"Processando [{idx + 1}/{len(sources)}] URL: {url}")

        text = fetch_url_content(url)

        if not text:
            logger.warning("Não foi possível extrair conteúdo. Pulando.")
            total_urls_failed += 1
            continue
        
        total_urls_processed += 1
        logger.debug(f"Texto extraído com sucesso ({len(text)} caracteres).")
        
        chunks = processor.create_chunks(text)
        logger.debug(f"Texto dividido em {len(chunks)} chunks.")

        chunks_inserted_count = 0
        for chunk in chunks:
            embedding = processor.get_embedding(chunk)
            
            if embedding:
                try:
                    insert_document(chunk, url, embedding)
                    chunks_inserted_count += 1
                except Exception as e:
                    logger.error(f"Falha ao inserir chunk (URL: {url}) no DB: {e}", exc_info=True)
        
        total_chunks_ingested += chunks_inserted_count
        logger.info(f"{chunks_inserted_count} chunks inseridos no banco para esta URL.")

    logger.info("--- 🏁 Pipeline de Ingestão Concluído ---")
    logger.info(f"Resumo da Execução (Esta Rodada):")
    logger.info(f"  Fontes únicas processadas (Locais + Web): {total_urls_processed}")
    logger.info(f"  Fontes que falharam (Locais + Web): {total_urls_failed}")
    logger.info(f"  Total de Chunks ingeridos (nesta execução): {total_chunks_ingested}")

    try:
        logger.info("--- 📊 Resumo do Conteúdo Total no Banco de Dados ---")
        summary = get_db_summary()
        if summary:
            total_geral_chunks = 0
            for dominio, count in summary:
                logger.info(f"  - {dominio}: {count} chunks")
                total_geral_chunks += count
            logger.info(f"  Total Geral no Banco: {total_geral_chunks} chunks")
        else:
            logger.warning("  Não foi possível gerar o resumo do banco de dados (ou o banco está vazio).")
    except Exception as e:
        logger.error(f"  Falha ao gerar resumo final do DB: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de Ingestão RAG UnB")
    parser.add_argument(
        '--substitute',
        action='store_true',
        help="Se definido, limpa todos os dados do banco antes de iniciar a ingestão."
    )
    args = parser.parse_args()
    
    run_ingestion(substitute=args.substitute)