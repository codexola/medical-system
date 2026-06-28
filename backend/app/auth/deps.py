from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models import AdminUser
from app.services.auth import AuthService


class StaffRole(str, Enum):
    DEVELOPER = "developer"
    ADMIN = "admin"


class AccountType(str, Enum):
    PATIENT = "patient"
    ADMIN = "admin"
    DEVELOPER = "developer"


async def _get_token_payload(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


async def get_current_staff(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    payload = await _get_token_payload(authorization)
    role = payload.get("role", "")
    if role not in (StaffRole.DEVELOPER.value, StaffRole.ADMIN.value):
        raise HTTPException(status_code=403, detail="Staff access required")
    result = await db.execute(select(AdminUser).where(AdminUser.id == UUID(payload["sub"])))
    staff = result.scalar_one_or_none()
    if not staff or not staff.is_active:
        raise HTTPException(status_code=401, detail="Staff account not found")
    return staff


async def require_developer(staff: AdminUser = Depends(get_current_staff)) -> AdminUser:
    if staff.role != StaffRole.DEVELOPER.value:
        raise HTTPException(status_code=403, detail="Developer access required")
    return staff


async def require_admin(staff: AdminUser = Depends(get_current_staff)) -> AdminUser:
    if staff.role != StaffRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return staff


async def require_admin_or_developer(staff: AdminUser = Depends(get_current_staff)) -> AdminUser:
    return staff
