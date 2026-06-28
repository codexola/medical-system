import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, User


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        channel: str = "line",
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            channel=channel,
            scheduled_at=scheduled_at,
            metadata_=metadata,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def send_line_notification(self, user: User, message: str) -> bool:
        if not user.line_user_id:
            return False
        from app.line.client import LineClient

        client = LineClient()
        return await client.push_message(user.line_user_id, message)

    async def get_user_notifications(
        self, user_id: uuid.UUID, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: uuid.UUID) -> None:
        result = await self.db.execute(select(Notification).where(Notification.id == notification_id))
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self.db.flush()
