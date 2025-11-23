from fastmcp import FastMCP
from pydantic import BaseModel, Field
from src.common.logger import setup_logging
from src.common.database import search_hybrid
from src.ingestor.processor import TextProcessor # Reutiliza para gerar embedding da query
import logging

setup_logging("server")
logger = logging.getLogger(__name__)

# Instancia global do processador para não recarregar modelo a cada request
processor = TextProcessor()

class RAGOutput(BaseModel):
    prompt_original: str
    contexto_recuperado: list[str]
    fontes: list[str]

mcp = FastMCP(name="Servidor_RAG_UnB")

@mcp.tool
def enriquecer_prompt_com_rag_unb(prompt_usuario: str) -> str:
    logger.info(f"Query: {prompt_usuario}")
    
    query_emb = processor.get_embedding(prompt_usuario)
    results = search_hybrid(prompt_usuario, query_emb)
    
    import json
    return json.dumps({
        "prompt_original": prompt_usuario,
        "contexto_recuperado": [r['conteudo'] for r in results],
        "fontes": [r['fonte'] for r in results]
    })

if __name__ == "__main__":
    mcp.run(transport='http', host="0.0.0.0", port=8888)