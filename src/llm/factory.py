from src.config import settings
from .openai import get_openai_model
from .anthropic import get_anthropic_model
from .gemini import get_gemini_model
from .glm import get_glm_model

def llm_factory(provider: str = None, model_name: str = None, temperature: float = 0):
    """
    Factory function to create LLM instances based on the provider.
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER

    if provider == "openai":
        default_model = "gpt-4-turbo-preview"
        return get_openai_model(model_name or settings.DEFAULT_LLM_MODEL or default_model, temperature)
    elif provider == "anthropic":
        default_model = "claude-3-opus-20240229"
        return get_anthropic_model(model_name or settings.DEFAULT_LLM_MODEL or default_model, temperature)
    elif provider == "gemini":
        default_model = "gemini-2.5-flash"
        return get_gemini_model(model_name or settings.DEFAULT_LLM_MODEL or default_model, temperature)
    elif provider == "glm":
        default_model = "glm-4.5"
        return get_glm_model(model_name or settings.DEFAULT_LLM_MODEL or default_model, temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
