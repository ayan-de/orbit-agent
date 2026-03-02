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

    # Tavily Settings (Web Search)
    TAVILY_API_KEY: Optional[str] = None  # Tavily API key for web search
    TAVILY_MAX_RESULTS: int = 10  # Default max results for search
    TAVILY_SEARCH_DEPTH: str = "basic"  # Search depth: basic or advanced
    TAVILY_TIMEOUT: int = 30  # Tavily API timeout in seconds

    # MCP Settings (Model Context Protocol)
    MCP_SERVERS_ENABLED: bool = True  # Enable MCP server connections
    MCP_SERVER_TIMEOUT: int = 30  # MCP server connection timeout
    MCP_TAVILY_SERVER_URL: str = "sse://tavily-mcp-server"  # Tavily MCP server endpoint

    # Frontend Settings
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
