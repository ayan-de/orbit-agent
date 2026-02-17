from src.config import settings
from .openai import get_openai_model
from .anthropic import get_anthropic_model
from .gemini import get_gemini_model

def llm_factory(provider: str = None, model_name: str = None, temperature: float = 0):
    """
    Factory function to create LLM instances based on the provider.
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    
    if provider == "openai":
        return get_openai_model(model_name or "gpt-4-turbo-preview", temperature)
    elif provider == "anthropic":
        return get_anthropic_model(model_name or "claude-3-opus-20240229", temperature)
    elif provider == "gemini":
        return get_gemini_model(model_name or "gemini-flash-latest", temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
