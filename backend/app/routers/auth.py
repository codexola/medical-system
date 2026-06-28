from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Header, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import LoginRequest, TokenResponse, UserProfile, UserUpdate
from app.database.session import get_db
from app.models import AdminUser, User
from app.services.auth import AuthService
from app.services.media import ALLOWED_IMAGE_TYPES, MediaService

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _user_profile(user: User) -> UserProfile:
    photo_url = MediaService.asset_url(user.profile_photo_id) if user.profile_photo_id else None
    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        preferred_language=user.preferred_language,
        address=user.address,
        job_function=user.job_function,
        profile_photo_id=user.profile_photo_id,
        profile_photo_url=photo_url,
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    home_address: str = Form(...),
    job_function: str = Form(...),
    profile_photo: UploadFile = File(...),
    phone: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if profile_photo.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Profile photo must be JPEG, PNG, or WebP")

    photo_data = await profile_photo.read()
    if not photo_data:
        raise HTTPException(status_code=400, detail="Profile photo is required")

    auth = AuthService(db)
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await auth.register_patient(email, password, name, home_address, job_function, phone)

    media_svc = MediaService(db)
    try:
        asset = await media_svc.store_profile_photo(
            user.id,
            photo_data,
            profile_photo.content_type or "image/jpeg",
            profile_photo.filename or "profile.jpg",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user.profile_photo_id = asset.id
    await db.flush()

    token = auth.create_access_token(str(user.id))
    return TokenResponse(access_token=token, user_id=str(user.id), role="patient")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    staff = await auth.authenticate_admin(data.email, data.password)
    if staff:
        token = auth.create_access_token(str(staff.id), role=staff.role)
        return TokenResponse(access_token=token, user_id=str(staff.id), role=staff.role)

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not auth.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token(str(user.id), role="patient")
    return TokenResponse(access_token=token, user_id=str(user.id), role="patient")


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    admin = await auth.authenticate_admin(data.email, data.password)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token(str(admin.id), role=admin.role)
    return TokenResponse(access_token=token, user_id=str(admin.id), role=admin.role)


@router.post("/developer/login", response_model=TokenResponse)
async def developer_login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    developer = await auth.authenticate_admin(data.email, data.password)
    if not developer or developer.role != "developer":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token(str(developer.id), role=developer.role)
    return TokenResponse(access_token=token, user_id=str(developer.id), role=developer.role)


@router.get("/staff/me")
async def staff_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = AuthService.verify_token(token)
    if not payload or payload.get("role") not in ("developer", "admin"):
        raise HTTPException(status_code=401, detail="Staff token required")
    result = await db.execute(select(AdminUser).where(AdminUser.id == UUID(payload["sub"])))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=401, detail="Staff account not found")
    return {
        "id": str(staff.id),
        "email": staff.email,
        "name": staff.name,
        "role": staff.role,
    }


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    return _user_profile(user)


@router.patch("/me", response_model=UserProfile)
async def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updates = data.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != user.email:
        existing = await db.execute(select(User).where(User.email == updates["email"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    if "address" in updates and updates["address"]:
        from app.services.google_maps import GoogleMapsService

        geo = await GoogleMapsService().geocode(updates["address"])
        if geo:
            updates["address"] = geo["formatted_address"]
            user.latitude = geo["latitude"]
            user.longitude = geo["longitude"]

    for field, value in updates.items():
        setattr(user, field, value)
    await db.flush()
    return _user_profile(user)
