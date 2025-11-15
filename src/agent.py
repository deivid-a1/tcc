from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

from llm.base_llm import BaseLLM
from log.log_manager import LogManager


class Agent:
    """Agente que interage com modelos LLM para tarefas específicas"""
    
    def __init__(
        self, 
        llm_model: BaseLLM,
        agent_name: str = "DefaultAgent",
        log_manager: Optional[LogManager] = None
    ):
        self.llm_model = llm_model
        self.agent_name = agent_name
        self.log_manager = log_manager or LogManager()
        
        # Histórico de conversação
        self.conversation_history: List[Dict[str, str]] = []
        
        # Logger específico do agente
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = self.log_manager.create_logger(f"agent_{self.agent_name}_{self.session_id}")
        
        self.logger.info(f"Agente {agent_name} inicializado com modelo {llm_model.model_name}")
    
    def chat(
        self, 
        message: str, 
        max_new_tokens: int = 32768,
        include_history: bool = True,
        **kwargs
    ) -> Dict[str, str]:
        """
        Conversa com o agente
        Retorna dict com thinking_content e response
        """
        self.logger.info(f"Recebendo mensagem: {message}...")
        
        # Constrói prompt com histórico se solicitado
        if include_history and self.conversation_history:
            prompt = self._build_prompt_with_history(message)
        else:
            prompt = message
        
        # Executa prompt no modelo
        thinking_content, response = self.llm_model.execute_prompt(
            prompt, 
            max_new_tokens=max_new_tokens,
            **kwargs
        )
        
        # Adiciona ao histórico
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": message,
            "thinking": thinking_content,
            "assistant": response
        })
        
        self.logger.info("Resposta gerada e adicionada ao histórico")
        
        return {
            "thinking_content": thinking_content,
            "response": response
        }
    
    def _build_prompt_with_history(self, current_message: str) -> str:
        """Constrói prompt incluindo histórico da conversação"""
        prompt_parts = ["Conversation history:"]
        
        # Inclui últimas N mensagens para não exceder limite de contexto
        recent_history = self.conversation_history[-5:]  # Últimas 5 mensagens
        
        for entry in recent_history:
            prompt_parts.append(f"User: {entry['user']}")
            prompt_parts.append(f"Assistant: {entry['assistant']}")
        
        prompt_parts.append(f"\nCurrent message:\nUser: {current_message}")
        
        return "\n".join(prompt_parts)
    
    def clear_history(self) -> None:
        """Limpa o histórico da conversação"""
        self.logger.info("Limpando histórico da conversação")
        self.conversation_history.clear()
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Retorna resumo da conversação atual"""
        return {
            "agent_name": self.agent_name,
            "model_name": self.llm_model.model_name,
            "total_messages": len(self.conversation_history),
            "session_start": self.conversation_history[0]["timestamp"] if self.conversation_history else None,
            "last_message": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def save_conversation(self, filename: Optional[str] = None) -> str:
        """Salva conversação em arquivo JSON"""
        if filename is None:
            filename = f"conversation_{self.agent_name}_{self.session_id}.json"
        
        conversation_data = {
            "agent_info": self.get_conversation_summary(),
            "conversation": self.conversation_history
        }
        
        filepath = self.log_manager.log_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Conversação salva em: {filepath}")
        return str(filepath)
    
    def load_conversation(self, filename: str) -> None:
        """Carrega conversação de arquivo JSON"""
        filepath = self.log_manager.log_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        self.conversation_history = conversation_data["conversation"]
        self.logger.info(f"Conversação carregada de: {filepath}")
    
    def ask_with_context(
        self, 
        question: str, 
        context: str,
        max_new_tokens: int = 32768,
        **kwargs
    ) -> Dict[str, str]:
        """
        Faz pergunta fornecendo contexto específico
        """
        prompt = f"""Context:
                    {context}

                    Question: {question}

                    Answer based on the provided context."""
        
        return self.chat(
            prompt, 
            max_new_tokens=max_new_tokens,
            include_history=False,  # Não inclui histórico para manter foco no contexto
            **kwargs
        )