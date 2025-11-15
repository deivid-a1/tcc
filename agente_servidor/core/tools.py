from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json

class Tool(ABC):
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass
    
    def to_llm_format(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Tool:
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def get_tools_description(self) -> str:
        descriptions = []
        for tool in self.tools.values():
            desc = f"""
Ferramenta: {tool.name}
Descrição: {tool.description}
Parâmetros (JSON Schema): {json.dumps(tool.parameters, indent=2)}
"""
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_llm_format() for tool in self.tools.values()]