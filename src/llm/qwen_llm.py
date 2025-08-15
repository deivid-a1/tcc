import torch
from typing import Tuple, Any, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from llm.base_llm import BaseLLM
from log.log_manager import LogManager


class QwenLLM(BaseLLM):
    """Implementação específica para o modelo Qwen"""
    
    def __init__(
        self, 
        model_name: str = "Qwen/Qwen3-14B",
        use_quantization: bool = True,
        log_manager: Optional[LogManager] = None
    ):
        super().__init__(model_name, log_manager)
        self.use_quantization = use_quantization
        self.model = None
        self.tokenizer = None
        
    def load_model(self) -> None:
        """Carrega o modelo Qwen com configurações específicas"""
        self.logger.info("Carregando tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        if self.use_quantization:
            self.logger.info("Configurando quantização BitsAndBytes...")
            compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            self.logger.info("Carregando modelo com quantização...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto"
            )
        else:
            self.logger.info("Carregando modelo sem quantização...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto"
            )
        
        self.logger.info("Modelo carregado com sucesso")
    
    def prepare_input(self, prompt: str) -> Any:
        """Prepara o input para o modelo Qwen"""
        self.logger.debug("Preparando input do modelo...")
        
        messages = [{"role": "user", "content": prompt}]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        self.logger.debug(f"Input preparado. Tokens: {len(model_inputs.input_ids[0])}")
        
        return model_inputs
    
    def parse_output(self, generated_ids: Any) -> Tuple[str, str]:
        """Processa output específico do Qwen com thinking content"""
        self.logger.debug("Processando output do modelo...")
        
        # Extrai apenas os tokens gerados (remove os tokens de input)
        model_inputs_length = len(generated_ids[0]) - len(generated_ids[0])
        output_ids = generated_ids[0][model_inputs_length:].tolist()
        
        # Parsing thinking content (procura pelo token </think> = 151668)
        try:
            index = len(output_ids) - output_ids[::-1].index(151668)
            self.logger.debug("Token </think> encontrado, separando thinking content")
        except ValueError:
            index = 0
            self.logger.debug("Token </think> não encontrado")
        
        thinking_content = self.tokenizer.decode(
            output_ids[:index], 
            skip_special_tokens=True
        ).strip("\n")
        
        final_content = self.tokenizer.decode(
            output_ids[index:], 
            skip_special_tokens=True
        ).strip("\n")
        
        self.logger.debug(f"Thinking content: {len(thinking_content)} chars")
        self.logger.debug(f"Final content: {len(final_content)} chars")
        
        return thinking_content, final_content
    
    def generate_response(
        self, 
        prompt: str, 
        max_new_tokens: int = 32768,
        **kwargs
    ) -> Tuple[str, str]:
        """Gera resposta usando o modelo Qwen"""
        if not self.is_loaded():
            self.logger.info("Modelo não carregado. Carregando...")
            self.load_model()
        
        self.logger.debug(f"Gerando resposta para prompt de {len(prompt)} caracteres")
        
        # Prepara input
        model_inputs = self.prepare_input(prompt)
        
        # Parâmetros padrão para geração
        generation_params = {
            "max_new_tokens": max_new_tokens,
            **kwargs
        }
        
        self.logger.debug(f"Parâmetros de geração: {generation_params}")
        
        # Gera resposta
        generated_ids = self.model.generate(
            **model_inputs,
            **generation_params
        )
        
        # Processa output
        return self.parse_output(generated_ids)