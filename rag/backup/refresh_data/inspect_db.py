import logging
from database import get_db_connection
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Inspector")

def inspect_data():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("\n--- 🔍 INSPEÇÃO DE DADOS (TOP 3) ---\n")
    
    try:
        cur.execute("""
            SELECT 
                id, 
                fonte, 
                metadados, 
                conteudo, 
                search_vector::text 
            FROM documentos_unb 
            ORDER BY id DESC 
            LIMIT 3
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("O banco de dados está vazio.")
            return

        for row in rows:
            doc_id, fonte, metadados, conteudo, search_vec = row
            
            preview = {
                "ID": doc_id,
                "Fonte": fonte,
                "Gemini_Metadados": metadados,
                "Conteudo_Preview": conteudo[:150] + "..." if len(conteudo) > 150 else conteudo,
                "Search_Vector_Sample": search_vec[:100] + "..." if search_vec else "NULL"
            }
            
            print(json.dumps(preview, indent=4, ensure_ascii=False))
            print("-" * 60)

    except Exception as e:
        logger.error(f"Erro ao inspecionar banco: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    inspect_data()