#!/usr/bin/env python3
"""Seed platform images from frontend/public/images into the database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import AsyncSessionLocal
from app.services.seed_media import seed_platform_images


async def main():
    images_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "images"
    async with AsyncSessionLocal() as db:
        count = await seed_platform_images(db, images_dir)
        await db.commit()
        print(f"Seeded {count} images from {images_dir}")


if __name__ == "__main__":
    asyncio.run(main())
