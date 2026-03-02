from fastapi import APIRouter
from src.api.v1 import agent, health, sessions, email, jira

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(email.router, tags=["email"])
api_router.include_router(jira.router, tags=["jira"])
