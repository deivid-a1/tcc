# MCP Agent - Plano de Arquitetura

## Objetivo
Criar um agente inteligente que utiliza o Model Context Protocol (MCP) para conectar LLMs a ferramentas internas e externas, permitindo function calling padronizado e extensível.

## Estrutura de Pastas

```
mcp-agent/
├── main.py                      # Entry point - orquestra inicialização
├── config.yaml                 # Configuração centralizada
│
├── core/                        # Núcleo do sistema
│   ├── interfaces/              # Contratos abstratos
│   │   ├── llm_interface.py     # Define como LLMs devem se comportar
│   │   ├── tool_interface.py    # Define como Tools devem se comportar
│   │   └── mcp_interface.py     # Define comunicação MCP padrão
│   │
│   ├── agent.py                 # Orquestrador principal - decisões
│   ├── function_registry.py     # Descoberta automática de tools
│   └── function_executor.py     # Execução segura de function calls
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
└── templates/                   # Templates para extensão
    ├── internal_tool_template.py
    ├── external_tool_template.py
    └── README_TOOLS.md
```

## Pontos Fundamentais da Arquitetura

### 1. Separação de Responsabilidades (core/)
**Raciocínio**: Cada componente tem uma responsabilidade única e bem definida.
- `interfaces/`: Contratos que garantem intercambiabilidade
- `agent.py`: Orquestração e tomada de decisão
- `function_registry.py`: Auto-descoberta sem acoplamento
- `function_executor.py`: Execução isolada e segura

**Benefício**: Mudanças em um componente não quebram outros. Testabilidade máxima.

### 2. Abstração de LLM (llm/)
**Raciocínio**: LLMs evoluem rapidamente, precisamos de flexibilidade.
- `factory.py`: Criação baseada em configuração, não código
- `models/`: Implementações específicas isoladas
- `function_schema.py`: Tradução para formato OpenAI function calling

**Benefício**: Trocar Qwen por Claude/GPT apenas mudando `config.yaml`.

### 3. MCP como Protocolo Universal (mcp/)
**Raciocínio**: MCP padroniza comunicação entre componentes heterogêneos.
- `server.py`: Interface padronizada com usuário
- `client_manager.py`: Pool de conexões com tools externas  
- `protocol_handler.py`: Implementação completa do MCP spec

**Benefício**: Interoperabilidade total, debugging facilitado, extensibilidade.

### 4. Ecossistema de Tools (tools/)
**Raciocínio**: Separação clara entre processamento local vs. externo.
- `internal/`: Zero latência de rede, controle total
- `external/`: Acesso a dados/serviços do mundo real
- `base_tool.py`: Interface uniforme para ambos tipos

**Benefício**: Otimizações específicas, clareza de arquitetura.

### 5. Templates para Extensibilidade (templates/)
**Raciocínio**: Facilitar criação de novas tools sem quebrar padrões.
- Templates documentados com exemplos
- Estrutura consistente para manutenção
- README com guidelines

**Benefício**: Onboarding rápido, qualidade consistente.

## Nuances do MCP Consideradas

### Server vs Client
- **MCP Server**: Recebe prompts do usuário via protocolo padronizado
- **MCP Client**: Conecta-se a ferramentas externas via MCP
- **Benefício**: Agente pode ser cliente e servidor simultaneamente

### Resource Management
- Tools registram recursos (functions) via MCP
- Schema automático das functions disponíveis
- Versionamento de tools via MCP metadata

### Error Handling
- Erros propagados via protocolo MCP
- Fallback para tools indisponíveis
- Timeout e retry automáticos

### Streaming Support
- Respostas longas via streaming MCP
- Progress feedback para operações lentas
- Cancelamento de operações via protocolo

## Fluxo de Dados na Arquitetura

```
User Input
    ↓
mcp/server.py (MCP Protocol)
    ↓
core/agent.py (Orchestration)
    ↓
llm/factory.py → llm/models/qwen.py (LLM Processing)
    ↓
core/function_registry.py (Available Functions)
    ↓
core/function_executor.py (Execute Calls)
    ↓
tools/internal/calculator_tool.py OR tools/external/weather_tool.py
    ↓
mcp/client_manager.py (Response Handling)
    ↓
mcp/server.py (Response to User)
```

### Justificativa do Fluxo

1. **MCP Entry Point**: Padronização desde a entrada
2. **Agent Orchestration**: Decisões centralizadas e auditáveis  
3. **LLM Factory**: Flexibilidade de modelo transparente
4. **Registry Discovery**: Auto-descoberta sem hardcoding
5. **Executor Isolation**: Execução segura e monitorável
6. **Tool Separation**: Otimizações específicas para cada tipo
7. **MCP Exit**: Consistência na resposta

## Raciocínio por Camada

### Core Layer (Núcleo)
**Por que interfaces?** Permitem mock para testes, troca de implementação sem refactor.
**Por que agent.py separado?** Lógica de negócio centralizada, fácil de auditar.
**Por que registry automático?** Reduz erro humano, facilita CI/CD.

### LLM Layer (Abstração)
**Por que factory?** Configuração > código. Deploy sem rebuild.
**Por que base_model.py?** Código comum reutilizado, menos bugs.
**Por que function_schema.py?** Tradução automática entre formatos.

### MCP Layer (Protocolo)
**Por que server + client?** Agente pode servir e consumir MCP simultaneamente.
**Por que client_manager?** Pool de conexões, retry automático, monitoring.
**Por que protocol_handler específico?** Compliance com spec MCP.

### Tools Layer (Ferramentas)
**Por que separar internal/external?** Diferentes padrões de erro, latência, auth.
**Por que base_tool.py?** Interface uniforme facilita registry e executor.
**Por que schemas JSON?** Validação automática, documentação auto-gerada.

## Decisões Arquiteturais Baseadas na Estrutura

### 1. Por que `core/` centralizado?
- **Evita dependências circulares**: LLM não conhece Tools diretamente
- **Single source of truth**: Agent orquestra tudo
- **Facilita debugging**: Logs centralizados em um local

### 2. Por que `llm/models/` separado?
- **Hotswap de modelos**: Deploy sem downtime
- **A/B testing**: Múltiplos modelos simultaneamente  
- **Vendor independence**: Lock-in mitigado

### 3. Por que `mcp/` como camada?
- **Protocol compliance**: Spec MCP seguida rigorosamente
- **Interoperability**: Outros agentes podem se conectar
- **Monitoring**: Logs de protocolo para debugging

### 4. Por que `tools/internal/` vs `tools/external/`?
- **Performance**: Internal = zero network, External = async + retry
- **Security**: Internal = trusted, External = sandboxed
- **Scaling**: Internal = CPU bound, External = I/O bound

### 5. Por que `templates/`?
- **Consistency**: Novos desenvolvedores seguem padrão
- **Quality gates**: Templates têm testes, validação
- **Documentation**: README explica design decisions

## Implementação Faseada

### Fase 1: Core
- Interfaces básicas
- Factory LLM simples
- MCP server/client básico

### Fase 2: Function Calling
- Registry de tools
- Function executor
- 2 tools de exemplo

### Fase 3: Otimização
- Error handling robusto
- Streaming support
- Performance tuning

### Fase 4: Extensões
- Templates avançados
- Monitoring/metrics
- Plugin ecosystem

## Riscos Mitigados

### Vendor Lock-in
- Interface abstrata para LLMs
- MCP como protocolo aberto
- Tools model-agnostic

### Complexidade
- Arquitetura modular
- Documentação clara
- Exemplos práticos

### Performance
- Async/await throughout
- Connection pooling MCP
- Caching de function schemas

## Conclusão

A arquitetura MCP-first garante padronização, extensibilidade e interoperabilidade, enquanto mantém flexibilidade para diferentes LLMs e ferramentas. O uso de interfaces e factory patterns permite evolução sem breaking changes, essencial para um sistema de IA em produção.