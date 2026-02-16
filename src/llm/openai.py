from langchain_openai import ChatOpenAI
from src.config import settings

def get_openai_model(model_name: str = "gpt-4-turbo-preview", temperature: float = 0):
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=settings.OPENAI_API_KEY
    )
