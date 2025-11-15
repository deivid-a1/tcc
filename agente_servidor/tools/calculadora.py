from core.tools import Tool
import math
import re

class CalculadoraTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculadora",
            description="Realiza cálculos matemáticos. Suporta operações básicas (+, -, *, /, **) e funções matemáticas.",
            parameters={
                "type": "object",
                "properties": {
                    "expressao": {
                        "type": "string",
                        "description": "Expressão matemática para calcular. Ex: '2 + 2', '10 * 5', 'sqrt(16)'"
                    }
                },
                "required": ["expressao"]
            }
        )
    
    async def execute(self, expressao: str) -> str:
        if not re.match(r'^[0-9+\-*/().\s sqrt,pow,log,sin,cos,tan]+$', expressao):
            return "Erro: Expressão contém caracteres não permitidos"
        
        try:
            safe_dict = {
                "sqrt": math.sqrt,
                "pow": math.pow,
                "log": math.log,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan
            }
            result = eval(expressao, {"__builtins__": {}}, safe_dict)
            return f"Resultado: {result}"
        except Exception as e:
            return f"Erro ao calcular: {str(e)}"