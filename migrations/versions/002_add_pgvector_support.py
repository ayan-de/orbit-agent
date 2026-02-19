"""Add pgvector extension and vector column for embeddings (Phase 4)

This migration enables vector similarity search for RAG functionality.

Revision ID: 002_add_pgvector
Revises: 001_initial_schema
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_add_pgvector"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add vector column to embeddings table
    # Default dimension is 1536 for OpenAI text-embedding-ada-002
    op.execute("ALTER TABLE embeddings ADD COLUMN embedding vector(1536)")

    # Create HNSW index for fast approximate vector search
    # Uses cosine distance (vector_cosine_ops) which is common for semantic search
    op.execute("""
        CREATE INDEX idx_embeddings_hnsw ON embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Add GIN index for metadata JSONB queries
    op.execute("CREATE INDEX idx_embeddings_metadata ON embeddings USING GIN (metadata)")

    # Add index for session_id (already exists, but ensuring it's there for vector queries with filtering)
    op.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_session ON embeddings (session_id)")


def downgrade() -> None:
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_embeddings_metadata")
    op.execute("DROP INDEX IF EXISTS idx_embeddings_session")

    # Drop vector column
    op.execute("ALTER TABLE embeddings DROP COLUMN IF EXISTS embedding")

    # Note: We don't drop the pgvector extension as it may be used by other tables
    # If you want to drop it, uncomment the following line:
    # op.execute("DROP EXTENSION IF EXISTS vector")
