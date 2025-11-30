from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastmcp import FastMCP, Context
from fastmcp.server.http import create_sse_app
from contextlib import asynccontextmanager
import asyncio
import json
import uvicorn
from main import initialize_system

agent_instance = None
mcp_manager_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance, mcp_manager_instance
    print("🚀 Inicializando Sistema (Interface Web)...")
    try:
        agent_instance, mcp_manager_instance = await initialize_system("config.yaml")
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
    
    yield
    
    print("🔌 Encerrando conexões MCP...")
    if mcp_manager_instance:
        await mcp_manager_instance.close_all()

app = FastAPI(lifespan=lifespan)

mcp = FastMCP("InterfaceWeb")

@mcp.tool
async def interagir_com_agente(prompt: str, ctx: Context) -> str:
    global agent_instance
    
    if not agent_instance:
        return "Erro: Agente não inicializado."

    async def on_step(step_data: dict):
        try:
            await ctx.info(json.dumps(step_data))
        except Exception as e:
            print(f"Erro ao enviar log MCP: {e}")

    try:
        response = await agent_instance.run(prompt, step_callback=on_step)
        return response
    except Exception as e:
        return f"Erro fatal no agente: {str(e)}"

sse_mcp_app = create_sse_app(
    mcp,
    sse_path="/sse",
    message_path="/messages"
)

app.mount("/mcp", sse_mcp_app)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    print("🌐 Servidor Web rodando em http://localhost:8000")
    print("   -> Frontend: http://localhost:8000/")
    print("   -> MCP SSE:  http://localhost:8000/mcp/sse")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)