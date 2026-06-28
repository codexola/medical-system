from datetime import date, datetime, timezone

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AdminDashboardStats, AdminSubscriptionCancel, AdminSubscriptionUpdate, FAQCreate, HealthCheckinCreate
from app.database.session import get_db
from app.models import (
    AILog,
    FAQ,
    HealthCheckin,
    Reservation,
    ReservationStatus,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
)
from app.auth.deps import require_admin
from app.models import AdminUser
from app.routers.auth import get_current_user
from app.services.chat_history import ChatHistoryService
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardStats)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    today = date.today()
    today_res = await db.scalar(
        select(func.count(Reservation.id)).where(Reservation.date == today)
    )
    total_patients = await db.scalar(select(func.count(User.id)))
    active_subs = await db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        )
    )
    ai_today = await db.scalar(
        select(func.count(AILog.id)).where(
            func.date(AILog.created_at) == today
        )
    )
    return AdminDashboardStats(
        today_reservations=today_res or 0,
        total_patients=total_patients or 0,
        active_subscriptions=active_subs or 0,
        ai_calls_today=ai_today or 0,
        unread_notifications=0,
    )


@router.get("/reservations/today")
async def today_reservations(
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    from app.services.reservation import ReservationService

    reservations = await ReservationService(db).get_today_reservations()
    return [
        {
            "id": str(r.id),
            "date": str(r.date),
            "time": r.time.isoformat(),
            "status": r.status.value,
            "patient_name": r.user.name if r.user else None,
            "department": r.department,
        }
        for r in reservations
    ]


@router.get("/patients")
async def search_patients(
    q: str = "",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    query = select(User).limit(limit)
    if q:
        query = query.where(
            User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%") | User.phone.ilike(f"%{q}%")
        )
    result = await db.execute(query)
    patients = result.scalars().all()
    svc = SubscriptionService(db)
    rows = []
    for p in patients:
        sub = await svc.get_active_subscription(p.id)
        row = {
            "id": str(p.id),
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "preferred_language": p.preferred_language,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        if sub:
            row["subscription"] = svc._subscription_to_dict(sub, p)
        else:
            row["subscription"] = None
        rows.append(row)
    return rows


@router.get("/ai-logs")
async def ai_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    result = await db.execute(select(AILog).order_by(AILog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "provider": l.provider,
            "model": l.model,
            "agent": l.agent,
            "tokens": l.total_tokens,
            "latency_ms": l.latency_ms,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/faqs")
async def list_faqs(
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    result = await db.execute(select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order))
    faqs = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "question": f.question,
            "question_en": f.question_en,
            "answer": f.answer,
            "answer_en": f.answer_en,
            "category": f.category,
        }
        for f in faqs
    ]


@router.post("/faqs")
async def create_faq(
    data: FAQCreate,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    faq = FAQ(
        question=data.question,
        question_en=data.question_en,
        answer=data.answer,
        answer_en=data.answer_en,
        category=data.category,
    )
    db.add(faq)
    await db.flush()
    return {"id": str(faq.id)}


@router.post("/health-checkin")
async def record_checkin(
    data: HealthCheckinCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checkin = HealthCheckin(
        user_id=user.id,
        checkin_date=date.today(),
        **data.model_dump(exclude_unset=True),
    )
    db.add(checkin)
    await db.flush()
    return {"status": "recorded", "id": str(checkin.id)}


@router.get("/analytics")
async def analytics(
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    total_users = await db.scalar(select(func.count(User.id)))
    total_reservations = await db.scalar(select(func.count(Reservation.id)))
    confirmed = await db.scalar(
        select(func.count(Reservation.id)).where(Reservation.status == ReservationStatus.CONFIRMED)
    )
    total_ai_calls = await db.scalar(select(func.count(AILog.id)))
    total_tokens = await db.scalar(select(func.sum(AILog.total_tokens)))
    return {
        "total_users": total_users or 0,
        "total_reservations": total_reservations or 0,
        "confirmed_reservations": confirmed or 0,
        "total_ai_calls": total_ai_calls or 0,
        "total_tokens_used": total_tokens or 0,
    }


@router.get("/subscriptions")
async def list_subscriptions(
    status: str = "",
    plan: str = "",
    q: str = "",
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    svc = SubscriptionService(db)
    return await svc.list_subscriptions(
        status=status or None,
        plan=plan or None,
        q=q,
        limit=min(limit, 200),
    )


@router.get("/subscriptions/{subscription_id}")
async def get_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    svc = SubscriptionService(db)
    sub = await svc.get_subscription_by_id(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return svc._subscription_to_dict(sub, sub.user)


@router.post("/subscriptions/{subscription_id}/cancel")
async def admin_cancel_subscription(
    subscription_id: UUID,
    data: AdminSubscriptionCancel,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    svc = SubscriptionService(db)
    sub = await svc.get_subscription_by_id(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    updated = await svc.cancel_subscription(sub, at_period_end=data.at_period_end)
    return svc._subscription_to_dict(updated, sub.user)


@router.patch("/subscriptions/{subscription_id}")
async def admin_update_subscription(
    subscription_id: UUID,
    data: AdminSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    svc = SubscriptionService(db)
    sub = await svc.get_subscription_by_id(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    try:
        plan = SubscriptionPlan(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")
    updated = await svc.change_plan(sub, plan, admin_override=data.admin_override)
    return svc._subscription_to_dict(updated, sub.user)


@router.delete("/users/{user_id}/chat-history")
async def admin_delete_chat_history(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: AdminUser = Depends(require_admin),
):
    """Permanently delete stored chat messages and conversation memory for a patient."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await ChatHistoryService(db).hard_delete_for_user(user_id)
    return {"deleted": True, **result}
