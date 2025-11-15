from fastmcp import FastMCP
import asyncio

HORARIOS_MOCK = {
    "CIC0004": {
        "codigo": "CIC0004",
        "nome": "Algoritmos e Programação de Computadores",
        "horario": "Terça e Quinta, 10:00-12:00",
        "professor": "Prof. João Silva",
        "sala": "LINF - Lab 3"
    },
    "MAT0025": {
        "codigo": "MAT0025",
        "nome": "Cálculo 1",
        "horario": "Segunda e Quarta, 14:00-16:00",
        "professor": "Prof. Maria Santos",
        "sala": "PAT - AT-042"
    },
    "FIS0001": {
        "codigo": "FIS0001",
        "nome": "Física 1",
        "horario": "Terça e Quinta, 16:00-18:00",
        "professor": "Prof. Carlos Lima",
        "sala": "PAT - AT-118"
    }
}

mcp = FastMCP("horarios-unb")

@mcp.tool
def consultar_horario(codigo: str) -> dict:
    """
    Consulta o horário de uma disciplina pelo código.
    Ex: 'CIC0004', 'MAT0025'
    """
    codigo = codigo.upper()
    if codigo in HORARIOS_MOCK:
        return HORARIOS_MOCK[codigo]
    else:
        return {"erro": f"Disciplina {codigo} não encontrada."}

@mcp.tool
def listar_disciplinas() -> dict:
    """Lista todas as disciplinas disponíveis com seus códigos."""
    lista = []
    for codigo, info in HORARIOS_MOCK.items():
        lista.append(f"• {codigo} - {info['nome']}")
    
    resultado = "Disciplinas disponíveis:\n" + "\n".join(lista)
    return {"disciplinas": resultado}

if __name__ == "__main__":
    print("🚀 Servidor MCP de Horários rodando em http://127.0.0.1:8888")
    mcp.run(
        transport='http',
        host="127.0.0.1",
        port=8888
    )