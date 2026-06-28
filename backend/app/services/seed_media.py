"""Seed platform images and materials into the database."""

import mimetypes
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import StoredAsset
from app.services.media import MediaService

# Map filename (without extension) to slug used by frontend
PLATFORM_IMAGE_SLUGS = {
    "bright-hero": "bright-hero",
    "bright-mascot": "bright-mascot",
    "bright-dashboard-greeting": "bright-dashboard-greeting",
    "bright-doctor": "bright-doctor",
    "bright-patient-hope": "bright-patient-hope",
    "bright-consultation": "bright-consultation",
    "bright-team": "bright-team",
    "bright-recovery": "bright-recovery",
    "bright-feature-chat": "bright-feature-chat",
    "bright-feature-rag": "bright-feature-rag",
    "bright-feature-reservation": "bright-feature-reservation",
    "bright-feature-hospital": "bright-feature-hospital",
    "bright-feature-health": "bright-feature-health",
    "bright-usage-line": "bright-usage-line",
    "bright-usage-booking": "bright-usage-booking",
    "bright-login": "bright-login",
    "bright-hospital": "bright-hospital",
    "bright-pricing": "bright-pricing",
    "bright-symptom": "bright-symptom",
    "bright-bg-pattern": "bright-bg-pattern",
    "hero-healthcare": "hero-healthcare",
    "hospital-search": "hospital-search",
    "health-timeline": "health-timeline",
    "ai-receptionist": "ai-receptionist",
    "japanese-pattern": "japanese-pattern",
    "login-bg": "login-bg",
    "hospital-banner": "hospital-banner",
    "medical-devices": "medical-devices",
    "feature-health": "feature-health",
    "feature-hospital": "feature-hospital",
    "feature-ai-chat": "feature-ai-chat",
    "feature-reservation": "feature-reservation",
    "feature-rag": "feature-rag",
    "usage-line": "usage-line",
    "usage-booking": "usage-booking",
    "pricing-hero": "pricing-hero",
    "dashboard-hero": "dashboard-hero",
    "symptom-check": "symptom-check",
    "ai-mascot": "ai-mascot",
}


async def seed_platform_images(db: AsyncSession, images_dir: Path) -> int:
    """Import all images from frontend/public/images into stored_assets."""
    if not images_dir.is_dir():
        return 0

    media = MediaService(db)
    count = 0

    for path in sorted(images_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"):
            continue

        stem = path.stem
        slug = PLATFORM_IMAGE_SLUGS.get(stem, stem)
        mime_type, _ = mimetypes.guess_type(path.name)
        if not mime_type:
            mime_type = "image/jpeg"

        data = path.read_bytes()
        if not data:
            continue

        existing = await db.execute(select(StoredAsset).where(StoredAsset.slug == slug))
        if existing.scalar_one_or_none():
            await media.store(
                data=data,
                mime_type=mime_type,
                filename=path.name,
                category="platform_image",
                slug=slug,
                description=f"Platform image: {slug}",
            )
        else:
            await media.store(
                data=data,
                mime_type=mime_type,
                filename=path.name,
                category="platform_image",
                slug=slug,
                description=f"Platform image: {slug}",
            )
        count += 1

    return count
