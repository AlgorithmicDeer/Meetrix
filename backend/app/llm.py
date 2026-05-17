"""
LLM factory function - the ONLY place ChatOllama instances are created.
All graph nodes call get_llm() to obtain configured LLM instances.
"""
from langchain_ollama import ChatOllama
from app.config import settings


def get_llm(model_name: str, temperature: float = 0.1) -> ChatOllama:
    """
    Create a configured ChatOllama instance.
    
    Args:
        model_name: Ollama model name (e.g., "llama3.2")
        temperature: Generation temperature (0.0-1.0)
            - 0.0: Deterministic (classification, extraction)
            - 0.3: Slightly creative (health scoring, interventions)
            - 0.5: Balanced (narratives, queries, scheduling)
    
    Returns:
        Configured ChatOllama instance
    """
    return ChatOllama(
        model=model_name,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature,
        num_ctx=4096,  # Context window (Ollama default 2048 is too small)
        num_predict=2048,  # Max tokens to generate
        keep_alive="5m",  # Keep model loaded between calls
    )

# Made with Bob
