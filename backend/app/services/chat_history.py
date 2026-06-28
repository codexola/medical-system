"""Chat history: patient dashboard clear (soft) vs staff hard delete."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationMemory, Message, User


class ChatHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _history_query(user_id: UUID, channel: str | None = "web", after: datetime | None = None):
        q = select(Message).where(Message.user_id == user_id)
        if channel:
            q = q.where(Message.channel == channel)
        if after:
            q = q.where(Message.created_at > after)
        return q.order_by(Message.created_at.asc())

    async def list_for_user(
        self,
        user: User,
        *,
        channel: str = "web",
        limit: int = 100,
    ) -> list[Message]:
        after = user.chat_cleared_at if channel == "web" else None
        result = await self.db.execute(
            self._history_query(user.id, channel, after).limit(min(limit, 200))
        )
        return list(result.scalars().all())

    async def clear_for_patient_dashboard(self, user: User) -> None:
        """Hide web chat from patient dashboard; rows remain until staff hard-deletes."""
        user.chat_cleared_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def hard_delete_for_user(self, user_id: UUID) -> dict:
        """Permanently remove messages and conversation memory (admin/developer only)."""
        msg_count = await self.db.scalar(
            select(func.count(Message.id)).where(Message.user_id == user_id)
        )
        mem_count = await self.db.scalar(
            select(func.count(ConversationMemory.id)).where(ConversationMemory.user_id == user_id)
        )

        await self.db.execute(delete(Message).where(Message.user_id == user_id))
        await self.db.execute(delete(ConversationMemory).where(ConversationMemory.user_id == user_id))

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.chat_cleared_at = None

        await self.db.flush()
        return {
            "deleted_messages": msg_count or 0,
            "deleted_memories": mem_count or 0,
            "user_id": str(user_id),
        }

    async def message_count(self, user_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(Message.id)).where(Message.user_id == user_id)
        ) or 0
