import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from src.common.config import DB_SETTINGS, VECTOR_DIMENSION, TOP_K_RESULTS

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = psycopg2.connect(**DB_SETTINGS)
    conn.set_client_encoding('UTF8')
    return conn

def setup_database():
    try:
        with get_db_connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(f"""
                CREATE TABLE IF NOT EXISTS documentos_unb (
                    id SERIAL PRIMARY KEY,
                    conteudo TEXT NOT NULL,
                    metadados TEXT,
                    fonte VARCHAR(1024) NOT NULL,
                    data_ingestao TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    embedding VECTOR({VECTOR_DIMENSION}),
                    search_vector TSVECTOR
                );
                """)
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_hnsw_embedding
                ON documentos_unb
                USING hnsw (embedding vector_cosine_ops);
                """)
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_gin_search
                ON documentos_unb
                USING GIN(search_vector);
                """)
            conn.commit()
            logger.info("Banco de dados configurado (Híbrido + UTF8).")
    except Exception as e:
        logger.critical(f"Erro setup_database: {e}", exc_info=True)
        raise

def drop_table():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS documentos_unb CASCADE;")
            conn.commit()
            logger.info("Tabela excluída.")
    except Exception as e:
        logger.error(f"Erro drop_table: {e}")

def search_hybrid(query_text: str, query_embedding: list[float], limit: int = TOP_K_RESULTS):
    try:
        with get_db_connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                sql = """
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
                cur.execute(sql, (query_embedding, query_embedding, query_text, query_text, limit))
                results = cur.fetchall()
                return [{"conteudo": r[0], "fonte": r[1]} for r in results]
    except Exception as e:
        logger.error(f"Erro search_hybrid: {e}", exc_info=True)
        return []