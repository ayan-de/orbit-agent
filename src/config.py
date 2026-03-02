from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    PORT: int = 8000
    DEBUG: bool = True
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GLM_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_LLM_MODEL: Optional[str] = None
    
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/orbit_agent"
    
    # Bridge Settings
    BRIDGE_URL: str = "http://localhost:3001"
    BRIDGE_API_KEY: Optional[str] = None

    # Gmail OAuth Settings
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REDIRECT_URI: str = "http://localhost:3001/auth/gmail/callback"
    GMAIL_SCOPES: list[str] = ["https://www.googleapis.com/auth/gmail.send"]

    # Email Settings
    ENCRYPTION_KEY: Optional[str] = None  # For token encryption
    TOKEN_STORAGE_PATH: str = "data/tokens.json"
    EMAIL_MAX_SIZE_MB: int = 25
    EMAIL_RATE_LIMIT: int = 10  # Max emails per hour per user

    # Jira Settings
    JIRA_TIMEOUT: int = 30  # Jira API timeout in seconds

    # Frontend Settings
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
