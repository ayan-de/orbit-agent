"""
Conversation Memory service for Orbit AI Agent.

Manages conversation history, context, and summarization.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import UUID

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage
)

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, Message, MessageRole
from src.db.repositories import SessionRepository, MessageRepository
from src.db.engine import get_session
from src.llm.factory import llm_factory


class ConversationMemory:
    """
    Manages conversation memory and context.

    Handles storing, retrieving, and summarizing conversations.
    """

    def __init__(self, db_session: AsyncSession = None):
        """
        Initialize conversation memory.

        Args:
            db_session: Async SQLAlchemy session (optional)
        """
        self.db_session = db_session
        self.session_repo = SessionRepository(db_session)
        self.message_repo = MessageRepository(db_session)

    async def _get_db_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return await get_session().__anext__()

    async def create_session(
        self,
        user_id: str,
        title: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new conversation session.

        Args:
            user_id: User identifier
            title: Optional session title
            meta: Optional metadata dictionary

        Returns:
            Created session
        """
        session = await self._get_db_session()

        try:
            new_session = await self.session_repo.create(
                user_id=user_id,
                title=title,
                status="active",
                meta=meta or {}
            )
            await session.commit()
            return new_session
        except Exception as e:
            await session.rollback()
            raise e

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session UUID as string

        Returns:
            Session or None
        """
        session = await self._get_db_session()
        return await self.session_repo.get_by_id(session_id)

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        meta: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to the conversation.

        Args:
            session_id: Session UUID as string
            role: Message role (user, assistant, system, tool)
            content: Message content
            meta: Optional metadata

        Returns:
            Created message
        """
        session = await self._get_db_session()

        try:
            message = await self.message_repo.create(
                session_id=session_id,
                role=role,
                content=content,
                meta=meta or {}
            )
            await session.commit()
            return message
        except Exception as e:
            await session.rollback()
            raise e

    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        before: Optional[datetime] = None
    ) -> List[Message]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session UUID as string
            limit: Maximum number of messages to return
            before: Get messages before this timestamp

        Returns:
            List of messages
        """
        session_db = await self._get_db_session()

        try:
            messages = await self.message_repo.get_conversation(
                session_id=session_id,
                limit=limit,
                before=before
            )
            return messages
        except Exception as e:
            await session_db.rollback()
            raise e

    async def get_messages_for_llm(
        self,
        session_id: str,
        include_system: bool = True,
        max_messages: int = 50
    ) -> List[BaseMessage]:
        """
        Get messages formatted for LLM consumption.

        Args:
            session_id: Session UUID as string
            include_system: Whether to include system messages
            max_messages: Maximum number of messages (from most recent)

        Returns:
            List of LangChain messages
        """
        messages_db = await self.get_conversation_history(
            session_id=session_id,
            limit=max_messages
        )

        langchain_messages = []
        for msg in messages_db:
            if not include_system and msg.role == MessageRole.SYSTEM:
                continue

            if msg.role == MessageRole.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.TOOL:
                langchain_messages.append(ToolMessage(content=msg.content))

        return langchain_messages

    async def get_context_window(
        self,
        session_id: str,
        max_tokens: int = 8000
    ) -> Tuple[List[BaseMessage], int]:
        """
        Get messages that fit within a token budget.

        Uses a simple estimation (roughly 4 chars per token).

        Args:
            session_id: Session UUID as string
            max_tokens: Maximum tokens to include

        Returns:
            Tuple of (messages, token_count)
        """
        messages_db = await self.get_conversation_history(session_id=session_id)
        messages_db.reverse()  # Get most recent first

        selected_messages = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars

        for msg in messages_db:
            msg_chars = len(msg.content)
            if total_chars + msg_chars > max_chars:
                break

            total_chars += msg_chars

            if msg.role == MessageRole.USER:
                selected_messages.insert(0, HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                selected_messages.insert(0, AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                selected_messages.insert(0, SystemMessage(content=msg.content))
            elif msg.role == MessageRole.TOOL:
                selected_messages.insert(0, ToolMessage(content=msg.content))

        estimated_tokens = total_chars // 4
        return selected_messages, estimated_tokens

    async def summarize_conversation(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> Optional[str]:
        """
        Summarize a long conversation.

        Uses LLM to create a concise summary of the conversation.

        Args:
            session_id: Session UUID as string
            max_messages: Maximum number of messages to summarize

        Returns:
            Conversation summary or None
        """
        messages = await self.get_messages_for_llm(
            session_id=session_id,
            max_messages=max_messages
        )

        if not messages:
            return None

        # Use LLM to summarize
        llm = llm_factory(temperature=0.3)

        prompt = f"""You are a conversation summarizer. Create a concise summary of this conversation.

The summary should:
- Capture the main topics and themes discussed
- Highlight key questions and answers
- Note any important decisions or conclusions
- Be 2-3 paragraphs maximum

Conversation:
{self._format_messages_for_summary(messages)}

Summary:"""

        try:
            from langchain_core.messages import HumanMessage
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            # Return None if summarization fails
            return None

    def _format_messages_for_summary(self, messages: List[BaseMessage]) -> str:
        """
        Format messages for summarization.

        Args:
            messages: List of LangChain messages

        Returns:
            Formatted string
        """
        formatted = []
        for msg in messages:
            role = msg.type
            content = msg.content
            formatted.append(f"{role.upper()}: {content}")
        return "\n\n".join(formatted)

    async def summarize_and_compress(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> List[BaseMessage]:
        """
        Summarize conversation and replace old messages with summary.

        Compresses old messages into a single system message summary,
        keeping recent messages intact.

        Args:
            session_id: Session UUID as string
            max_messages: Maximum messages to summarize

        Returns:
            Updated message list (summary + recent messages)
        """
        # Get all messages
        all_messages = await self.get_conversation_history(session_id=session_id)

        if len(all_messages) <= max_messages:
            # No need to compress
            return await self.get_messages_for_llm(session_id=session_id)

        # Summarize older messages
        older_messages = all_messages[:-max_messages]
        recent_messages = all_messages[-max_messages:]

        # Convert to LangChain format
        older_langchain = []
        for msg in older_messages:
            if msg.role == MessageRole.USER:
                older_langchain.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                older_langchain.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM:
                older_langchain.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.TOOL:
                older_langchain.append(ToolMessage(content=msg.content))

        # Generate summary
        summary = await self.summarize_conversation(
            session_id=session_id,
            max_messages=len(older_messages)
        )

        if not summary:
            return await self.get_messages_for_llm(session_id=session_id)

        # Replace old messages with summary
        session = await self._get_db_session()

        try:
            # Delete old messages
            for msg in older_messages:
                await self.message_repo.delete(msg.id)

            # Add summary as system message
            await self.message_repo.create(
                session_id=session_id,
                role=MessageRole.SYSTEM,
                content=f"Conversation Summary: {summary}",
                meta={"is_summary": True}
            )

            await session.commit()

            # Return updated messages
            return await self.get_messages_for_llm(session_id=session_id)

        except Exception as e:
            await session.rollback()
            raise e

    async def search_conversations(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Tuple[Session, List[Message]]]:
        """
        Search conversations by content.

        Args:
            user_id: User identifier
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of (session, messages) tuples
        """
        session_db = await self._get_db_session()

        try:
            # Search messages by content
            matching_messages = await self.message_repo.search_by_content(
                query=query,
                limit=limit * 5  # Get more to filter by user
            )

            # Filter by user_id and deduplicate by session
            seen_sessions = set()
            results = []

            for msg in matching_messages:
                if msg.session_id in seen_sessions:
                    continue

                # Get session to verify user_id
                session_obj = await self.session_repo.get_by_id(str(msg.session_id))
                if not session_obj or session_obj.user_id != user_id:
                    continue

                seen_sessions.add(msg.session_id)
                results.append((session_obj, [msg]))

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            await session_db.rollback()
            raise e

    async def get_recent_sessions(
        self,
        user_id: str,
        limit: int = 10,
        days: int = 7
    ) -> List[Session]:
        """
        Get recent sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum sessions to return
            days: Days to look back

        Returns:
            List of recent sessions
        """
        session_db = await self._get_db_session()

        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            sessions = await self.session_repo.get_recent_sessions(
                user_id=user_id,
                limit=limit,
                since_date=since_date
            )
            return sessions
        except Exception as e:
            await session_db.rollback()
            raise e

    async def update_session_title(
        self,
        session_id: str,
        title: str
    ) -> Session:
        """
        Update session title.

        Args:
            session_id: Session UUID as string
            title: New title

        Returns:
            Updated session
        """
        session_db = await self._get_db_session()

        try:
            updated_session = await self.session_repo.update(
                session_id=session_id,
                title=title
            )
            await session_db.commit()
            return updated_session
        except Exception as e:
            await session_db.rollback()
            raise e

    async def archive_session(
        self,
        session_id: str
    ) -> Session:
        """
        Archive a session (mark as archived).

        Args:
            session_id: Session UUID as string

        Returns:
            Archived session
        """
        session_db = await self._get_db_session()

        try:
            archived_session = await self.session_repo.archive(session_id)
            await session_db.commit()
            return archived_session
        except Exception as e:
            await session_db.rollback()
            raise e

    async def delete_session(
        self,
        session_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session UUID as string
            soft_delete: If True, soft delete (set status to deleted)

        Returns:
            True if successful
        """
        session_db = await self._get_db_session()

        try:
            if soft_delete:
                await self.session_repo.soft_delete(session_id)
            else:
                await self.session_repo.delete(session_id)
            await session_db.commit()
            return True
        except Exception as e:
            await session_db.rollback()
            raise e


# Global memory instance
_conversation_memory: Optional[ConversationMemory] = None


async def get_conversation_memory() -> ConversationMemory:
    """
    Get or create global conversation memory instance.

    Returns:
        Conversation memory instance
    """
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory


def reset_conversation_memory():
    """Reset global conversation memory instance (for testing)."""
    global _conversation_memory
    _conversation_memory = None
