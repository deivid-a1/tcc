import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import config

logger = logging.getLogger(__name__)

logger.info(f"Carregando modelo de embedding: {config.HF_MODEL_NAME}...")
try:
    EMBEDDING_MODEL = SentenceTransformer(config.HF_MODEL_NAME)
    logger.info("Modelo de embedding carregado com sucesso.")
except Exception as e:
    logger.critical(f"Falha ao carregar modelo SentenceTransformer: {e}", exc_info=True)
    raise

def search_rag(query: str) -> dict:
    try:
        query_embedding = EMBEDDING_MODEL.encode(query)

        with psycopg2.connect(**config.DB_SETTINGS) as conn:
            register_vector(conn)
            
            with conn.cursor() as cur:
                sql_query = f"""
                    SELECT {config.TEXT_COLUMN}, {config.SOURCE_COLUMN}
                    FROM {config.DB_TABLE}
                    ORDER BY {config.VECTOR_COLUMN} <-> %s
                    LIMIT %s
                """
                cur.execute(sql_query, (query_embedding, config.TOP_K_RESULTS))
                results = cur.fetchall()
                
                contextos = [row[0] for row in results]
                fontes = [row[1] for row in results]
                
                return {"contexto": contextos, "fontes": fontes}
                
    except Exception as e:
        logger.error(f"Erro ao consultar PGVector: {e}", exc_info=True)
        return {"contexto": [], "fontes": []}