"""
Exemplo de uso do sistema LLM orientado a objetos
"""

from log.log_manager import LogManager
from llm.qwen_llm import QwenLLM
from agent import LLMAgent


def main():
    # Inicializa o gerenciador de logs
    log_manager = LogManager(log_dir="log/meus_logs")
    
    # Inicializa o modelo Qwen
    print("Inicializando modelo Qwen...")
    qwen_model = QwenLLM(
        model_name="Qwen/Qwen3-14B",
        use_quantization=True,
        log_manager=log_manager
    )
    
    # Carrega o modelo (opcional - será carregado automaticamente no primeiro uso)
    qwen_model.load_model()
    
    # Cria um agente
    agent = LLMAgent(
        llm_model=qwen_model,
        agent_name="AssistenteTecnico",
        log_manager=log_manager
    )
    
    # Exemplo 1: Chat simples
    print("\n=== CHAT SIMPLES ===")
    response = agent.chat("Give me a short introduction to large language models.")
    print("Thinking:", response["thinking_content"][:200] + "...")
    print("Response:", response["response"])
    
    # Exemplo 2: Chat com contexto
    print("\n=== CHAT COM CONTEXTO ===")
    context = """
    Large Language Models (LLMs) are neural networks trained on vast amounts of text data.
    They can understand and generate human-like text for various tasks.
    """
    
    response = agent.ask_with_context(
        question="What are the main applications of LLMs?",
        context=context,
        max_new_tokens=32768
    )
    print("Response:", response["response"])
    
    # Exemplo 3: Conversação com histórico
    print("\n=== CONVERSAÇÃO COM HISTÓRICO ===")
    agent.chat("Hello, I'm learning about AI.")
    agent.chat("Can you explain what is machine learning?")
    agent.chat("How does it relate to deep learning?")
    
    # Resumo da conversação
    summary = agent.get_conversation_summary()
    print("Summary:", summary)
    
    # Salva conversação
    conversation_file = agent.save_conversation()
    print(f"Conversação salva em: {conversation_file}")
    
    # Estatísticas de performance
    print("\n=== ESTATÍSTICAS DE PERFORMANCE ===")
    stats = log_manager.get_performance_stats()
    print(f"Total de prompts: {stats.get('total_prompts', 0)}")
    print(f"Tempo médio de execução: {stats.get('avg_execution_time', 0):.2f}s")
    print(f"Tokens médios de saída: {stats.get('avg_output_tokens', 0):.0f}")


def example_with_different_model():
    """
    Exemplo de como seria fácil trocar o modelo
    (implementação futura de outros modelos)
    """
    # No futuro, você poderia fazer:
    # from openai_llm import OpenAILLM
    # from claude_llm import ClaudeLLM
    
    # openai_model = OpenAILLM("gpt-4", api_key="your-key")
    # agent = LLMAgent(openai_model, "AgentOpenAI")
    
    # claude_model = ClaudeLLM("claude-3-opus", api_key="your-key")
    # agent = LLMAgent(claude_model, "AgentClaude")
    
    print("Facilmente extensível para outros modelos!")


if __name__ == "__main__":
    main()
    example_with_different_model()