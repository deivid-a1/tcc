from typing import Literal, Optional, Dict, Any, List, Callable
from pydantic import BaseModel
import json
import logging
import re
from core.llm_provider import LLMProvider
from core.tools import ToolRegistry

logger = logging.getLogger(__name__)

class ReactDecision(BaseModel):
    thought: str
    action: Literal["ANSWER", "ABORT"] | str
    action_input: Optional[Dict[str, Any]] = None
    answer: Optional[str] = None

class ReactAgent:
    MAX_ITERATIONS = 10
    
    def __init__(self, llm_provider: LLMProvider, tool_registry: ToolRegistry):
        self.llm = llm_provider
        self.tools = tool_registry
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        tools_description = self.tools.get_tools_description()
        
        return f"""Você é um agente assistente de estudantes da Universidade de Brasília (UnB).

Sua função é ajudar estudantes com informações acadêmicas, horários, cardápios, cálculos e outras tarefas.

FERRAMENTAS DISPONÍVEIS:
{tools_description}

PROCESSO DE RACIOCÍNIO (REACT):
Você deve seguir o ciclo Reasoning → Action → Observation até resolver o problema.

FORMATO DE RESPOSTA:
Você DEVE responder APENAS com um objeto JSON válido no seguinte formato:

{{
  "thought": "seu raciocínio sobre o problema e próximos passos. Este campo é OBRIGATÓRIO.",
  "action": "nome_da_ferramenta" ou "ANSWER" ou "ABORT",
  "action_input": {{"parametro": "valor"}} ou null,
  "answer": "resposta final ao usuário" ou null
}}

REGRAS:
1. O campo "thought" é SEMPRE obrigatório, mesmo se a ação for "ANSWER".
2. Se você tem informação suficiente para responder, use "action": "ANSWER" e preencha "answer"
3. Se você precisa usar uma ferramenta ("action": "nome_da_ferramenta"), você DEVE preencher o "action_input" com os parâmetros exatos definidos no JSON Schema da ferramenta.
4. Se você não consegue resolver o problema mesmo após usar ferramentas, use "action": "ABORT"
5. NUNCA invente informações. Use as ferramentas disponíveis.
6. Seja conciso e direto nas respostas.

EXEMPLO DE USO DE FERRAMENTA:
Prompt do Usuário: "Qual o horário de CIC0004?"

Sua Resposta JSON:
{{
  "thought": "O usuário quer o horário de CIC0004. A ferramenta 'consultar_horario' precisa do parâmetro 'codigo'. Vou extrair 'CIC0004' do prompt.",
  "action": "consultar_horario",
  "action_input": {{"codigo": "CIC0004"}},
  "answer": null
}}

EXEMPLO DE RESPOSTA DIRETA (PERGUNTA SIMPLES):
Prompt do Usuário: "Quanto é 1+1?"

Sua Resposta JSON:
{{
  "thought": "O usuário fez uma pergunta simples (1+1). Posso responder diretamente.",
  "action": "ANSWER",
  "action_input": null,
  "answer": "O resultado de 1 + 1 é 2."
}}

IMPORTANTE: Responda APENAS com o JSON, sem texto adicional antes ou depois.
"""
    
    async def run(self, user_prompt: str, step_callback: Optional[Callable[[Dict], Any]] = None) -> str:
        logger.info(f"Iniciando novo ciclo REACT para o prompt: '{user_prompt[:70]}...'")
        conversation_history = []
        observations = []
        
        for iteration in range(self.MAX_ITERATIONS):
            context = self._build_context(user_prompt, observations)
            
            llm_response = await self.llm.generate(
                system_prompt=self.system_prompt,
                user_message=context,
                conversation_history=conversation_history
            )
            
            try:
                decision = self._parse_decision(llm_response)
            except Exception as e:
                error_msg = f"Erro ao processar decisão do agente: {str(e)}"
                if step_callback:
                    await step_callback({"type": "error", "content": error_msg})
                return error_msg
            
            conversation_history.append({"role": "assistant", "content": llm_response})
            
            if step_callback:
                await step_callback({
                    "type": "thought", 
                    "content": decision.thought,
                    "action": decision.action,
                    "input": decision.action_input
                })
            
            if decision.action == "ANSWER":
                if step_callback:
                    await step_callback({"type": "final", "content": decision.answer})
                return decision.answer
            
            elif decision.action == "ABORT":
                return "Desculpe, não consegui resolver seu problema com as ferramentas disponíveis."
            
            else:
                try:
                    if step_callback:
                        await step_callback({
                            "type": "tool_start", 
                            "tool": decision.action,
                            "input": decision.action_input
                        })
                        
                    tool = self.tools.get_tool(decision.action)
                    result = await tool.execute(**(decision.action_input or {}))
                    observation = f"Resultado da ferramenta '{decision.action}': {result}"
                    
                    if step_callback:
                        await step_callback({
                            "type": "observation", 
                            "content": str(result)
                        })
                    
                    observations.append(observation)
                    
                    conversation_history.append({
                        "role": "user",
                        "content": f"OBSERVATION: {observation}"
                    })
                    
                except Exception as e:
                    error_msg = f"Erro ao executar ferramenta '{decision.action}': {str(e)}"
                    observations.append(error_msg)
                    conversation_history.append({
                        "role": "user",
                        "content": f"OBSERVATION: {error_msg}"
                    })
                    if step_callback:
                        await step_callback({"type": "error", "content": error_msg})
        
        return f"ABORT: Limite de {self.MAX_ITERATIONS} iterações atingido sem resolver o problema."
    
    def _build_context(self, original_prompt: str, observations: List[str]) -> str:
        if not observations:
            return original_prompt
        
        context = f"TAREFA ORIGINAL: {original_prompt}\n\n"
        context += "OBSERVAÇÕES DAS AÇÕES ANTERIORES:\n"
        context += "\n".join(observations)
        return context
    
    def _parse_decision(self, llm_response: str) -> ReactDecision:
        llm_response = llm_response.strip()
        match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        
        if not match:
            raise ValueError(f"Nenhum JSON válido encontrado na resposta do LLM: {llm_response}")
        
        json_str = match.group(0)
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Falha ao decodificar JSON: {e}")
            
        return ReactDecision(**data)