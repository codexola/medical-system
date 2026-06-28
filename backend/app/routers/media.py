from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.services.media import ALLOWED_IMAGE_TYPES, MediaService

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{asset_id}")
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = MediaService(db)
    asset = await svc.get(asset_id)
    if not asset or not await svc.verify(asset):
        raise HTTPException(status_code=404, detail="Asset not found or corrupted")
    return Response(
        content=asset.data,
        media_type=asset.mime_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{asset.filename}"',
            "X-Checksum-SHA256": asset.checksum_sha256,
        },
    )


@router.get("/slug/{slug}")
async def get_asset_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    svc = MediaService(db)
    asset = await svc.get_by_slug(slug)
    if not asset or not await svc.verify(asset):
        raise HTTPException(status_code=404, detail="Asset not found")
    return Response(
        content=asset.data,
        media_type=asset.mime_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{asset.filename}"',
            "X-Checksum-SHA256": asset.checksum_sha256,
        },
    )


@router.post("/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type. Use JPEG, PNG, or WebP.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    svc = MediaService(db)
    try:
        asset = await svc.store_profile_photo(
            user.id, data, file.content_type or "image/jpeg", file.filename or "photo.jpg"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user.profile_photo_id = asset.id
    await db.flush()
    return {
        "id": str(asset.id),
        "url": svc.asset_url(asset.id),
        "checksum": asset.checksum_sha256,
    }
