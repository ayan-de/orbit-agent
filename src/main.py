from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from src.api.router import api_router
from src.config import settings
from src.mcp.client import get_mcp_client, MCPClientManager
from src.middleware import (
    register_exception_handlers,
    AuthMiddleware,
    setup_rate_limiting,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global state for health check
mcp_servers_initialized = False
mcp_tools_registered = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global mcp_servers_initialized, mcp_tools_registered

    print("🚀 Orbit Agent starting up...")
    print(f"📍 Port: {settings.PORT}")
    print(f"🤖 Default LLM: {settings.DEFAULT_LLM_PROVIDER}")

    # Initialize MCP servers
    mcp_client = get_mcp_client()

    if settings.MCP_SERVERS_ENABLED:
        print("🔌 Initializing MCP servers...")
        try:
            mcp_servers_initialized = await mcp_client.initialize_servers()
            if mcp_servers_initialized:
                print("✅ MCP servers initialized successfully")

                # Phase 1: Register MCP tools with IntegrationRegistry
                print("📦 Registering MCP tools with IntegrationRegistry...")
                try:
                    from src.integrations.registry import get_registry
                    registry = await get_registry()
                    mcp_tools_registered = mcp_client.register_tools_with_integration_registry(registry)
                    print(f"✅ Registered {mcp_tools_registered} MCP tools")
                except Exception as e:
                    print(f"⚠️  Failed to register MCP tools: {e}")

            else:
                print("⚠️  No MCP servers configured")
        except Exception as e:
            print(f"❌ MCP initialization failed: {e}")
            mcp_servers_initialized = False

    yield

    # Shutdown MCP servers
    if mcp_servers_initialized:
        print("🔌 Shutting down MCP servers...")
        try:
            await mcp_client.shutdown_servers()
            print("✅ MCP servers shut down")
        except Exception as e:
            print(f"❌ MCP shutdown failed: {e}")

    print("🛑 Orbit Agent shutting down...")


app = FastAPI(
    title="Orbit AI Agent",
    description="Python microservice for Orbit AI Agent with LangGraph",
    version="0.1.0",
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# Setup rate limiting
setup_rate_limiting(app)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Root health check
@app.get("/")
async def root():
    return {
        "service": "Orbit AI Agent",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "mcp_servers": "initialized" if mcp_servers_initialized else "not_configured",
        "mcp_tools": mcp_tools_registered,
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
