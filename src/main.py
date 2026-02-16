from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from src.api.router import api_router
from src.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    print("🚀 Orbit Agent starting up...")
    print(f"📍 Port: {settings.PORT}")
    print(f"🤖 Default LLM: {settings.DEFAULT_LLM_PROVIDER}")
    yield
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
        "llm_provider": settings.DEFAULT_LLM_PROVIDER
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
