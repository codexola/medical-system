import hashlib
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.media import StoredAsset

settings = get_settings()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
MAX_PROFILE_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PLATFORM_ASSET_BYTES = 15 * 1024 * 1024


class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def asset_url(asset_id: uuid.UUID) -> str:
        return f"{settings.API_PREFIX}/media/{asset_id}"

    async def store(
        self,
        data: bytes,
        mime_type: str,
        filename: str,
        category: str,
        slug: Optional[str] = None,
        owner_user_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        max_bytes: int = MAX_PLATFORM_ASSET_BYTES,
    ) -> StoredAsset:
        if len(data) > max_bytes:
            raise ValueError(f"File exceeds maximum size of {max_bytes} bytes")
        if category == "profile_photo" and mime_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Profile photo must be JPEG, PNG, or WebP")
        if category == "platform_image" and mime_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Invalid image type")

        checksum = self.checksum(data)

        if slug:
            existing = await self.get_by_slug(slug)
            if existing:
                if existing.checksum_sha256 == checksum:
                    return existing
                existing.data = data
                existing.mime_type = mime_type
                existing.filename = filename
                existing.size_bytes = len(data)
                existing.checksum_sha256 = checksum
                existing.description = description
                await self.db.flush()
                return existing

        asset = StoredAsset(
            slug=slug,
            category=category,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(data),
            checksum_sha256=checksum,
            data=data,
            owner_user_id=owner_user_id,
            description=description,
        )
        self.db.add(asset)
        await self.db.flush()
        return asset

    async def get(self, asset_id: uuid.UUID) -> Optional[StoredAsset]:
        result = await self.db.execute(select(StoredAsset).where(StoredAsset.id == asset_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[StoredAsset]:
        result = await self.db.execute(select(StoredAsset).where(StoredAsset.slug == slug))
        return result.scalar_one_or_none()

    async def verify(self, asset: StoredAsset) -> bool:
        return self.checksum(asset.data) == asset.checksum_sha256

    async def store_profile_photo(
        self, user_id: uuid.UUID, data: bytes, mime_type: str, filename: str
    ) -> StoredAsset:
        return await self.store(
            data=data,
            mime_type=mime_type,
            filename=filename,
            category="profile_photo",
            owner_user_id=user_id,
            max_bytes=MAX_PROFILE_PHOTO_BYTES,
        )
