from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from src.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Only log SQL in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=20,  # Number of connections to keep in pool
    max_overflow=10,  # Allow pool to grow by this many connections
)

# Create async session factory
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database connection pool."""
    # Test connection
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for getting database sessions.

    Use as a FastAPI dependency:
        @app.get("/sessions")
        async def get_sessions(db: AsyncSession = Depends(get_db)):
            repo = SessionRepository(db)
            sessions = await repo.get_active_sessions(user_id="user123")
            return sessions
    """
    async with async_session() as session:
        yield session


async def get_session() -> AsyncSession:
    """
    Get a new database session (for non-FastAPI contexts).

    Returns:
        AsyncSession instance

    Note:
        The caller is responsible for closing the session.
        Prefer get_db() for FastAPI routes.
    """
    async_session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session_local()
