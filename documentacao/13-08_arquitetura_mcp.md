# MCP Agent - Plano de Arquitetura Melhorado

## Objetivo
Criar um agente inteligente que utiliza o Model Context Protocol (MCP) para conectar LLMs a ferramentas internas e externas, com sistema de logging detalhado por requisição, autenticação simples e execução sequencial.

## Estrutura de Pastas Atualizada

```
mcp-agent/
├── main.py                      # Entry point - orquestra inicialização
├── config.yaml                 # Configuração centralizada
│
├── core/                        # Núcleo do sistema
│   ├── interfaces/              # Contratos abstratos
│   │   ├── llm_interface.py     # Define como LLMs devem se comportar
│   │   ├── tool_interface.py    # Define como Tools devem se comportar
│   │   ├── mcp_interface.py     # Define comunicação MCP padrão
│   │   └── logger_interface.py  # Define interface de logging
│   │
│   ├── agent.py                 # Orquestrador principal - decisões
│   ├── function_registry.py     # Descoberta automática de tools
│   ├── function_executor.py     # Execução segura de function calls
│   └── lifecycle_manager.py     # Gerencia ciclo de vida de requisições
│

├── logging/                     # Sistema de logging detalhado
│   ├── request_logger.py        # Logger específico por requisição
│   ├── log_formatter.py         # Formatação padronizada de logs
│   ├── log_storage.py           # Persistência de logs
│   ├── log_aggregator.py        # Agregação e correlação de logs
│   └── models/                  # Estruturas de dados de log
│       ├── request_log.py       # Modelo de log de requisição
│       ├── execution_log.py     # Modelo de log de execução
│       └── performance_log.py   # Modelo de log de performance
│
├── llm/                         # Camada de abstração LLM
│   ├── factory.py               # Criação dinâmica de LLMs
│   ├── models/                  # Implementações específicas
│   │   ├── qwen.py              # Qwen3-14B + function calling
│   │   └── base_model.py        # Implementação base comum
│   └── function_schema.py       # Geração de schemas OpenAI
│
├── mcp/                         # Protocolo de comunicação
│   ├── server.py                # Interface com usuário
│   ├── client_manager.py        # Gerencia conexões com tools
│   └── protocol_handler.py      # Implementação MCP completa
│
├── queue/                       # Sistema de filas
│   ├── request_queue.py         # Implementação da fila FIFO
│   ├── queue_manager.py         # Gerenciamento de estado da fila
│   ├── execution_scheduler.py   # Agendador de execução
│   └── queue_monitor.py         # Monitoramento da fila
│
├── tools/                       # Ecossistema de ferramentas
│   ├── base_tool.py             # Classe abstrata para todas tools
│   ├── tool_factory.py          # Criação dinâmica de tools
│   │
│   ├── internal/                # Processamento local
│   │   └── calculator_tool.py   # Exemplo: operações matemáticas
│   │
│   ├── external/                # APIs e serviços externos
│   │   └── weather_tool.py      # Exemplo: dados meteorológicos
│   │
│   └── schemas/                 # Definições de função
│       └── function_schemas.json
│
├── storage/                     # Persistência de dados
│   └── logs/                    # Armazenamento de logs por data
│       └── YYYY-MM-DD/          # Estrutura por data
│           ├── requests/        # Logs de requisição
│           ├── executions/      # Logs de execução
│           └── performance/     # Logs de performance
│
└── templates/                   # Templates para extensão
    ├── internal_tool_template.py
    ├── external_tool_template.py
    └── README_TOOLS.md
```

## Funcionalidades Arquiteturais Principais

### 1. Sistema de Logging Detalhado por Requisição

#### **Rastreamento Completo do Ciclo de Vida**
- **Log Único por Prompt**: Cada requisição gera um UUID único que acompanha toda a execução
- **Timestamps Precisos**: Cada etapa registra timestamp de início/fim com precisão de milissegundos
- **Fluxo de Execução Completo**: Log sequencial de todas as etapas (recepção → fila → processamento → resposta)
- **Métricas de Performance**: Tempo de CPU, memória utilizada, latência de LLM, tempo de função
- **Contexto Detalhado**: Parâmetros de entrada, resultados intermediários, decisões do agente

#### **Estrutura de Dados de Log**
- **Request Log**: Informações gerais da requisição (ID, timestamps, status)
- **Execution Log**: Detalhamento passo-a-passo da execução
- **Performance Log**: Métricas de desempenho e recursos utilizados
- **Error/Warning Log**: Erros e avisos com contexto completo

- **Armazenamento Inteligente**
- **Organização por Data**: Logs organizados em estrutura hierárquica por data
- **Compressão Automática**: Logs antigos comprimidos para economizar espaço
- **Retenção Configurável**: Limpeza automática baseada em política de retenção

### 2. Sistema de Fila Sequencial (FIFO)

#### **Execução Única e Sequencial**
- **Fila FIFO Rígida**: Apenas uma requisição processada por vez
- **Bloqueio de Concorrência**: Sistema bloqueia novas execuções até conclusão da atual
- **Posição na Fila**: Cada requisição recebe informação sobre sua posição
- **Tempo de Espera**: Estimativa de tempo de espera baseada em histórico

#### **Gerenciamento de Estado**
- **Monitoramento em Tempo Real**: Métricas da fila (tamanho, tempo médio, throughput)
- **Cancelamento**: Capacidade de cancelar requisições na fila
- **Timeout de Requisições**: Requisições muito longas são automaticamente canceladas

## Fluxo de Dados Atualizado com Logging e Fila

```
1. User Request
   ↓
2. queue/request_queue.py (Enqueue + Position Info)
   ↓ (Wait in FIFO Queue)
3. queue/execution_scheduler.py (Dequeue When Ready)
   ↓ (Start RequestLogger)
4. mcp/server.py (MCP Protocol Processing)
   ↓ (Log: mcp_receive_step)
5. core/agent.py (Orchestration + Decision Making)
   ↓ (Log: agent_orchestration_step)
6. llm/factory.py → llm/models/qwen.py (LLM Processing)
   ↓ (Log: llm_processing_step with tokens/timing)
7. core/function_registry.py (Function Discovery)
   ↓ (Log: function_discovery_step)
8. core/function_executor.py (Function Execution)
   ↓ (Log: function_execution_step with results)
9. mcp/client_manager.py (Response Preparation)
   ↓ (Log: response_preparation_step)
10. mcp/server.py (Final Response to User)
    ↓ (Log: response_delivery_step)
11. logging/request_logger.py (Finalize Complete Log)
    ↓
12. logging/log_storage.py (Store Complete Request Log)
```

## Decisões Arquiteturais Justificadas

### **Por que Logging por Requisição?**
- **Debugging Eficiente**: Cada problema pode ser rastreado completamente
- **Auditoria Completa**: Histórico completo de decisões e execuções
- **Análise de Performance**: Identificação de gargalos por etapa
- **Compliance**: Rastreabilidade completa para auditorias

### **Por que Fila Sequencial?**
- **Controle de Recursos**: Evita sobrecarga do LLM e ferramentas
- **Previsibilidade**: Comportamento determinístico do sistema
- **Debugging Simplificado**: Sem problemas de concorrência
- **Qualidade de Resposta**: LLM dedicado por requisição

### **Por que MCP Mantido?**
- **Padrão da Indústria**: Interoperabilidade com outros sistemas
- **Extensibilidade**: Adição fácil de novas ferramentas
- **Protocolo Robusto**: Tratamento de erros e versionamento
- **Ecosystem Ready**: Compatibilidade com ferramentas MCP existentes

## Configuração Centralizada Estendida

```yaml
# config.yaml
system:
  environment: "production"
  debug_mode: false
  max_concurrent_requests: 1  # Força sequencial

queue:
  max_queue_size: 100
  request_timeout_minutes: 30

logging:
  level: "INFO"
  retention_days: 30
  storage_path: "./storage/logs"
  compress_after_days: 7
  performance_metrics: true
  
llm:
  model: "qwen3-14b"
  max_tokens: 4096
  temperature: 0.7
  timeout_seconds: 180

mcp:
  server_port: 8080
  client_pool_size: 10
  protocol_version: "1.0"

tools:
  auto_discovery: true
  load_internal: true
  load_external: true
```

## Benefícios da Arquitetura Melhorada

### **Operacionais**
- **Observabilidade Total**: Visibilidade completa do sistema
- **Debug Eficiente**: Logs detalhados facilitam resolução de problemas
- **Performance Tracking**: Métricas precisas de cada componente
- **Simplicidade de Acesso**: Sistema aberto sem barreiras de autenticação

### **Técnicos**
- **Arquitetura Limpa**: Separação clara de responsabilidades
- **Extensibilidade**: Fácil adição de novas funcionalidades
- **Simplicidade**: Sistema focado em funcionalidades essenciais
- **Manutenibilidade**: Código organizados e bem documentado

### **Negócio**
- **Controle de Custos**: Visibilidade de uso de recursos
- **Qualidade Garantida**: Execução sequencial garante qualidade
- **Acesso Livre**: Sem complexidade de gerenciamento de usuários
- **Escalabilidade Planejada**: Base sólida para crescimento futuro