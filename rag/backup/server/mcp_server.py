import logging
import logger_setup
logger_setup.setup_logging()

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from rag_core import search_rag

logger = logging.getLogger(__name__)

class RAGOutput(BaseModel):
    prompt_original: str = Field(description="O prompt original enviado pelo usuário.")
    contexto_recuperado: list[str] = Field(description="Os chunks de texto mais relevantes encontrados.")
    fontes: list[str] = Field(description="As fontes (URLs/Arquivos) do contexto.")

mcp = FastMCP(
    name="Servidor_RAG_UnB",
    instructions="Servidor de Busca Híbrida (Semântica + Keywords) para documentos da UnB."
)

@mcp.tool
def enriquecer_prompt_com_rag_unb(
    prompt_usuario: str = Field(description="O prompt do usuário para busca de contexto.")
    ) -> dict:
    
    logger.info(f"Recebendo query: {prompt_usuario}")
    
    rag_data = search_rag(prompt_usuario)
    
    count = len(rag_data.get("contexto", []))
    logger.info(f"Busca Híbrida retornou {count} resultados.")

    output = RAGOutput(
        prompt_original=prompt_usuario,
        contexto_recuperado=rag_data["contexto"],
        fontes=rag_data["fontes"]
    )
    return output.model_dump()

if __name__ == "__main__":
    logger.info("Iniciando servidor FastMCP (Híbrido)...")
    mcp.run(transport='http', host="0.0.0.0", port=8888)