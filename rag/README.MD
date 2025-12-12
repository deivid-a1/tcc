# UnB RAG - Sistema de Recuperação Híbrida (MCP + Crawler)

Este repositório contém uma implementação avançada de RAG (Retrieval-Augmented Generation) projetada para documentos acadêmicos e administrativos da Universidade de Brasília (UnB).

O sistema utiliza uma arquitetura de **Busca Híbrida (Hybrid Search)** combinando busca semântica (Embeddings) e busca lexical (BM25/TF-IDF) via PostgreSQL, orquestrada por um servidor **MCP (Model Context Protocol)**.

-----

## 🚀 Funcionalidades Principais

  * **Busca Híbrida com RRF:** Utiliza *Reciprocal Rank Fusion* para combinar a precisão de palavras-chave exatas (`tsvector`) com a compreensão de contexto (`vector cosine similarity`).
  * **Enriquecimento Inteligente (Gemini 2.5):** Antes de indexar, cada fragmento de texto é analisado pelo Google Gemini para gerar metadados e palavras-chave contextuais, melhorando a recuperabilidade.
  * **Crawler Focado:** Sistema automatizado que varre URLs semente (ex: páginas de matrícula) e extrai conteúdo recursivamente.
  * **Ingestão de Múltiplos Formatos:** Suporte nativo para **PDFs** locais e páginas **Web** (incluindo renderização dinâmica via Playwright).
  * **Arquitetura MCP:** O servidor expõe ferramentas padronizadas para conexão direta com Agentes de IA (Claude Desktop, IDEs com suporte a MCP, etc).

-----

## 🛠️ Pré-requisitos (Ubuntu 22.04)

### 1\. Sistema e Dependências

Certifique-se de ter o Python 3.10+ e bibliotecas de construção instaladas:

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv build-essential libpq-dev
```

### 2\. Banco de Dados (PostgreSQL + pgvector)

O projeto requer o PostgreSQL com a extensão `pgvector`. A forma mais recomendada de rodar é via Docker para garantir compatibilidade das versões:

```bash
# Se não tiver docker instalado:
# sudo apt install docker.io

# Subir container do Postgres com pgvector
sudo docker run -d \
  --name unb_rag_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=unb_rag_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

-----

## 📦 Instalação

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/unb-rag.git
    cd unb-rag
    ```

2.  **Crie e ative o ambiente virtual:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Instale os navegadores do Playwright (Necessário para o Crawler):**

    ```bash
    playwright install chromium
    ```

-----

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto com base no exemplo abaixo:

```ini
# .env

# Chave API do Google (Necessária para o enriquecimento de dados na ingestão)
GEMINI_API_KEY="sua_chave_api_do_google_ai_studio"

# Configurações do Banco de Dados
DB_USER="postgres"
DB_PASS="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="unb_rag_db"

# Logs
LOG_LEVEL="INFO"
```

> **Nota:** Se estiver usando Docker, as credenciais acima já funcionam por padrão.

-----

## 🖥️ Uso: Pipeline de Ingestão (Escrita)

O módulo de ingestão é responsável por ler PDFs locais e URLs, enriquecer o conteúdo via Gemini e salvar no banco com vetores híbridos.

### Adicionar Arquivos Locais

Coloque seus arquivos `.pdf`, `.txt` ou `.md` na pasta:
`unb_rag/documentos_locais/`

### Rodar a Ingestão

Para iniciar o crawler e processar arquivos locais:

```bash
# Executar como módulo a partir da raiz
python3 -m src.ingestor.main
```

**Opções:**

  * `--substitute`: **CUIDADO**. Limpa todo o banco de dados (DROP TABLE) antes de iniciar a ingestão. Use para reiniciar o ambiente.
    ```bash
    python3 -m src.ingestor.main --substitute
    ```

-----

## 🌐 Uso: Servidor MCP (Leitura)

O servidor disponibiliza a ferramenta `enriquecer_prompt_com_rag_unb` via protocolo HTTP/MCP.

### Iniciar o Servidor

```bash
python3 -m src.server.main
```

*O servidor iniciará em `http://0.0.0.0:8888`.*

### Testar a Recuperação

Em outro terminal, execute o cliente de teste para verificar se a busca híbrida está retornando contextos relevantes:

```bash
python3 src/server/test_client.py
```

-----

## 🧩 Arquitetura do Projeto

O projeto segue uma estrutura de Monorepo modular:

```text
unb_rag/
├── src/
│   ├── common/      # Configurações e Conexão DB (Singleton)
│   ├── ingestor/    # ETL: Crawler -> Gemini -> Vector DB
│   └── server/      # API: MCP -> Hybrid Search -> JSON
├── documentos_locais/
├── requirements.txt
└── .env
```

### Fluxo de Dados (Hybrid Search)

1.  **Usuário** envia query: *"Qual o prazo para matrícula?"*
2.  **Embeddings:** O sistema converte a pergunta em vetor (SentenceTransformer).
3.  **Busca Vetorial:** Encontra documentos semanticamente próximos.
4.  **Busca Textual (`tsvector`):** Encontra documentos com palavras-chave exatas ("prazo", "matrícula").
5.  **RRF (Reciprocal Rank Fusion):** Um algoritmo de rankeamento combina as duas listas, priorizando documentos que aparecem em ambas.
6.  **Retorno:** O servidor entrega os top-K chunks mais relevantes.

-----

## 🐛 Solução de Problemas Comuns

**Erro: `operator does not exist: vector <=> numeric[]`**

  * **Causa:** O banco não está convertendo a lista Python para vetor SQL.
  * **Solução:** O código já implementa o cast `::vector`, mas certifique-se de que a extensão foi ativada (`register_vector(conn)` no código Python cuida disso).

**Erro: `playwright._impl._api_types.Error: Executable doesn't exist`**

  * **Solução:** Você esqueceu de rodar `playwright install chromium`.

**Gemini API Error (400/403)**

  * **Causa:** Chave de API inválida ou cota excedida.
  * **Solução:** Verifique a `GEMINI_API_KEY` no `.env`. O ingestor falhará silenciosamente no enriquecimento (logs warning), mas continuará a ingestão básica.
