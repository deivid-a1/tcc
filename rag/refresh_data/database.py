import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from config import DB_SETTINGS, VECTOR_DIMENSION

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = psycopg2.connect(**DB_SETTINGS)
    return conn

def setup_database():
    try:
        with get_db_connection() as conn:
            register_vector(conn) 
            
            with conn.cursor() as cur:
                
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS documentos_unb (
                    id SERIAL PRIMARY KEY,
                    conteudo TEXT NOT NULL,
                    fonte VARCHAR(1024) NOT NULL,
                    data_ingestao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    embedding VECTOR({VECTOR_DIMENSION})
                );
                """
                cur.execute(create_table_query)
                
                create_index_query = """
                CREATE INDEX IF NOT EXISTS idx_hnsw_embedding
                ON documentos_unb
                USING hnsw (embedding vector_cosine_ops);
                """
                cur.execute(create_index_query)
            
            conn.commit()
            logger.info("Banco de dados configurado e tabelas/índices verificados.")
            
    except Exception as e:
        logger.critical(f"Falha crítica ao configurar o banco de dados: {e}", exc_info=True)
        raise

def clear_database():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE documentos_unb RESTART IDENTITY;")
            conn.commit()
            logger.info("Banco de dados (tabela documentos_unb) limpo com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao limpar o banco de dados: {e}", exc_info=True)
        raise

def insert_document(conteudo: str, fonte: str, embedding: list[float]):
    try:
        with get_db_connection() as conn:
            register_vector(conn) 
            
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO documentos_unb (conteudo, fonte, embedding) VALUES (%s, %s, %s)",
                    (conteudo, fonte, embedding)
                )
            conn.commit()
    except Exception as e:
        logger.error(f"Falha ao inserir documento (fonte: {fonte}) no DB: {e}", exc_info=True)

def get_db_summary() -> list[tuple]:
    logger.debug("Executando consulta de resumo do banco de dados...")
    
    summary_query = """
        SELECT 
            REGEXP_REPLACE(fonte, 'https?://([^/]+)/.*', '\1') AS dominio, 
            COUNT(*) AS total_chunks
        FROM 
            documentos_unb
        GROUP BY 
            dominio
        ORDER BY 
            total_chunks DESC;
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(summary_query)
                results = cur.fetchall()
                return results
    except Exception as e:
        logger.error(f"Falha ao gerar o resumo do banco de dados: {e}", exc_info=True)
        return []