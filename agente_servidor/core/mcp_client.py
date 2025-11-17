from fastmcp import Client
from typing import Dict, List
from core.tools import ToolRegistry
from tools.mcp_tool import MCPTool
import json

class MCPClientManager:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.servers: Dict[str, str] = {}
        self.started_clients: Dict[str, Client] = {}
    
    async def connect_server(self, name: str, url: str) -> Client:
        client = Client(url)
        self.clients[name] = client
        self.servers[name] = url
        return client

    async def start_all(self):
        for server_name, client in self.clients.items():
            try:
                await client.__aenter__()
                await client.ping()
                print(f"  ✓ Conexão MCP iniciada: {server_name}")
                self.started_clients[server_name] = client
            except Exception as e:
                print(f"  ✗ Erro ao iniciar {server_name}: {e}")
        
        self.clients = self.started_clients

    async def discover_and_register_tools(self, tool_registry: ToolRegistry) -> None:
        for server_name, client in self.clients.items():
            try:
                tools_response = await client.list_tools()
                
                for tool_info in tools_response:
                    mcp_tool = MCPTool(
                        name=tool_info.name,
                        description=tool_info.description or "Sem descrição",
                        parameters=tool_info.inputSchema,
                        mcp_client=client,
                        mcp_tool_name=tool_info.name
                    )
                    tool_registry.register(mcp_tool)
                    print(f"✓ Ferramenta MCP registrada: {tool_info.name} (servidor: {server_name})")
                    
            except Exception as e:
                print(f"✗ Erro ao descobrir ferramentas do servidor {server_name}: {e}")
    
    async def close_all(self):
        for client in self.clients.values():
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass