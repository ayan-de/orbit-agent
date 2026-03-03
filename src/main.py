from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.api.router import api_router
from src.config import settings
from src.mcp.client import get_mcp_client, MCPClientManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    print("🚀 Orbit Agent starting up...")
    print(f"📍 Port: {settings.PORT}")
    print(f"🤖 Default LLM: {settings.DEFAULT_LLM_PROVIDER}")

    # Initialize MCP servers
    mcp_client = get_mcp_client()
    mcp_servers_initialized = False

    if settings.MCP_SERVERS_ENABLED:
        print("🔌 Initializing MCP servers...")
        try:
            mcp_servers_initialized = await mcp_client.initialize_servers()
            if mcp_servers_initialized:
                print("✅ MCP servers initialized successfully")
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
        "mcp_servers": "initialized" if mcp_servers_initialized else "not_configured"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
