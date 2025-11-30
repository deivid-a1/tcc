import asyncio
import yaml
import logging
import os
from core.tools import ToolRegistry
from core.mcp_client import MCPClientManager
from core.llm_provider import QwenLocalProvider
from core.agent import ReactAgent

async def initialize_system(config_path: str = "config.yaml"):
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    tool_registry = ToolRegistry()
    
    print("\n🌐 Configurando conexões MCP...")
    mcp_manager = MCPClientManager()
    
    for server_config in config.get("mcp_servers", []):
        try:
            await mcp_manager.connect_server(
                name=server_config["name"],
                url=server_config["url"]
            )
            print(f"  • Servidor configurado: {server_config['name']}")
        except Exception as e:
            print(f"  ✗ Erro ao configurar {server_config['name']}: {e}")
    
    print("\n🔌 Iniciando conexões MCP...")
    await mcp_manager.start_all()
    
    print("\n🔍 Descobrindo ferramentas MCP...")
    await mcp_manager.discover_and_register_tools(tool_registry)
    
    print("\n🤖 Inicializando LLM Provider...")
    llm_config = config.get("llm", {})
    
    if llm_config.get("provider") == "qwen_local":
        llm_provider = QwenLocalProvider(model_name=llm_config.get("model"))
        print(f"  ✓ Qwen Local carregado: {llm_config.get('model')}")
    else:
        raise ValueError(f"Provider não suportado: {llm_config.get('provider')}")
    
    print("\n🎯 Criando agente REACT...")
    agent = ReactAgent(llm_provider, tool_registry)
    agent.MAX_ITERATIONS = config.get("agent", {}).get("max_iterations", 10)
    print("  ✓ Agente pronto!")
    
    print(f"\n✅ Sistema inicializado com sucesso!")
    print(f"   Ferramentas disponíveis: {len(tool_registry.tools)}")
    print(f"   Modelo LLM: {llm_provider.get_model_info()['model']}")
    
    return agent, mcp_manager

async def run_interactive_mode(agent: ReactAgent):
    print("\n" + "="*60)
    print("AGENTE REACT UnB - Modo Interativo")
    print("Digite 'sair' para encerrar")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("\n🎓 Você: ").strip()
            
            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("👋 Encerrando...")
                break
            
            if not user_input:
                continue
            
            print("\n🤔 Agente processando...\n")
            response = await agent.run(user_input)
            print(f"🤖 Agente: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

async def main():
    LOG_DIR = "log"
    LOG_FILE = "agent.log"
    LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
    
    os.makedirs(LOG_DIR, exist_ok=True)
    
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(LOG_PATH, mode='w', encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    root_logger.info("Logging configurado. Salvando em: " + LOG_PATH)

    agent = None
    mcp_manager = None
    
    try:
        agent, mcp_manager = await initialize_system()
        await run_interactive_mode(agent)
        
    except Exception as e:
        root_logger.error(f"Erro fatal: {e}", exc_info=True)
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if mcp_manager:
            print("\n🔌 Fechando conexões MCP...")
            await mcp_manager.close_all()
            print("  ✓ Conexões fechadas")

if __name__ == "__main__":
    asyncio.run(main())