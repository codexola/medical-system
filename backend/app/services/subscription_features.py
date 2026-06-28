"""Feature access by subscription plan."""

from __future__ import annotations

from app.models import Subscription, SubscriptionPlan, User

FEATURES_BY_PLAN: dict[SubscriptionPlan, frozenset[str]] = {
    SubscriptionPlan.FREE_TRIAL: frozenset({
        "ai_chat",
        "hospital_search",
        "medication_advice",
    }),
    SubscriptionPlan.STANDARD: frozenset({
        "ai_chat",
        "hospital_search",
        "medication_advice",
        "medication_prices",
        "pharmacy_search",
        "directions",
        "reminders",
    }),
    SubscriptionPlan.PREMIUM: frozenset({
        "ai_chat",
        "hospital_search",
        "medication_advice",
        "medication_prices",
        "medication_origin",
        "pharmacy_search",
        "directions",
        "specialist_details",
        "reminders",
        "family",
        "analytics",
        "priority_support",
    }),
    SubscriptionPlan.ENTERPRISE: frozenset({
        "ai_chat",
        "hospital_search",
        "medication_advice",
        "medication_prices",
        "medication_origin",
        "pharmacy_search",
        "directions",
        "specialist_details",
        "reminders",
        "family",
        "analytics",
        "priority_support",
    }),
}


def plan_features(plan: SubscriptionPlan) -> frozenset[str]:
    return FEATURES_BY_PLAN.get(plan, FEATURES_BY_PLAN[SubscriptionPlan.FREE_TRIAL])


def has_feature(plan: SubscriptionPlan, feature: str) -> bool:
    return feature in plan_features(plan)


def features_for_user(user: User, subscription: Subscription | None) -> frozenset[str]:
    if not subscription:
        return plan_features(SubscriptionPlan.FREE_TRIAL)
    return plan_features(subscription.plan)
