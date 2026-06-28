from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Subscription, SubscriptionPlan, SubscriptionStatus, User

settings = get_settings()
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class SubscriptionService:
    PLAN_PRICES = {
        SubscriptionPlan.STANDARD: settings.STRIPE_PRICE_STANDARD,
        SubscriptionPlan.PREMIUM: settings.STRIPE_PRICE_PREMIUM,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def test_account_emails() -> set[str]:
        return {e.strip().lower() for e in settings.TEST_ACCOUNT_EMAILS.split(",") if e.strip()}

    @classmethod
    def is_test_account(cls, user: User) -> bool:
        email = (user.email or "").lower()
        return email in cls.test_account_emails()

    async def get_active_subscription(self, user_id) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def check_subscription_active(self, user_id) -> bool:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and self.is_test_account(user):
            sub = await self.get_active_subscription(user_id)
            if not sub:
                await self.activate_plan_without_payment(user, SubscriptionPlan.PREMIUM)
                return True
            return sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL)

        sub = await self.get_active_subscription(user_id)
        if not sub:
            return False
        if sub.status == SubscriptionStatus.CANCELLED:
            return False
        if sub.status == SubscriptionStatus.TRIAL and sub.trial_end:
            return sub.trial_end > datetime.now(timezone.utc)
        if sub.status == SubscriptionStatus.EXPIRED:
            return False
        if sub.status == SubscriptionStatus.ACTIVE:
            if sub.current_period_end and sub.current_period_end < datetime.now(timezone.utc):
                return False
            return True
        return sub.status == SubscriptionStatus.TRIAL

    def _subscription_to_dict(self, sub: Subscription, user: Optional[User] = None) -> dict:
        data = {
            "id": str(sub.id),
            "user_id": str(sub.user_id),
            "plan": sub.plan.value,
            "status": sub.status.value,
            "stripe_customer_id": sub.stripe_customer_id,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "trial_start": sub.trial_start.isoformat() if sub.trial_start else None,
            "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
            "active": False,
        }
        if user:
            data["patient_name"] = user.name
            data["patient_email"] = user.email
        data["active"] = (
            sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL)
            and (not sub.trial_end or sub.trial_end > datetime.now(timezone.utc) or sub.status == SubscriptionStatus.ACTIVE)
            and sub.status != SubscriptionStatus.CANCELLED
        )
        return data

    async def list_subscriptions(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        q: str = "",
        limit: int = 100,
    ) -> list[dict]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .order_by(Subscription.created_at.desc())
            .limit(limit * 3)
        )
        subs = result.scalars().all()
        seen_users: set[UUID] = set()
        items: list[dict] = []

        for sub in subs:
            if sub.user_id in seen_users:
                continue
            seen_users.add(sub.user_id)
            user = sub.user
            if q:
                blob = f"{user.name or ''} {user.email or ''} {user.phone or ''}".lower()
                if q.lower() not in blob:
                    continue
            if status and sub.status.value != status:
                continue
            if plan and sub.plan.value != plan:
                continue
            items.append(self._subscription_to_dict(sub, user))
            if len(items) >= limit:
                break
        return items

    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def activate_plan_without_payment(self, user: User, plan: SubscriptionPlan) -> Subscription:
        """Activate or upgrade a plan without Stripe (test accounts / admin)."""
        sub = await self.get_active_subscription(user.id)
        now = datetime.now(timezone.utc)
        if not sub:
            sub = Subscription(user_id=user.id)
            self.db.add(sub)

        sub.plan = plan
        sub.status = SubscriptionStatus.ACTIVE
        sub.trial_start = None
        sub.trial_end = None
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=365)
        sub.cancelled_at = None
        await self.db.flush()
        return sub

    async def create_checkout_session(self, user: User, plan: SubscriptionPlan) -> str:
        if self.is_test_account(user):
            await self.activate_plan_without_payment(user, plan)
            base = settings.FRONTEND_URL.rstrip("/")
            return f"{base}/dashboard/subscription?success=true&test_account=1"

        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe is not configured. Contact admin to change your plan.")
        price_id = self.PLAN_PRICES.get(plan)
        if not price_id:
            raise ValueError(f"No price configured for plan {plan}")

        base = settings.FRONTEND_URL.rstrip("/")
        session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{base}/dashboard/subscription?success=true",
            cancel_url=f"{base}/dashboard/subscription?cancelled=true",
            metadata={"user_id": str(user.id), "plan": plan.value},
        )
        return session.url

    async def cancel_subscription(self, sub: Subscription, at_period_end: bool = False) -> Subscription:
        if sub.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
            try:
                if at_period_end:
                    stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
                else:
                    stripe.Subscription.cancel(sub.stripe_subscription_id)
            except stripe.error.StripeError:
                pass

        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = datetime.now(timezone.utc)
        await self.db.flush()
        return sub

    async def change_plan(
        self,
        sub: Subscription,
        new_plan: SubscriptionPlan,
        admin_override: bool = False,
        user: Optional[User] = None,
    ) -> Subscription:
        if user and self.is_test_account(user):
            admin_override = True

        if new_plan == SubscriptionPlan.FREE_TRIAL:
            sub.plan = new_plan
            sub.status = SubscriptionStatus.TRIAL
            now = datetime.now(timezone.utc)
            if not sub.trial_start:
                sub.trial_start = now
            sub.trial_end = now + timedelta(days=settings.FREE_TRIAL_DAYS)
            await self.db.flush()
            return sub

        if (
            sub.stripe_subscription_id
            and settings.STRIPE_SECRET_KEY
            and not admin_override
        ):
            price_id = self.PLAN_PRICES.get(new_plan)
            if price_id:
                try:
                    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                    item_id = stripe_sub["items"]["data"][0]["id"]
                    stripe.Subscription.modify(
                        sub.stripe_subscription_id,
                        items=[{"id": item_id, "price": price_id}],
                    )
                except stripe.error.StripeError:
                    pass

        sub.plan = new_plan
        sub.status = SubscriptionStatus.ACTIVE
        now = datetime.now(timezone.utc)
        if not sub.current_period_start:
            sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.cancelled_at = None
        await self.db.flush()
        return sub

    async def handle_webhook_event(self, event: dict) -> None:
        event_type = event["type"]

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            plan = SubscriptionPlan(session["metadata"]["plan"])
            sub = await self.get_active_subscription(UUID(user_id))
            if sub:
                sub.plan = plan
                sub.status = SubscriptionStatus.ACTIVE
                sub.stripe_customer_id = session.get("customer")
                sub.stripe_subscription_id = session.get("subscription")
                sub.current_period_start = datetime.now(timezone.utc)
                sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
                await self.db.flush()
            return

        if event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
            obj = event["data"]["object"]
            stripe_sub_id = obj.get("id")
            result = await self.db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
            )
            sub = result.scalar_one_or_none()
            if not sub:
                return
            if event_type == "customer.subscription.deleted" or obj.get("status") == "canceled":
                sub.status = SubscriptionStatus.CANCELLED
                sub.cancelled_at = datetime.now(timezone.utc)
            elif obj.get("status") == "active":
                sub.status = SubscriptionStatus.ACTIVE
                if obj.get("current_period_start"):
                    sub.current_period_start = datetime.fromtimestamp(obj["current_period_start"], tz=timezone.utc)
                if obj.get("current_period_end"):
                    sub.current_period_end = datetime.fromtimestamp(obj["current_period_end"], tz=timezone.utc)
            elif obj.get("status") == "past_due":
                sub.status = SubscriptionStatus.PAST_DUE
            await self.db.flush()
