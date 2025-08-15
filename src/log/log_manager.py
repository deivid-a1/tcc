import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class PromptLog:
    """Estrutura de dados para log de cada prompt"""
    timestamp: str
    prompt: str
    model_name: str
    parameters: Dict[str, Any]
    execution_time: float
    token_count_input: int
    token_count_output: int
    thinking_content: str
    final_content: str
    error: Optional[str] = None


class LogManager:
    """Gerenciador de logs para cada execução"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
    def create_logger(self, session_id: str) -> logging.Logger:
        """Cria um logger específico para a sessão"""
        logger = logging.getLogger(f"llm_session_{session_id}")
        logger.setLevel(logging.DEBUG)
        
        # Remove handlers anteriores para evitar duplicação
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para arquivo
        log_file = self.log_dir / f"session_{session_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter detalhado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def save_prompt_log(self, prompt_log: PromptLog):
        """Salva log estruturado do prompt em JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = self.log_dir / f"prompt_{timestamp}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(prompt_log), f, ensure_ascii=False, indent=2)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Analisa logs e retorna estatísticas de performance"""
        json_files = list(self.log_dir.glob("prompt_*.json"))
        
        if not json_files:
            return {"message": "Nenhum log encontrado"}
        
        execution_times = []
        token_counts = []
        
        for file in json_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                execution_times.append(data['execution_time'])
                token_counts.append(data['token_count_output'])
        
        return {
            "total_prompts": len(json_files),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "avg_output_tokens": sum(token_counts) / len(token_counts)
        }