import logging
import psycopg2
from pgvector.psycopg2 import register_vector
from config import DB_SETTINGS, VECTOR_DIMENSION

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
            logger.info("Tabela documentos_unb excluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro drop_table: {e}", exc_info=True)
        raise

def clear_database():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE documentos_unb RESTART IDENTITY;")
            conn.commit()
    except Exception as e:
        logger.error(f"Erro clear_database: {e}", exc_info=True)
        raise

def insert_document(conteudo: str, fonte: str, embedding: list[float], metadados: str = ""):
    try:
        with get_db_connection() as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                sql = """
                    INSERT INTO documentos_unb (conteudo, fonte, embedding, metadados, search_vector)
                    VALUES (%s, %s, %s, %s, setweight(to_tsvector('portuguese', %s), 'A') || setweight(to_tsvector('portuguese', %s), 'B'));
                """
                cur.execute(sql, (conteudo, fonte, embedding, metadados, metadados, conteudo))
            conn.commit()
    except Exception as e:
        logger.error(f"Erro insert_document: {e}", exc_info=True)

def get_db_summary() -> list[tuple]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        REGEXP_REPLACE(fonte, 'https?://([^/]+)/.*', '\\1') AS dominio, 
                        COUNT(*) 
                    FROM documentos_unb 
                    GROUP BY dominio 
                    ORDER BY COUNT(*) DESC;
                """)
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Erro get_db_summary: {e}", exc_info=True)
        return []

def search_hybrid(query_text: str, query_embedding: list[float], limit: int = 5):
    results = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                sql = """
                WITH semantic_search AS (
                    SELECT id, conteudo, fonte, 
                           RANK() OVER (ORDER BY embedding <=> %s) as rank_semantic
                    FROM documentos_unb
                    ORDER BY embedding <=> %s
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
                    COALESCE(s.id, k.id) as id,
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
                
                formatted_results = []
                for row in results:
                    formatted_results.append({
                        "id": row[0],
                        "conteudo": row[1],
                        "fonte": row[2],
                        "score": row[3]
                    })
                return formatted_results
                
    except Exception as e:
        logger.error(f"Erro search_hybrid: {e}", exc_info=True)
        return []