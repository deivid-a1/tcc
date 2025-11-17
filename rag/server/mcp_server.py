import logging
import logger_setup
logger_setup.setup_logging()

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from rag_core import search_rag

logger = logging.getLogger(__name__)

class RAGOutput(BaseModel):
    prompt_original: str = Field(description="O prompt original enviado pelo usuário.")
    contexto_recuperado: list[str] = Field(description="Os N pedaços de texto (chunks) mais relevantes encontrados no banco vetorial.")
    fontes: list[str] = Field(description="As URLs ou nomes de arquivos de onde o contexto foi extraído.")

mcp = FastMCP(
    name="Servidor_RAG_UnB",
    instructions="Este servidor enriquece um prompt do usuário com contexto da Universidade de Brasília (UnB) usando RAG."
)

@mcp.tool
def enriquecer_prompt_com_rag_unb(
    prompt_usuario: str = Field(description="O prompt original enviado pelo usuário.")
    ) -> dict:
    """
    Enriquesse o prompt do usuário, para conseguir responder com informações atualizadas.
    """
    # if ctx:
    #     ctx.info(f"Recebido prompt para RAG: {prompt_usuario[:50]}...")

    rag_data = search_rag(prompt_usuario)
    
    # if ctx:
    #     ctx.info(f"Contexto RAG encontrado. {len(rag_data['contexto'])} chunks recuperados.")

    output = RAGOutput(
        prompt_original=prompt_usuario,
        contexto_recuperado=rag_data["contexto"],
        fontes=rag_data["fontes"]
    )
    return output.model_dump()

if __name__ == "__main__":
    logger.info("Iniciando servidor FastMCP RAG...")
    mcp.run(
        transport='http',
        host="0.0.0.0",
        port=8888
    )