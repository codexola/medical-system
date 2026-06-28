from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AdminSubscriptionCancel, AdminSubscriptionUpdate
from app.database.session import get_db
from app.models import SubscriptionPlan, User
from app.routers.auth import get_current_user
from app.services.subscription import SubscriptionService
from app.services.subscription_features import plan_features

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("/status")
async def subscription_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = SubscriptionService(db)
    if service.is_test_account(user):
        sub = await service.get_active_subscription(user.id)
        if not sub:
            sub = await service.activate_plan_without_payment(user, SubscriptionPlan.PREMIUM)
            await db.commit()
    sub = await service.get_active_subscription(user.id)
    active = await service.check_subscription_active(user.id)
    if not sub:
        return {
            "active": False,
            "plan": None,
            "status": None,
            "subscription_id": None,
            "is_test_account": service.is_test_account(user),
            "can_select_without_payment": service.is_test_account(user),
            "features": list(plan_features(SubscriptionPlan.FREE_TRIAL)),
        }
    data = service._subscription_to_dict(sub, user)
    data["active"] = active
    data["is_test_account"] = service.is_test_account(user)
    data["can_select_without_payment"] = service.is_test_account(user)
    data["features"] = list(plan_features(sub.plan))
    return data


@router.post("/checkout")
async def create_checkout(
    plan: str = "standard",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SubscriptionService(db)
    try:
        plan_enum = SubscriptionPlan(plan)
        url = await service.create_checkout_session(user, plan_enum)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"checkout_url": url}


@router.post("/cancel")
async def cancel_my_subscription(
    data: AdminSubscriptionCancel,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SubscriptionService(db)
    sub = await service.get_active_subscription(user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    updated = await service.cancel_subscription(sub, at_period_end=data.at_period_end)
    return service._subscription_to_dict(updated, user)


@router.patch("/plan")
async def change_my_plan(
    data: AdminSubscriptionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SubscriptionService(db)
    try:
        plan = SubscriptionPlan(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if service.is_test_account(user):
        updated = await service.activate_plan_without_payment(user, plan)
        await db.commit()
        result = service._subscription_to_dict(updated, user)
        result["features"] = list(plan_features(plan))
        result["is_test_account"] = True
        return result

    sub = await service.get_active_subscription(user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    if not data.admin_override:
        try:
            url = await service.create_checkout_session(user, plan)
            return {"checkout_url": url, "requires_payment": True}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    updated = await service.change_plan(sub, plan, admin_override=data.admin_override, user=user)
    return service._subscription_to_dict(updated, user)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    import stripe
    from app.config import get_settings

    settings = get_settings()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return {"error": "invalid signature"}

    await SubscriptionService(db).handle_webhook_event(event)
    return {"status": "ok"}
