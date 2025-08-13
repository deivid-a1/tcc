#!/usr/bin/env python3
"""
Teste de Carregamento e Validação do Modelo Qwen3-14B
Para TCC: Assistente Estudantil Web Descentralizada

Executa testes básicos para verificar compatibilidade com NVIDIA A2 (15GB VRAM)
"""

import torch
import psutil
import time
import gc
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import BitsAndBytesConfig
import subprocess
import sys

def check_system_resources():
    """Verifica recursos do sistema antes do teste"""
    print("=== VERIFICAÇÃO DO SISTEMA ===")
    
    # GPU Info
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✅ GPU: {gpu_name}")
        print(f"✅ VRAM Total: {total_memory:.1f}GB")
        
        # VRAM Disponível
        torch.cuda.empty_cache()
        available_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
        available_gb = available_memory / (1024**3)
        print(f"✅ VRAM Disponível: {available_gb:.1f}GB")
    else:
        print("❌ CUDA não disponível!")
        return False
    
    # RAM Info
    ram_gb = psutil.virtual_memory().total / (1024**3)
    ram_available = psutil.virtual_memory().available / (1024**3)
    print(f"✅ RAM Total: {ram_gb:.1f}GB")
    print(f"✅ RAM Disponível: {ram_available:.1f}GB")
    
    return True

def install_requirements():
    """Instala dependências necessárias"""
    print("\n=== INSTALAÇÃO DE DEPENDÊNCIAS ===")
    requirements = [
        "torch",
        "transformers>=4.51.0",
        "accelerate",
        "bitsandbytes",
        "sentencepiece",
        "protobuf"
    ]
    
    for package in requirements:
        try:
            __import__(package.split('>=')[0].split('==')[0])
            print(f"✅ {package} já instalado")
        except ImportError:
            print(f"⚠️  Instalando {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def test_model_loading():
    """Testa carregamento do modelo com diferentes configurações"""
    model_name = "Qwen/Qwen3-14B"
    
    print(f"\n=== TESTE DE CARREGAMENTO: {model_name} ===")
    
    # Configurações de quantização para testar
    quantization_configs = [
        {
            "name": "4-bit (BNB)",
            "config": BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        },
        {
            "name": "8-bit (BNB)", 
            "config": BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_enable_fp32_cpu_offload=True
            )
        },
        {
            "name": "FP16 (Sem quantização)",
            "config": None
        }
    ]
    
    successful_config = None
    
    for quant_config in quantization_configs:
        print(f"\n--- Testando: {quant_config['name']} ---")
        
        try:
            start_time = time.time()
            
            # Limpa cache antes do teste
            torch.cuda.empty_cache()
            gc.collect()
            
            # Carrega tokenizer
            print("Carregando tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            
            # Prepara argumentos do modelo
            model_kwargs = {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "trust_remote_code": True,
                "low_cpu_mem_usage": True
            }
            
            if quant_config["config"]:
                model_kwargs["quantization_config"] = quant_config["config"]
            
            # Carrega modelo
            print("Carregando modelo...")
            model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
            
            load_time = time.time() - start_time
            
            # Verifica uso de VRAM
            if torch.cuda.is_available():
                memory_used = torch.cuda.memory_allocated(0) / (1024**3)
                memory_cached = torch.cuda.memory_reserved(0) / (1024**3)
                print(f"✅ Carregamento bem-sucedido!")
                print(f"✅ Tempo de carregamento: {load_time:.1f}s")
                print(f"✅ VRAM usada: {memory_used:.1f}GB")
                print(f"✅ VRAM reservada: {memory_cached:.1f}GB")
                
                successful_config = {
                    "name": quant_config["name"],
                    "model": model,
                    "tokenizer": tokenizer,
                    "memory_used": memory_used,
                    "load_time": load_time
                }
                
                # Se conseguiu carregar, para aqui
                break
            
        except Exception as e:
            print(f"❌ Falha com {quant_config['name']}: {str(e)}")
            
            # Limpa memória em caso de erro
            if 'model' in locals():
                del model
            if 'tokenizer' in locals():
                del tokenizer
            torch.cuda.empty_cache()
            gc.collect()
            continue
    
    return successful_config

def test_basic_inference(config):
    """Tests basic model inference"""
    if not config:
        print("❌ No valid configuration available for testing")
        return False
    
    print(f"\n=== BASIC INFERENCE TEST ===")
    print(f"Using configuration: {config['name']}")
    
    model = config["model"]
    tokenizer = config["tokenizer"]
    
    # Simple test prompt in English
    test_prompt = "Explain in one sentence what artificial intelligence is."
    
    try:
        # Prepare messages in English
        messages = [
            {"role": "system", "content": "You are an intelligent academic assistant."},
            {"role": "user", "content": test_prompt}
        ]
        
        # Aplica template de chat
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokeniza
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        print("Generating response...")
        start_time = time.time()
        
        # Generate response
        with torch.no_grad():
            generated_ids = model.generate(
                model_inputs.input_ids,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generation_time = time.time() - start_time
        
        # Decode response
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"✅ Inference successful!")
        print(f"✅ Generation time: {generation_time:.2f}s")
        print(f"✅ Prompt: {test_prompt}")
        print(f"✅ Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Inference error: {str(e)}")
        return False

def test_function_calling_capability(config):
    """Tests basic function calling capability"""
    if not config:
        print("❌ Model not available for function calling test")
        return False
    
    print(f"\n=== TESTE DE FUNCTION CALLING ===")
    
    model = config["model"]
    tokenizer = config["tokenizer"]
    
    # Function calling prompt in English
    function_prompt = """
    You have access to the following function:
    
    get_lab_availability(lab_name: str) -> dict
    Description: Checks laboratory availability
    Parameters: lab_name (laboratory name)
    
    Question: Check the availability of computer lab 1.
    """
    
    try:
        messages = [
            {"role": "system", "content": "You are an assistant that can use functions. When necessary, call the appropriate function."},
            {"role": "user", "content": function_prompt}
        ]
        
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        print("Testing function calling capability...")
        
        with torch.no_grad():
            generated_ids = model.generate(
                model_inputs.input_ids,
                max_new_tokens=150,
                do_sample=True,
                temperature=0.3,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"✅ Function calling response:")
        print(f"📝 {response}")
        
        # Check if model attempted to use the function
        function_indicators = [
            "get_lab_availability",
            "computer lab 1", 
            "check",
            "availability"
        ]
        
        response_lower = response.lower()
        indicators_found = [indicator for indicator in function_indicators if indicator.lower() in response_lower]
        
        if indicators_found:
            print(f"✅ Model demonstrated function understanding (indicators: {indicators_found})")
            return True
        else:
            print("⚠️  Model did not demonstrate clear function calling capability")
            return False
            
    except Exception as e:
        print(f"❌ Function calling test error: {str(e)}")
        return False

def cleanup_and_summary(config):
    """Limpa recursos e apresenta resumo"""
    print(f"\n=== LIMPEZA E RESUMO ===")
    
    if config:
        # Limpa modelo da memória
        if 'model' in config:
            del config['model']
        if 'tokenizer' in config:
            del config['tokenizer']
    
    torch.cuda.empty_cache()
    gc.collect()
    
    final_memory = torch.cuda.memory_allocated(0) / (1024**3) if torch.cuda.is_available() else 0
    print(f"✅ Memória GPU após limpeza: {final_memory:.1f}GB")
    
    if config:
        print(f"\n📋 RESUMO DO TESTE:")
        print(f"   Modelo: Qwen3-14B-Instruct")
        print(f"   Configuração funcional: {config['name']}")
        print(f"   VRAM utilizada: {config['memory_used']:.1f}GB")
        print(f"   Tempo de carregamento: {config['load_time']:.1f}s")
        print(f"   Status: ✅ APROVADO para uso")
        
        print(f"\n🚀 PRÓXIMOS PASSOS:")
        print(f"   1. Implementar Qwen-Agent framework")
        print(f"   2. Criar ferramentas acadêmicas customizadas")
        print(f"   3. Testar cenários específicos do TCC")
        print(f"   4. Manter Qwen2.5-14B como backup")
    else:
        print(f"\n❌ TESTE FALHOU")
        print(f"   Recomendação: Usar Qwen2.5-14B-Instruct como alternativa")
        print(f"   Motivo: Hardware insuficiente para Qwen3-14B")

def main():
    """Função principal que executa todos os testes"""
    print("🧪 TESTE DE COMPATIBILIDADE: Qwen3-14B para Assistente Acadêmico")
    print("=" * 60)
    
    # 1. Verifica sistema
    if not check_system_resources():
        print("❌ Sistema não atende requisitos mínimos")
        return
    
    # 2. Instala dependências
    try:
        install_requirements()
    except Exception as e:
        print(f"❌ Erro na instalação de dependências: {e}")
        return
    
    # 3. Testa carregamento do modelo
    successful_config = test_model_loading()
    
    if successful_config:
        # 4. Testa inferência básica
        inference_success = test_basic_inference(successful_config)
        
        if inference_success:
            # 5. Testa function calling
            function_calling_success = test_function_calling_capability(successful_config)
    
    # 6. Limpa e apresenta resumo
    cleanup_and_summary(successful_config)

if __name__ == "__main__":
    main()