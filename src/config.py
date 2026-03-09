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

    # Token Storage (for OAuth integrations)
    ENCRYPTION_KEY: Optional[str] = None  # For token encryption
    TOKEN_STORAGE_PATH: str = "data/tokens.json"

    # Tavily Settings (Web Search)
    TAVILY_API_KEY: Optional[str] = None  # Tavily API key for web search
    TAVILY_MAX_RESULTS: int = 10  # Default max results for search
    TAVILY_SEARCH_DEPTH: str = "basic"  # Search depth: basic or advanced
    TAVILY_TIMEOUT: int = 30  # Tavily API timeout in seconds

    # MCP Settings (Model Context Protocol)
    MCP_SERVERS_ENABLED: bool = True  # Enable MCP server connections
    MCP_SERVER_TIMEOUT: int = 30  # MCP server connection timeout
    MCP_SERVERS: dict = {}  # MCP server configurations by name

    # Google Workspace MCP Settings (for future MCP integrations)
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None  # Google OAuth Client ID
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None  # Google OAuth Client Secret
    OAUTHLIB_INSECURE_TRANSPORT: str = "1"  # Allow HTTP transport for OAuth
    MCP_ENABLE_OAUTH21: bool = False  # Enable OAuth 2.1 mode for multi-user
    EXTERNAL_OAUTH21_PROVIDER: bool = False  # External OAuth provider mode
    WORKSPACE_MCP_BASE_URI: str = "http://localhost"  # MCP server base URI
    WORKSPACE_MCP_PORT: str = "8000"  # MCP server port
    WORKSPACE_MCP_HOST: str = "0.0.0.0"  # MCP server host

    # Frontend Settings
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
