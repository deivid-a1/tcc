from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import logging
import time
from datetime import datetime

from log.log_manager import LogManager, PromptLog


class BaseLLM(ABC):
    """Classe base abstrata para interação com modelos LLM"""
    
    def __init__(self, model_name: str, log_manager: Optional[LogManager] = None):
        self.model_name = model_name
        self.log_manager = log_manager or LogManager()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = self.log_manager.create_logger(self.session_id)
        
        self.logger.info(f"Inicializando modelo: {model_name}")
        
    @abstractmethod
    def load_model(self) -> None:
        """Carrega o modelo e tokenizer"""
        pass
    
    @abstractmethod
    def generate_response(
        self, 
        prompt: str, 
        max_new_tokens: int = 32768,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Gera resposta para o prompt
        Retorna: (thinking_content, final_content)
        """
        pass
    
    @abstractmethod
    def prepare_input(self, prompt: str) -> Any:
        """Prepara input para o modelo"""
        pass
    
    @abstractmethod
    def parse_output(self, output: Any) -> Tuple[str, str]:
        """
        Processa output do modelo
        Retorna: (thinking_content, final_content)
        """
        pass
    
    def get_token_count(self, text: str) -> int:
        """Conta tokens no texto"""
        if hasattr(self, 'tokenizer'):
            return len(self.tokenizer.encode(text))
        return len(text.split())  # Fallback simples
    
    def execute_prompt(
        self, 
        prompt: str, 
        max_new_tokens: int = 32768,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Executa prompt com logging completo
        Retorna: (thinking_content, final_content)
        """
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        self.logger.info(f"Iniciando execução do prompt: {prompt}")
        self.logger.debug(f"Parâmetros: max_new_tokens={max_new_tokens}, kwargs={kwargs}")
        
        try:
            thinking_content, final_content = self.generate_response(
                prompt, max_new_tokens, **kwargs
            )
            
            execution_time = time.time() - start_time
            
            # Contagem de tokens
            input_tokens = self.get_token_count(prompt)
            output_tokens = self.get_token_count(final_content)
            
            self.logger.info(f"Execução concluída em {execution_time:.2f}s")
            self.logger.info(f"Tokens: input={input_tokens}, output={output_tokens}")
            
            # Salva log estruturado
            prompt_log = PromptLog(
                timestamp=timestamp,
                prompt=prompt,
                model_name=self.model_name,
                parameters={
                    "max_new_tokens": max_new_tokens,
                    **kwargs
                },
                execution_time=execution_time,
                token_count_input=input_tokens,
                token_count_output=output_tokens,
                thinking_content=thinking_content,
                final_content=final_content
            )
            
            self.log_manager.save_prompt_log(prompt_log)
            
            return thinking_content, final_content
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"Erro durante execução: {error_msg}")
            
            # Salva log de erro
            prompt_log = PromptLog(
                timestamp=timestamp,
                prompt=prompt,
                model_name=self.model_name,
                parameters={"max_new_tokens": max_new_tokens, **kwargs},
                execution_time=execution_time,
                token_count_input=self.get_token_count(prompt),
                token_count_output=0,
                thinking_content="",
                final_content="",
                error=error_msg
            )
            
            self.log_manager.save_prompt_log(prompt_log)
            raise
    
    def is_loaded(self) -> bool:
        """Verifica se o modelo está carregado"""
        return hasattr(self, 'model') and self.model is not None