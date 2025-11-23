import logging
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
from config import HF_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, GEMINI_API_KEY

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        try:
            self.model = SentenceTransformer(HF_MODEL_NAME)
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP
            )
            # Inicializa o cliente com a API Key
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            logger.critical(f"Erro init TextProcessor: {e}", exc_info=True)
            raise

    def create_chunks(self, text: str) -> list[str]:
        return self.text_splitter.split_text(text)

    def get_embedding(self, text: str) -> list[float]:
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Erro get_embedding: {e}")
            return []

    def enrich_text(self, text: str) -> str:
        if not text or len(text) < 50:
            return ""

        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Gere apenas 5 a 10 palavras-chave separadas por espaço que descrevam o contexto técnico, datas e entidades deste texto para fins de busca: {text[:2000]}"
            )
            
            if response.text:
                return response.text.strip()
            return ""
            
        except Exception as e:
            logger.warning(f"Falha no enriquecimento Gemini: {e}")
            return ""