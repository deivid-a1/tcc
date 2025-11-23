import logging
import asyncio
import sys
import textwrap
import os
import json
from logging.handlers import RotatingFileHandler

from fastmcp import Client

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger("RAG_TESTER")
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

log_format_str = '%(asctime)s [%(levelname)s] - %(message)s'
date_format_str = '%Y-%m-%d %H:%M:%S'

log_format = logging.Formatter(log_format_str, date_format_str)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "test_client.log"),
    maxBytes=5*1024*1024,
    backupCount=2
)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

SERVER_URL = "http://127.0.0.1:8888/mcp"
TOOL_NAME = "enriquecer_prompt_com_rag_unb"

TEST_PROMPTS = [
    "Quais os documentos necessários para a matrícula de calouros?",
    "Como funciona o aproveitamento de estudos na UnB?",
    "Onde e como faço a carteirinha estudantil?",
    "Explique o sistema de registro acadêmico",
    "Qual é a capital da França?"
]

async def run_tests():
    logger.info(f"--- 🧪 Iniciando Teste (Assíncrono) do Servidor RAG em {SERVER_URL} ---")
    
    try:
        async with Client(SERVER_URL) as client:
            
            tools = await client.list_tools()
            logger.info(f"Cliente conectado. Ferramentas disponíveis: {[t.name for t in tools]}")

            for i, prompt in enumerate(TEST_PROMPTS):
                logger.info("\n" + "="*80)
                logger.info(f"CASO DE TESTE {i+1}:")
                logger.info(f"ENVIANDO PROMPT: '{prompt}'")
                logger.info("="*80)
                
                try:
                    tool_args = {"prompt_usuario": prompt}
                    result = await client.call_tool(TOOL_NAME, tool_args)

                    try:
                        content_text = result.content[0].text
                        rag_output = json.loads(content_text)
                    except (AttributeError, json.JSONDecodeError, IndexError):
                        logger.warning(f"Resposta bruta não é JSON válido ou estrutura inesperada: {result}")
                        continue

                    logger.info(f"✅ RESPOSTA DO SERVIDOR (RAGOutput):")
                    
                    contextos = rag_output.get("contexto_recuperado", [])
                    fontes = rag_output.get("fontes", [])
                    
                    if contextos:
                        logger.info(f"Encontrados {len(contextos)} chunks de contexto:")
                        
                        for j, (contexto, fonte) in enumerate(zip(contextos, fontes)):
                            logger.info(f"\n  --- Chunk {j+1} (Fonte: {fonte}) ---")
                            wrapped_text = textwrap.fill(f'"{contexto}"', width=78, initial_indent='  ', subsequent_indent='  ')
                            logger.info(wrapped_text)
                    else:
                        logger.warning("⚠️ O servidor não retornou nenhum contexto (RAG 0 resultados).")

                except Exception as e:
                    logger.error(f"\n[ERRO DA FERRAMENTA] O servidor retornou um erro: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"\n[ERRO FATAL] Não foi possível conectar ao servidor em {SERVER_URL}.")
        logger.error(f"Verifique se o 'mcp_server.py' está em execução: {e}")
        sys.exit(1)

    logger.info("\n" + "="*80)
    logger.info("--- 🧪 Teste concluído ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        logger.info("\nTeste interrompido.")