# Database Patterns

## SQLAlchemy Async

Use async sessions throughout:

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.database_url)
async_session = sessionmaker(engine, class_=AsyncSession)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

## Repository Pattern

Encapsulate data access:

```python
from abc import ABC, abstractmethod

class MessageRepository(ABC):
    @abstractmethod
    async def create(self, session_id: str, content: str, role: str) -> Message:
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> list[Message]:
        pass

class SQLAlchemyMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, session_id: str, content: str, role: str) -> Message:
        message = Message(session_id=session_id, content=content, role=role)
        self.session.add(message)
        await self.session.commit()
        return message
```

## Migrations with Alembic

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Query Optimization

```python
# Use eager loading to avoid N+1
from sqlalchemy.orm import selectinload

query = select(Session).options(
    selectinload(Session.messages)
).where(Session.id == session_id)

# Use indexes for frequently queried columns
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True)
    session_id = Column(UUID, ForeignKey("sessions.id"), index=True)
    created_at = Column(DateTime, default=utcnow, index=True)
```

## Testing with Testcontainers

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
async def test_db():
    async with PostgresContainer("postgres:15") as postgres:
        # Create engine with test container URL
        engine = create_async_engine(postgres.get_connection_url())
        yield engine
```
