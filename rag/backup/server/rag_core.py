import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import config

logger = logging.getLogger(__name__)

try:
    EMBEDDING_MODEL = SentenceTransformer(config.HF_MODEL_NAME)
except Exception as e:
    logger.critical(f"Falha ao carregar modelo: {e}", exc_info=True)
    raise

def get_db_connection():
    conn = psycopg2.connect(**config.DB_SETTINGS)
    conn.set_client_encoding('UTF8')
    return conn

def search_rag(query: str) -> dict:
    try:
        query_embedding = EMBEDDING_MODEL.encode(query).tolist()

        with get_db_connection() as conn:
            register_vector(conn)
            
            with conn.cursor() as cur:
                sql_query = """
                WITH semantic_search AS (
                    SELECT id, conteudo, fonte, 
                           RANK() OVER (ORDER BY embedding <=> %s::vector) as rank_semantic
                    FROM documentos_unb
                    ORDER BY embedding <=> %s::vector
                    LIMIT 20
                ),
                keyword_search AS (
                    SELECT id, conteudo, fonte,
                           RANK() OVER (ORDER BY ts_rank_cd(search_vector, websearch_to_tsquery('portuguese', %s)) DESC) as rank_keyword
                    FROM documentos_unb
                    WHERE search_vector @@ websearch_to_tsquery('portuguese', %s)
                    LIMIT 20
                )
                SELECT 
                    COALESCE(s.conteudo, k.conteudo) as conteudo,
                    COALESCE(s.fonte, k.fonte) as fonte,
                    COALESCE(1.0 / (60 + s.rank_semantic), 0.0) + 
                    COALESCE(1.0 / (60 + k.rank_keyword), 0.0) as rrf_score
                FROM semantic_search s
                FULL OUTER JOIN keyword_search k ON s.id = k.id
                ORDER BY rrf_score DESC
                LIMIT %s;
                """
                
                cur.execute(sql_query, (
                    query_embedding, 
                    query_embedding, 
                    query, 
                    query, 
                    config.TOP_K_RESULTS
                ))
                
                rows = cur.fetchall()
                
                contextos = [r[0] for r in rows]
                fontes = [r[1] for r in rows]
                
                return {"contexto": contextos, "fontes": fontes}
                
    except Exception as e:
        logger.error(f"Erro no search_rag: {e}", exc_info=True)
        return {"contexto": [], "fontes": []}