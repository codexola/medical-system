from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_developer
from app.config import get_settings
from app.database.session import get_db
from app.models import AILog, AdminUser, Subscription, SubscriptionStatus, User
from app.models.platform import AuditLog
from app.services.chat_history import ChatHistoryService
from app.services.platform_settings import PlatformSettingsService

router = APIRouter(prefix="/developer", tags=["developer"])
settings = get_settings()


class SettingUpdate(BaseModel):
    value: dict


class BulkSettingsUpdate(BaseModel):
    settings: dict[str, dict]


@router.get("/dashboard")
async def developer_dashboard(
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    total_users = await db.scalar(select(func.count(User.id)))
    total_staff = await db.scalar(select(func.count(AdminUser.id)))
    active_subs = await db.scalar(
        select(func.count()).select_from(Subscription).where(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        )
    )
    total_ai_calls = await db.scalar(select(func.count(AILog.id)))
    total_tokens = await db.scalar(select(func.sum(AILog.total_tokens)))
    recent_audit = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
    )

    return {
        "platform": {"name": settings.APP_NAME, "version": settings.APP_VERSION},
        "stats": {
            "total_users": total_users or 0,
            "total_staff": total_staff or 0,
            "active_subscriptions": active_subs or 0,
            "total_ai_calls": total_ai_calls or 0,
            "total_tokens_used": total_tokens or 0,
        },
        "staff": {"email": staff.email, "name": staff.name, "role": staff.role},
        "recent_audit": [
            {
                "action": a.action,
                "resource": a.resource,
                "actor_email": a.actor_email,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_audit.scalars().all()
        ],
    }


@router.get("/settings")
async def list_settings(
    category: Optional[str] = None,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    svc = PlatformSettingsService(db)
    await svc.ensure_defaults()
    items = await svc.get_all(category)
    return [
        {
            "key": s.key,
            "value": s.value,
            "category": s.category,
            "description": s.description,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in items
    ]


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    data: SettingUpdate,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    svc = PlatformSettingsService(db)
    try:
        setting = await svc.update(key, data.value, staff.id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    await svc.log_action(staff.id, staff.email, staff.role, "update_setting", key, data.value)
    return {"key": setting.key, "value": setting.value, "updated": True}


@router.put("/settings")
async def bulk_update_settings(
    data: BulkSettingsUpdate,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    svc = PlatformSettingsService(db)
    updated = []
    for key, value in data.settings.items():
        try:
            setting = await svc.update(key, value, staff.id)
            updated.append(setting.key)
        except ValueError:
            continue
    await svc.log_action(staff.id, staff.email, staff.role, "bulk_update_settings", details={"keys": updated})
    return {"updated": updated}


@router.get("/usage")
async def usage_inspection(
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    ai_by_provider = await db.execute(
        select(AILog.provider, func.count(AILog.id), func.sum(AILog.total_tokens))
        .group_by(AILog.provider)
    )
    ai_by_model = await db.execute(
        select(AILog.model, func.count(AILog.id), func.sum(AILog.total_tokens))
        .group_by(AILog.model)
        .order_by(func.count(AILog.id).desc())
        .limit(10)
    )
    users_by_role = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    subs_by_plan = await db.execute(
        select(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan)
    )

    return {
        "ai_by_provider": [
            {"provider": r[0], "calls": r[1], "tokens": r[2] or 0} for r in ai_by_provider.all()
        ],
        "ai_by_model": [
            {"model": r[0], "calls": r[1], "tokens": r[2] or 0} for r in ai_by_model.all()
        ],
        "users_by_role": [{"role": r[0].value if hasattr(r[0], "value") else r[0], "count": r[1]} for r in users_by_role.all()],
        "subscriptions_by_plan": [
            {"plan": r[0].value if hasattr(r[0], "value") else r[0], "count": r[1]} for r in subs_by_plan.all()
        ],
    }


@router.get("/audit-logs")
async def audit_logs(
    limit: int = 100,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "actor_email": l.actor_email,
            "actor_role": l.actor_role,
            "action": l.action,
            "resource": l.resource,
            "details": l.details,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/system")
async def system_info(staff: AdminUser = Depends(require_developer)):
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "ai_provider": settings.DEFAULT_AI_PROVIDER,
        "ai_model": settings.DEFAULT_AI_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "free_trial_days": settings.FREE_TRIAL_DAYS,
        "cors_origins": settings.cors_origins_list,
    }


@router.get("/staff")
async def list_staff(
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at))
    accounts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "email": a.email,
            "name": a.name,
            "role": a.role,
            "is_active": a.is_active,
            "last_login": a.last_login.isoformat() if a.last_login else None,
        }
        for a in accounts
    ]


@router.get("/users")
async def list_users(
    q: str = "",
    limit: int = 50,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).limit(limit)
    if q:
        query = query.where(
            User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%") | User.phone.ilike(f"%{q}%")
        )
    result = await db.execute(query)
    patients = result.scalars().all()
    svc = ChatHistoryService(db)
    rows = []
    for p in patients:
        rows.append({
            "id": str(p.id),
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "message_count": await svc.message_count(p.id),
        })
    return rows


@router.delete("/users/{user_id}/chat-history")
async def developer_delete_chat_history(
    user_id: UUID,
    staff: AdminUser = Depends(require_developer),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete stored chat messages and conversation memory for a patient."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await ChatHistoryService(db).hard_delete_for_user(user_id)
    return {"deleted": True, **result}
