import logging
import os

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_SEARCH_QUERIES

logger = logging.getLogger(__name__)

def get_updated_information() -> list[dict]:
    if not GEMINI_API_KEY:
        logger.critical("GEMINI_API_KEY não definida no .env. Impossível continuar.")
        raise ValueError("GEMINI_API_KEY não definida no .env")
    
    try:
        client = genai.Client()
    except Exception as e:
        logger.critical(f"Falha ao instanciar o genai.Client(): {e}", exc_info=True)
        return []

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    all_results = []
    
    for query in GEMINI_SEARCH_QUERIES:
        try:
            logger.debug(f"Executando busca Gemini para: '{query}'")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Busque resultados recentes para: {query}",
                config=config
            )
            
            if (response.candidates[0].grounding_metadata and 
                response.candidates[0].grounding_metadata.grounding_chunks):
                
                for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                    if chunk.web:
                         all_results.append({
                            "url": chunk.web.uri,
                            "title": chunk.web.title
                        })
            
        except Exception as e:
            logger.error(f"Erro ao buscar por '{query}': {e}", exc_info=True)
            
    unique_results = list({v['url']:v for v in all_results}.values())
    logger.info(f"Busca Gemini concluída. {len(unique_results)} URLs únicas encontradas.")
    
    client.close()
    
    return unique_results


if __name__ == "__main__":
    import logger_setup
    
    logger_setup.setup_logging()
    
    logger.info("--- 🧪 Testando o módulo data_source.py (SDK google-genai) ---")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        results = get_updated_information()
        
        logger.info("--- Resultados da Busca ---")
        if results:
            for i, res in enumerate(results):
                logger.info(f"Resultado {i+1}: {res['title']} ({res['url']})")
        else:
            logger.warning("Nenhum resultado encontrado.")
            
    except Exception as e:
        logger.critical(f"Falha ao executar o teste: {e}", exc_info=True)
        
    logger.info("--- 🧪 Teste do módulo data_source.py concluído ---")