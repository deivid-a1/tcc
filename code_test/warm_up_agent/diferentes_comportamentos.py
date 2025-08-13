import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import warnings
warnings.filterwarnings("ignore")

# Modelo de function calling que funciona
model_name = "InterSync/Mistral-7B-Instruct-v0.2-Function-Calling"

print("Carregando modelo Mistral com Function Calling...")

# Configuração de quantização para economizar VRAM
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

# Configurar pad_token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"Modelo carregado! VRAM usada: {torch.cuda.memory_allocated() / 1024**3:.1f}GB")

def gerar_resposta(prompt, personalidade="equilibrado"):
    # Formatar prompt para modelo especializado em reasoning
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    
    # Tokenizar com attention_mask
    inputs = tokenizer(
        formatted_prompt, 
        return_tensors="pt", 
        padding=True, 
        truncation=True,
        max_length=512
    )
    
    if torch.cuda.is_available():
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
    
    # Configurações por personalidade
    configs = {
        "criativo": {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 50,
            "repetition_penalty": 1.05,
            "do_sample": True,
            "max_new_tokens": 200
        },
        "conservador": {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 20,
            "repetition_penalty": 1.2,
            "do_sample": True,
            "max_new_tokens": 150
        },
        "determinista": {
            "temperature": 0.1,
            "top_p": 0.6,
            "top_k": 10,
            "repetition_penalty": 1.3,
            "do_sample": True,
            "max_new_tokens": 100
        },
        "equilibrado": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1.1,
            "do_sample": True,
            "max_new_tokens": 180
        },
        "agente_tecnico": {
            "temperature": 0.2,
            "top_p": 0.7,
            "top_k": 15,
            "repetition_penalty": 1.25,
            "do_sample": True,
            "max_new_tokens": 350  # Mais tokens para reasoning complexo
        },
        "reasoning": {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 20,
            "repetition_penalty": 1.2,
            "do_sample": True,
            "max_new_tokens": 400  # Para explicações detalhadas
        },
        "function_calling": {
            "temperature": 0.1,
            "top_p": 0.6,
            "top_k": 10,
            "repetition_penalty": 1.3,
            "do_sample": True,
            "max_new_tokens": 300
        }
    }
    
    config = configs.get(personalidade, configs["equilibrado"])
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            **config
        )
    
    # Decodificar apenas a resposta nova
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()

def testar_comportamentos():
    print("=== REASONING COMPLEXO ===")
    prompt_reasoning = "Explique passo a passo como resolver: Se um trem viaja a 80 km/h e precisa chegar em 3 horas, qual deve ser a velocidade se o tempo for reduzido para 2 horas?"
    print(gerar_resposta(prompt_reasoning, "reasoning"))
    print()
    
    print("=== FUNCTION CALLING ===")
    prompt_function = "Crie uma função Python que calcule a área de diferentes formas geométricas (quadrado, retângulo, círculo)"
    print(gerar_resposta(prompt_function, "function_calling"))
    print()
    
    print("=== AGENTE TÉCNICO ===")
    prompt_tecnico = "Como implementar um sistema de autenticação JWT em FastAPI com middleware personalizado?"
    print(gerar_resposta(prompt_tecnico, "agente_tecnico"))
    print()
    
    print("=== CRIATIVO ===")
    prompt_criativo = "Invente uma história sobre um robô que descobre sentimentos"
    print(gerar_resposta(prompt_criativo, "criativo"))

def agente_reasoning(pergunta):
    """Agente especializado em raciocínio lógico passo-a-passo"""
    system_context = """Você é um assistente especializado em raciocínio lógico.
    Sempre explique seu pensamento passo a passo.
    Use numeração para organizar seu raciocínio.
    Seja preciso e metódico."""
    
    prompt_completo = f"{system_context}\n\nProblema: {pergunta}"
    return gerar_resposta(prompt_completo, "reasoning")

def agente_function_calling(pergunta):
    """Agente especializado em criação de funções e APIs"""
    system_context = """Você é um assistente especializado em desenvolvimento de funções.
    Crie código limpo, bem documentado e testável.
    Inclua exemplos de uso quando apropriado.
    Foque em boas práticas de programação."""
    
    prompt_completo = f"{system_context}\n\nTarefa: {pergunta}"
    return gerar_resposta(prompt_completo, "function_calling")

def chat_interativo():
    print("\n" + "="*50)
    print("Chat com comportamentos personalizados")
    print("Comandos: 'criativo', 'conservador', 'determinista', 'agente_tecnico', 'reasoning', 'function_calling', 'quit'")
    print("=" * 50)
    
    personalidade = "equilibrado"
    
    while True:
        user_input = input(f"\n[{personalidade}] Você: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() in ['criativo', 'conservador', 'determinista', 'agente_tecnico', 'reasoning', 'function_calling', 'equilibrado']:
            personalidade = user_input.lower()
            print(f"Personalidade alterada para: {personalidade}")
            continue
        
        if not user_input:
            continue
        
        print("Gerando resposta...")
        try:
            resposta = gerar_resposta(user_input, personalidade)
            print(f"Assistente: {resposta}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    # Teste rápido
    print("\n=== TESTE RÁPIDO ===")
    resposta = gerar_resposta("Olá! Como você pode me ajudar?", "equilibrado")
    print(f"Resposta: {resposta}")
    
    # Testes de comportamento
    print("\n=== TESTANDO COMPORTAMENTOS ===")
    testar_comportamentos()
    
    # Chat interativo
    chat_interativo()