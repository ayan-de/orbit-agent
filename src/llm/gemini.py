from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings

def get_gemini_model(model_name: str = "gemini-flash-lite-latest", temperature: float = 0):
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=settings.GOOGLE_API_KEY
    )
