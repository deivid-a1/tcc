#!/bin/bash
set -e

echo "--- 🚀 Iniciando Validador e Provisionador de Ambiente (Ubuntu/Debian) ---"

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"
REQ_FILE="requirements.txt"
VENV_DIR=".venv"

# Funções de log
log_info() { echo "[INFO] $1"; }
log_warn() { echo "[AVISO ⚠️] $1"; }
log_ok() { echo "[OK ✅] $1"; }
log_err() { echo "[ERRO ❌] $1"; exit 1; }
log_act() { echo "[AÇÃO! 🛑] $1"; }

# 1. Verificação do .env
log_info "1. Verificando ficheiro de configuração (.env)..."
if [ ! -f $ENV_FILE ]; then
    log_warn "$ENV_FILE não encontrado."
    if [ ! -f $EXAMPLE_FILE ]; then
        log_err "Template $EXAMPLE_FILE também não foi encontrado. Abortando."
    fi
    cp $EXAMPLE_FILE $ENV_FILE
    echo "--------------------------------------------------------"
    log_act "O ficheiro $ENV_FILE foi criado."
    log_act "Edite-o com as suas credenciais (GEMINI_API_KEY, DB_USER, DB_PASS)."
    log_act "Rode este script (./setup.sh) novamente após editar."
    echo "--------------------------------------------------------"
    exit 1
fi
log_ok "$ENV_FILE encontrado."

# 2. Carregar variáveis de ambiente
log_info "2. Carregando variáveis de ambiente do .env..."
set -o allexport
source $ENV_FILE
set +o allexport
log_ok "Variáveis carregadas."

# 3. Verificação de Python, Pip e Venv
log_info "3. Verificando Python, Pip e Venv..."
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null; then
    log_err "python3 ou pip3 não encontrados. Por favor, instale o Python 3."
fi
if ! dpkg -s python3-venv &> /dev/null; then
    log_warn "Pacote 'python3-venv' (necessário para ambientes virtuais) não encontrado."
    read -p "Deseja instalar 'python3-venv' agora? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        sudo apt-get update
        sudo apt-get install -y python3-venv
    else
        log_err "Instalação do 'python3-venv' negada. Abortando."
    fi
fi
log_ok "Python, Pip e Venv estão disponíveis."

# 4. Criando Ambiente Virtual
log_info "4. Configurando Ambiente Virtual em $VENV_DIR..."
if [ ! -d "$VENV_DIR" ]; then
    log_info "Criando $VENV_DIR..."
    python3 -m venv $VENV_DIR
    log_ok "Ambiente virtual criado."
else
    log_ok "Ambiente virtual já existe."
fi

# --- CORREÇÃO AQUI ---
# 5. Limpeza e Instalação de Dependências Python
log_info "5. Limpando e instalando dependências do venv..."
if [ ! -f $REQ_FILE ]; then
    log_err "$REQ_FILE não encontrado. Abortando."
fi

log_info "Atualizando pip..."
$VENV_DIR/bin/pip install --upgrade pip

log_info "Desinstalando bibliotecas Google conflitantes (se existirem)..."
# Isto limpa o ambiente de qualquer instalação antiga
$VENV_DIR/bin/pip uninstall -y google-generativeai google-genai google-ai-generativelanguage

log_info "Instalando dependências de $REQ_FILE..."
$VENV_DIR/bin/pip install -r $REQ_FILE
log_ok "Dependências Python instaladas no venv."
# --- FIM DA CORREÇÃO ---

# 6. Instalação e Configuração do PostgreSQL + pgvector
log_info "6. Verificando instalação do PostgreSQL..."
if ! command -v psql &> /dev/null; then
    log_warn "PostgreSQL (psql) não encontrado."
    read -p "Deseja instalar o PostgreSQL 16 e o pgvector agora? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_err "Instalação cancelada. O script não pode continuar sem o PostgreSQL."
    fi
    log_info "Instalando PostgreSQL e pgvector via apt..."
    sudo apt-get update
    sudo apt-get install -y postgresql-16 postgresql-contrib-16 postgresql-16-pgvector
    log_info "Iniciando e habilitando o serviço PostgreSQL..."
    sudo systemctl enable --now postgresql
    log_ok "PostgreSQL instalado e iniciado."
else
    log_ok "PostgreSQL (psql) já está instalado."
fi

# 7. Configuração do Banco de Dados (Utilizador, Base e Extensão)
log_info "7. Configurando Utilizador e Base de Dados no PostgreSQL..."
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    log_ok "Utilizador '$DB_USER' já existe."
else
    log_info "Criando utilizador '$DB_USER'..."
    sudo -u postgres createuser $DB_USER
    log_ok "Utilizador '$DB_USER' criado."
fi
log_info "Definindo password para '$DB_USER'..."
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
log_ok "Password definida."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    log_ok "Base de dados '$DB_NAME' já existe."
else
    log_info "Criando base de dados '$DB_NAME'..."
    sudo -u postgres createdb $DB_NAME -O $DB_USER
    log_ok "Base de dados '$DB_NAME' criada e associada ao utilizador '$DB_USER'."
fi
log_info "Habilitando a extensão 'pgvector' na base '$DB_NAME'..."
sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"
log_ok "Extensão 'vector' habilitada."

# 8. Instalação das Dependências de Sistema e Navegadores Playwright
log_info "8. Instalando dependências de sistema do Playwright (requer sudo)..."
sudo $VENV_DIR/bin/python -m playwright install-deps
log_ok "Dependências de sistema do Playwright instaladas."
log_info "Instalando/verificando navegadores do Playwright..."
$VENV_DIR/bin/python -m playwright install
log_ok "Navegadores Playwright (binários) instalados."

# 9. Validação Final da Conexão
log_info "9. Validando conexão final ao banco de dados..."
export PGPASSWORD=$DB_PASS
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q; then
    log_ok "Conexão com PostgreSQL (Host: $DB_HOST, DB: $DB_NAME) bem-sucedida!"
else
    log_err "Falha na validação final da conexão com o PostgreSQL. Verifique o .env e as regras de 'pg_hba.conf'."
fi
unset PGPASSWORD

echo ""
echo "--- Ambiente Pronto! ✨ ---"
echo "Para ativar o ambiente virtual e executar o pipeline, use:"
echo ""
echo "  source $VENV_DIR/bin/activate"
echo "  python main.py"
echo ""