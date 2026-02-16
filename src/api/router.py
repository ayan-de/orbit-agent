from fastapi import APIRouter
from src.api.v1 import agent, health

api_router = APIRouter()

# Placeholder for actual routes
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
