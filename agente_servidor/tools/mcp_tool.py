from core.tools import Tool
from typing import Dict, Any
from fastmcp import Client
import json

class MCPTool(Tool):
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], 
                 mcp_client: Client, mcp_tool_name: str):
        super().__init__(name, description, parameters)
        self.mcp_client = mcp_client
        self.mcp_tool_name = mcp_tool_name
    
    async def execute(self, **kwargs) -> str:
        try:
            result = await self.mcp_client.call_tool(
                self.mcp_tool_name,
                kwargs
            )
            
            if result.is_error:
                error_message = "Erro desconhecido da ferramenta"
                if result.content and hasattr(result.content[0], 'text'):
                    error_message = result.content[0].text
                return f"Erro retornado pela ferramenta MCP: {error_message}"
            
            return json.dumps(result.data, ensure_ascii=False)
            
        except Exception as e:
            return f"Erro ao executar ferramenta MCP: {str(e)}"