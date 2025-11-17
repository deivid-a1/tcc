import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (ex: GEMINI_API_KEY, DB_PASS)
# do ficheiro .env para o ambiente de execução.
load_dotenv()

# --- Configurações da API e do Banco de Dados ---

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

DB_SETTINGS = {
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASS", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "unb_rag_db")
}

# --- Configurações do Pipeline de RAG ---

# Modelo do Hugging Face para criar os embeddings (vetores).
HF_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
VECTOR_DIMENSION = 768 # A dimensão DEVE corresponder ao modelo acima.

# Configuração do "Chunking" (como os documentos são divididos).
CHUNK_SIZE = 1000 # Tamanho de cada pedaço de texto (em caracteres).
CHUNK_OVERLAP = 200 # Sobreposição entre pedaços para não perder o contexto.
LOCAL_DOCS_PATH = "documentos_locais"

# --------------------------------------------------------------------------
# --- 🎯 Configuração das Queries de Busca do Agente Gemini ---
# --------------------------------------------------------------------------
#
# Este é o "cérebro" do seu agente de coleta. A qualidade das suas
# buscas aqui define a qualidade do seu RAG.
#
# ### GUIA DE SINTAXE ###
#
# 1.  **Sintaxe Python (Aspas Simples):**
#     Use aspas simples ( '...' ) para definir a string inteira.
#     Isso permite usar aspas duplas ( "..." ) dentro dela, o que é
#     crucial para a sintaxe do Google.
#
# 2.  **Sintaxe Google (Aspas Duplas):**
#     Use "frase exata" para forçar o Google a procurar por termos
#     compostos.
#     - RUIM:   'vestibular UnB' (pode encontrar páginas sobre "vestibular"
#               e outras sobre "UnB")
#     - BOM:    '"vestibular UnB"' (procura a frase exata)
#
# 3.  **Operador OR (Sempre em Maiúsculas):**
#     Use OR para combinar termos.
#     - BOM: '"bolsas de estudo" OR "bolsas acadêmicas"'
#
# 4.  **Desambiguação (Evitando "Lixo"):**
#     Termos curtos como "bolsas" ou "PAS" são ambíguos. O Google pode
#     retornar "bolsas de moda" ou "PAS (passo)".
#     Sempre adicione um termo de contexto:
#     - RUIM:   'bolsas 2025'
#     - BOM:    '"bolsas de estudo" "UnB" 2025'
#
# 5.  **Restrição de Site (site:):**
#     Use `site:dominio.com` para restringir a busca a um portal específico.
#     - BOM: 'edital site:atosoficiais.unb.br'
#
# --------------------------------------------------------------------------

GEMINI_SEARCH_QUERIES = [
    # 1. Buscas de Notícias (Oficiais e Imprensa)
    'notícias site:noticias.unb.br',
    # 'novidades "Universidade de Brasília" 2025 site:g1.globo.com/df',
    'reportagens "UnB" 2025 site:correiobraziliense.com.br/euestudante',

    # 2. Buscas de Atos Oficiais (Editais, Resoluções)
    'edital 2025 site:unb.br',
    'resolução 2025 site:unb.br',

    # 3. Buscas Específicas
    'calendário acadêmico 2025 site:deg.unb.br',
    '"bolsas de estudo" OR "bolsas acadêmicas" 2025 site:dpg.unb.br',
    
    # 4. Buscas Abertas (mas com contexto obrigatório)
    'matrícula "UnB" 2025',
    'vestibular "Universidade de Brasília" 2025',
    '"PAS UnB" 2025'
]