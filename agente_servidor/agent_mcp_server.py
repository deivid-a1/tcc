from fastmcp import FastMCP
import asyncio
from main import initialize_system

agent_instance = None
mcp_manager_instance = None

mcp = FastMCP("agent-unb")

@mcp.tool
async def processar_prompt(prompt: str) -> str:
    """
    Processa um prompt do usuário usando o agente REACT da UnB. 
    O agente pode responder perguntas, fazer cálculos, consultar horários e mais.
    """
    global agent_instance
    
    if agent_instance is None:
        return "Erro: Agente não foi inicializado corretamente"
    
    if not prompt:
        return "Erro: Prompt vazio"
    
    try:
        response = await agent_instance.run(prompt)
        return response
    
    except Exception as e:
        return f"Erro ao processar prompt: {str(e)}"

async def setup_agent():
    global agent_instance, mcp_manager_instance
    
    print("🚀 Inicializando Agente UnB para servidor MCP...")
    agent_instance, mcp_manager_instance = await initialize_system()
    print("✅ Agente inicializado!\n")

def main():
    global mcp_manager_instance
    
    try:
        asyncio.run(setup_agent())
    
    except Exception as e:
        print(f"❌ Erro fatal durante a inicialização do agente: {e}")
        return

    try:
        print("🚀 Servidor MCP do Agente rodando em http://127.0.0.1:8889")
        mcp.run(
            transport='http',
            host="0.0.0.0",
            port=8889
        )
            
    except KeyboardInterrupt:
        print("\n👋 Encerrando servidor do agente...")
    finally:
        if mcp_manager_instance:
            print("\n🔌 Fechando conexões MCP do agente...")
            try:
                asyncio.run(mcp_manager_instance.close_all())
            except RuntimeError as e:
                print(f"Aviso ao fechar conexões: {e}")
            print("  ✓ Conexões fechadas")

if __name__ == "__main__":
    main()