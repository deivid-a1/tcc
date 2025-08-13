#!/usr/bin/env python3
"""
MCP Server para Sistema Acadêmico
Demonstra como integrar ferramentas acadêmicas via MCP
"""

import asyncio
import json
from typing import Any, Sequence
from dataclasses import dataclass
import httpx
from mcp.server import Server
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource,
    Resource
)

# Simulação de dados acadêmicos
ACADEMIC_DATA = {
    "students": {
        "190026758": {
            "name": "João Silva",
            "course": "Engenharia de Software",
            "semester": 6,
            "grades": [8.5, 9.0, 7.5, 8.0],
            "enrolled_subjects": ["Algoritmos", "BD", "Redes", "IA"]
        },
        "190012345": {
            "name": "Maria Santos", 
            "course": "Ciência da Computação",
            "semester": 4,
            "grades": [9.0, 8.5, 9.5, 8.0],
            "enrolled_subjects": ["Estruturas", "SO", "Compiladores"]
        }
    },
    "library": {
        "available_books": [
            {"id": "001", "title": "Inteligência Artificial", "author": "Russell & Norvig", "available": True},
            {"id": "002", "title": "Algoritmos", "author": "Cormen", "available": False},
            {"id": "003", "title": "Redes de Computadores", "author": "Tanenbaum", "available": True}
        ]
    },
    "labs": {
        "lab_informatica_1": {"capacity": 30, "available_spots": 15, "equipment": "Windows 10"},
        "lab_informatica_2": {"capacity": 25, "available_spots": 0, "equipment": "Linux Ubuntu"},
        "lab_redes": {"capacity": 20, "available_spots": 8, "equipment": "Cisco Equipment"}
    }
}

# Inicializar servidor MCP
app = Server("academic-system")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """Lista recursos disponíveis no sistema acadêmico."""
    return [
        Resource(
            uri="academic://students",
            name="Lista de Estudantes",
            description="Acesso aos dados dos estudantes cadastrados",
            mimeType="application/json"
        ),
        Resource(
            uri="academic://library/catalog", 
            name="Catálogo da Biblioteca",
            description="Livros disponíveis no acervo da biblioteca",
            mimeType="application/json"
        ),
        Resource(
            uri="academic://labs/status",
            name="Status dos Laboratórios", 
            description="Disponibilidade atual dos laboratórios de informática",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Lê dados de recursos específicos."""
    if uri == "academic://students":
        return json.dumps(ACADEMIC_DATA["students"], indent=2, ensure_ascii=False)
    elif uri == "academic://library/catalog":
        return json.dumps(ACADEMIC_DATA["library"], indent=2, ensure_ascii=False)
    elif uri == "academic://labs/status":
        return json.dumps(ACADEMIC_DATA["labs"], indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Recurso não encontrado: {uri}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista ferramentas disponíveis."""
    return [
        Tool(
            name="get_student_grades",
            description="Busca as notas de um estudante específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "Matrícula do estudante"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="check_lab_availability", 
            description="Verifica disponibilidade de laboratórios",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_name": {
                        "type": "string", 
                        "description": "Nome do laboratório (opcional)",
                        "enum": ["lab_informatica_1", "lab_informatica_2", "lab_redes"]
                    }
                }
            }
        ),
        Tool(
            name="reserve_book",
            description="Reserva um livro na biblioteca",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "ID do livro a ser reservado"
                    },
                    "student_id": {
                        "type": "string", 
                        "description": "Matrícula do estudante"
                    }
                },
                "required": ["book_id", "student_id"]
            }
        ),
        Tool(
            name="calculate_semester_average",
            description="Calcula a média do semestre para um estudante",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "Matrícula do estudante"
                    }
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="find_optimal_study_location",
            description="Encontra o melhor local de estudo baseado em disponibilidade",
            inputSchema={
                "type": "object",
                "properties": {
                    "required_capacity": {
                        "type": "integer",
                        "description": "Número mínimo de lugares necessários",
                        "minimum": 1
                    },
                    "equipment_preference": {
                        "type": "string",
                        "description": "Preferência de equipamento",
                        "enum": ["Windows", "Linux", "Cisco", "any"]
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Executa ferramentas do sistema acadêmico."""
    
    if name == "get_student_grades":
        student_id = arguments.get("student_id")
        student = ACADEMIC_DATA["students"].get(student_id)
        
        if not student:
            return [TextContent(
                type="text", 
                text=f"Estudante com matrícula {student_id} não encontrado."
            )]
        
        average = sum(student["grades"]) / len(student["grades"])
        result = {
            "student": student["name"],
            "grades": student["grades"],
            "average": round(average, 2),
            "subjects": student["enrolled_subjects"]
        }
        
        return [TextContent(
            type="text",
            text=f"📊 **Relatório Acadêmico**\n\n"
                 f"**Estudante:** {result['student']}\n"
                 f"**Notas:** {result['grades']}\n" 
                 f"**Média:** {result['average']}\n"
                 f"**Disciplinas:** {', '.join(result['subjects'])}"
        )]
    
    elif name == "check_lab_availability":
        lab_name = arguments.get("lab_name")
        
        if lab_name:
            lab = ACADEMIC_DATA["labs"].get(lab_name)
            if not lab:
                return [TextContent(type="text", text=f"Laboratório {lab_name} não encontrado.")]
            
            status = "✅ Disponível" if lab["available_spots"] > 0 else "❌ Lotado"
            return [TextContent(
                type="text",
                text=f"🖥️ **{lab_name}**\n"
                     f"Status: {status}\n"
                     f"Vagas disponíveis: {lab['available_spots']}/{lab['capacity']}\n"
                     f"Equipamento: {lab['equipment']}"
            )]
        else:
            # Lista todos os labs
            report = "🖥️ **Status dos Laboratórios**\n\n"
            for lab_id, lab_info in ACADEMIC_DATA["labs"].items():
                status = "✅ Disponível" if lab_info["available_spots"] > 0 else "❌ Lotado"
                report += f"**{lab_id}:** {status} ({lab_info['available_spots']}/{lab_info['capacity']})\n"
            
            return [TextContent(type="text", text=report)]
    
    elif name == "reserve_book":
        book_id = arguments.get("book_id")
        student_id = arguments.get("student_id")
        
        # Verifica se livro existe
        book = None
        for b in ACADEMIC_DATA["library"]["available_books"]:
            if b["id"] == book_id:
                book = b
                break
        
        if not book:
            return [TextContent(type="text", text=f"❌ Livro ID {book_id} não encontrado.")]
        
        if not book["available"]:
            return [TextContent(type="text", text=f"❌ Livro '{book['title']}' já está emprestado.")]
        
        # Simula reserva
        book["available"] = False
        return [TextContent(
            type="text",
            text=f"✅ **Reserva Confirmada**\n\n"
                 f"**Livro:** {book['title']}\n"
                 f"**Autor:** {book['author']}\n"
                 f"**Estudante:** {student_id}\n"
                 f"**Status:** Reservado para retirada"
        )]
    
    elif name == "calculate_semester_average":
        student_id = arguments.get("student_id")
        student = ACADEMIC_DATA["students"].get(student_id)
        
        if not student:
            return [TextContent(type="text", text=f"Estudante {student_id} não encontrado.")]
        
        average = sum(student["grades"]) / len(student["grades"])
        status = "Aprovado" if average >= 7.0 else "Reprovado" if average < 5.0 else "Recuperação"
        
        return [TextContent(
            type="text",
            text=f"📈 **Cálculo da Média**\n\n"
                 f"**Estudante:** {student['name']}\n"
                 f"**Notas:** {student['grades']}\n"
                 f"**Média Final:** {round(average, 2)}\n"
                 f"**Situação:** {status}"
        )]
    
    elif name == "find_optimal_study_location":
        required_capacity = arguments.get("required_capacity", 1)
        equipment_pref = arguments.get("equipment_preference", "any")
        
        suitable_labs = []
        for lab_id, lab_info in ACADEMIC_DATA["labs"].items():
            if lab_info["available_spots"] >= required_capacity:
                if equipment_pref == "any" or equipment_pref.lower() in lab_info["equipment"].lower():
                    suitable_labs.append((lab_id, lab_info))
        
        if not suitable_labs:
            return [TextContent(
                type="text", 
                text="❌ Nenhum laboratório disponível com os critérios especificados."
            )]
        
        # Ordena por número de vagas disponíveis
        suitable_labs.sort(key=lambda x: x[1]["available_spots"], reverse=True)
        
        recommendation = "🎯 **Recomendação de Local de Estudo**\n\n"
        for lab_id, lab_info in suitable_labs:
            recommendation += f"**{lab_id}:** {lab_info['available_spots']} vagas ({lab_info['equipment']})\n"
        
        return [TextContent(type="text", text=recommendation)]
    
    else:
        raise ValueError(f"Ferramenta desconhecida: {name}")

async def main():
    """Função principal do servidor MCP."""
    # Lê argumentos da linha de comando para transporte
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # Modo stdio para comunicação local
        from mcp.server.stdio import stdio_server
        async with stdio_server() as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
    else:
        # Modo standalone para testes
        print("🎓 Servidor MCP Acadêmico iniciado")
        print("📚 Recursos disponíveis:")
        resources = await list_resources()
        for resource in resources:
            print(f"  - {resource.name}: {resource.description}")
        
        print("\n🔧 Ferramentas disponíveis:")
        tools = await list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

if __name__ == "__main__":
    asyncio.run(main())