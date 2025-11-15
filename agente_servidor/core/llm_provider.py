from abc import ABC, abstractmethod
from typing import Dict, Any, List
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str, 
                      conversation_history: List[Dict[str, str]] = None) -> str:
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass

class QwenLocalProvider(LLMProvider):
    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True
        )
        self.model_name = model_name
    
    async def generate(self, system_prompt: str, user_message: str,
                      conversation_history: List[Dict[str, str]] = None) -> str:
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return response.strip()
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "qwen_local",
            "model": self.model_name,
            "quantization": "int4",
            "device": str(self.model.device)
        }

class GeminiAPIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, system_prompt: str, user_message: str,
                      conversation_history: List[Dict[str, str]] = None) -> str:
        raise NotImplementedError("Gemini provider será implementado futuramente")
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "gemini_api",
            "model": self.model
        }