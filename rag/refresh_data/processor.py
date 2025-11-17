import logging
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import HF_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        logger.info(f"Carregando modelo de embedding: {HF_MODEL_NAME}...")
        try:
            self.model = SentenceTransformer(HF_MODEL_NAME)
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP
            )
            logger.info("Modelo de embedding carregado com sucesso.")
        except Exception as e:
            logger.critical(f"Falha ao carregar modelo SentenceTransformer: {e}", exc_info=True)
            raise

    def create_chunks(self, text: str) -> list[str]:
        return self.text_splitter.split_text(text)

    def get_embedding(self, text: str) -> list[float]:
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Falha ao gerar embedding para texto: {e}", exc_info=True)
            return []