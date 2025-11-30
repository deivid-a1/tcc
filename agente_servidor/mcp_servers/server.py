from fastmcp import FastMCP

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
    }
}

CARDAPIO_RU = {
    "2024-03-20": {
        "almoco": "Estrogonofe de Frango",
        "jantar": "Peixe Assado",
        "vegetariano": "Grão de Bico com Legumes"
    }
}

USUARIOS_RU = {
    "2023001": {"saldo": 15.50, "tipo": "subsidiado"},
    "2023002": {"saldo": 2.00, "tipo": "integral"},
    "2023003": {"saldo": 50.00, "tipo": "subsidiado"}
}

LIVROS_BIBLIOTECA = {
    "LIV001": {"titulo": "Clean Code", "autor": "Robert Martin", "copias": 2, "disponiveis": 1},
    "LIV002": {"titulo": "Introduction to Algorithms", "autor": "Cormen", "copias": 3, "disponiveis": 0},
    "LIV003": {"titulo": "Design Patterns", "autor": "Gamma", "copias": 1, "disponiveis": 1}
}

SITUACAO_BIBLIOTECA = {
    "2023001": {"multas": False, "livros_emprestados": []},
    "2023002": {"multas": True, "valor_multa": 12.50, "livros_emprestados": ["LIV002"]}
}

HISTORICO_ACADEMICO = {
    "2023001": {
        "cursadas": ["MAT0025", "CIC0004"],
        "reprovadas": [],
        "cra": 4.5
    },
    "2023002": {
        "cursadas": ["CIC0004"],
        "reprovadas": ["MAT0025"],
        "cra": 2.8
    }
}

REQUISITOS_DISCIPLINAS = {
    "CIC0004": [],
    "MAT0025": [],
    "CIC0099": ["CIC0004"],
    "MAT0026": ["MAT0025"]
}

mcp = FastMCP("ferramentas-complexas-unb")

@mcp.tool
def consultar_horario(codigo: str) -> dict:
    return HORARIOS_MOCK.get(codigo.upper(), {"erro": "Disciplina não encontrada"})

@mcp.tool
def consultar_cardapio_ru(data: str) -> dict:
    return CARDAPIO_RU.get(data, {"erro": "Cardápio não disponível para esta data"})

@mcp.tool
def verificar_saldo_usuario(matricula: str) -> dict:
    return USUARIOS_RU.get(matricula, {"erro": "Usuário não encontrado"})

@mcp.tool
def calcular_custo_refeicao(tipo_usuario: str) -> float:
    if tipo_usuario.lower() == "subsidiado":
        return 2.50
    return 15.00

@mcp.tool
def buscar_livro_por_titulo(termo: str) -> list:
    resultados = []
    termo = termo.lower()
    for id_livro, dados in LIVROS_BIBLIOTECA.items():
        if termo in dados["titulo"].lower():
            r = dados.copy()
            r["id"] = id_livro
            resultados.append(r)
    return resultados

@mcp.tool
def verificar_disponibilidade_exemplar(id_livro: str) -> dict:
    livro = LIVROS_BIBLIOTECA.get(id_livro)
    if not livro:
        return {"erro": "Livro não encontrado"}
    return {"titulo": livro["titulo"], "disponiveis": livro["disponiveis"]}

@mcp.tool
def verificar_pendencias_biblioteca(matricula: str) -> dict:
    return SITUACAO_BIBLIOTECA.get(matricula, {"erro": "Aluno não cadastrado na biblioteca"})

@mcp.tool
def reservar_livro(matricula: str, id_livro: str) -> str:
    situacao = SITUACAO_BIBLIOTECA.get(matricula)
    if not situacao:
        return "Erro: Aluno não encontrado"
    
    if situacao["multas"]:
        return "Erro: Não é possível reservar. Aluno possui multas pendentes."
    
    livro = LIVROS_BIBLIOTECA.get(id_livro)
    if not livro:
        return "Erro: Livro inexistente"
    
    if livro["disponiveis"] < 1:
        return "Erro: Não há exemplares disponíveis para reserva imediata."
    
    return f"Sucesso: Livro '{livro['titulo']}' reservado para matrícula {matricula}."

@mcp.tool
def consultar_historico_analitico(matricula: str) -> dict:
    return HISTORICO_ACADEMICO.get(matricula, {"erro": "Histórico não encontrado"})

@mcp.tool
def verificar_requisitos_disciplina(codigo_disciplina: str) -> list:
    return REQUISITOS_DISCIPLINAS.get(codigo_disciplina.upper(), [])

@mcp.tool
def simular_cra_projetado(matricula: str, media_esperada: float, creditos_futuros: int) -> float:
    dados = HISTORICO_ACADEMICO.get(matricula)
    if not dados:
        return -1.0
    
    cra_atual = dados["cra"]
    creditos_passados = 100
    novo_cra = ((cra_atual * creditos_passados) + (media_esperada * creditos_futuros)) / (creditos_passados + creditos_futuros)
    return round(novo_cra, 2)

if __name__ == "__main__":
    mcp.run(transport='http', host="0.0.0.0", port=8889)