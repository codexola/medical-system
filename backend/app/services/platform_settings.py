from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import AuditLog, PlatformSetting

DEFAULT_SETTINGS: list[dict[str, Any]] = [
    {
        "key": "ai.default_provider",
        "category": "ai",
        "description": "Default AI provider (openai, anthropic)",
        "value": {"provider": "openai", "model": "gpt-4o"},
    },
    {
        "key": "ai.temperature",
        "category": "ai",
        "description": "Default AI temperature",
        "value": {"temperature": 0.7},
    },
    {
        "key": "subscription.trial_days",
        "category": "subscription",
        "description": "Free trial duration in days",
        "value": {"days": 7},
    },
    {
        "key": "features.line_enabled",
        "category": "features",
        "description": "Enable LINE Messaging API integration",
        "value": {"enabled": True},
    },
    {
        "key": "features.rag_enabled",
        "category": "features",
        "description": "Enable RAG knowledge base",
        "value": {"enabled": True},
    },
    {
        "key": "features.hospital_search_enabled",
        "category": "features",
        "description": "Enable hospital search and recommendation",
        "value": {"enabled": True},
    },
    {
        "key": "features.health_timeline_enabled",
        "category": "features",
        "description": "Enable health check-in timeline",
        "value": {"enabled": True},
    },
    {
        "key": "platform.maintenance_mode",
        "category": "platform",
        "description": "Maintenance mode — blocks patient registration",
        "value": {"enabled": False, "message": ""},
    },
    {
        "key": "platform.default_language",
        "category": "platform",
        "description": "Default platform language",
        "value": {"language": "ja"},
    },
    {
        "key": "notifications.daily_checkin",
        "category": "notifications",
        "description": "Send daily health check-in prompts",
        "value": {"enabled": True, "hour": 8},
    },
]


class PlatformSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_defaults(self) -> None:
        for item in DEFAULT_SETTINGS:
            existing = await self.db.execute(
                select(PlatformSetting).where(PlatformSetting.key == item["key"])
            )
            if not existing.scalar_one_or_none():
                self.db.add(
                    PlatformSetting(
                        key=item["key"],
                        value=item["value"],
                        category=item["category"],
                        description=item["description"],
                    )
                )
        await self.db.flush()

    async def get_all(self, category: Optional[str] = None) -> list[PlatformSetting]:
        query = select(PlatformSetting)
        if category:
            query = query.where(PlatformSetting.category == category)
        query = query.order_by(PlatformSetting.category, PlatformSetting.key)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, key: str) -> Optional[PlatformSetting]:
        result = await self.db.execute(select(PlatformSetting).where(PlatformSetting.key == key))
        return result.scalar_one_or_none()

    async def get_value(self, key: str, default: Any = None) -> Any:
        setting = await self.get(key)
        if not setting:
            return default
        return setting.value

    async def update(self, key: str, value: dict, updated_by: UUID) -> PlatformSetting:
        setting = await self.get(key)
        if not setting:
            raise ValueError(f"Setting not found: {key}")
        setting.value = value
        setting.updated_by = updated_by
        await self.db.flush()
        return setting

    async def log_action(
        self,
        actor_id: UUID,
        actor_email: str,
        actor_role: str,
        action: str,
        resource: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor_id,
                actor_email=actor_email,
                actor_role=actor_role,
                action=action,
                resource=resource,
                details=details,
            )
        )
        await self.db.flush()
