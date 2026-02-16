from langchain_anthropic import ChatAnthropic
from src.config import settings

def get_anthropic_model(model_name: str = "claude-3-opus-20240229", temperature: float = 0):
    return ChatAnthropic(
        model=model_name,
        temperature=temperature,
        anthropic_api_key=settings.ANTHROPIC_API_KEY
    )
