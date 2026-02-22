from langchain_openai import ChatOpenAI
from src.config import settings

def get_glm_model(model_name: str = "glm-4.5", temperature: float = 0.01):
    """
    Get ZhipuAI/GLM model via the OpenAI compatible endpoint.
    Temperature must be > 0
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature if temperature > 0 else 0.01,
        api_key=settings.GLM_API_KEY,
        base_url="https://api.z.ai/api/coding/paas/v4/"
    )
