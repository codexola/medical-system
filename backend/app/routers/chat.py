from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.api.schemas import (
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
    SymptomAssessmentRequest,
    SymptomAssessmentResponse,
)
from app.ai.agents import AgentOrchestrator
from app.ai.openai_provider import AIProviderError
from app.database.session import get_db
from app.models import SubscriptionPlan, User
from app.routers.auth import get_current_user
from app.services.chat_history import ChatHistoryService
from app.services.response_composer import ResponseComposer
from app.services.subscription import SubscriptionService

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history", response_model=list[ChatHistoryItem])
async def get_chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    messages = await ChatHistoryService(db).list_for_user(user, channel="web", limit=limit)
    return [
        ChatHistoryItem(role=m.role.value, content=m.content, created_at=m.created_at.isoformat())
        for m in messages
    ]


@router.delete("/history")
async def clear_chat_history_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Patient dashboard: hide conversation from view. Database rows kept for admin/developer."""
    await ChatHistoryService(db).clear_for_patient_dashboard(user)
    lang = user.preferred_language or "ja"
    message = (
        "会話履歴を削除しました。"
        if lang == "ja"
        else "Conversation history cleared."
    )
    return {"cleared": True, "message": message}


@router.post("/", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_svc = SubscriptionService(db)
    if sub_svc.is_test_account(user):
        sub = await sub_svc.get_active_subscription(user.id)
        if not sub:
            await sub_svc.activate_plan_without_payment(user, SubscriptionPlan.PREMIUM)
            await db.commit()

    sub_active = await sub_svc.check_subscription_active(user.id)
    if not sub_active:
        return ChatResponse(
            reply="サブスクリプションの有効期限が切れています。/dashboard/subscription から更新してください。"
            if user.preferred_language == "ja"
            else "Your subscription has expired. Please renew at /dashboard/subscription.",
            user_id=str(user.id),
        )

    orchestrator = AgentOrchestrator(db)
    try:
        result = await orchestrator.process_message(user, data.message, data.channel)
    except Exception as e:
        logger.exception("chat_error", user_id=str(user.id), error=str(e))
        lang = user.preferred_language or "ja"
        history = await ChatHistoryService(db).list_for_user(user, channel="web", limit=20)
        composed = await ResponseComposer(db).compose(user, data.message, lang, history=history)
        from app.ai.chat_result import ChatResult
        result = ChatResult(
            reply=composed.reply,
            hospitals=composed.hospitals,
            pharmacies=composed.pharmacies,
            suggested_department=composed.suggested_department,
            cannot_diagnose=composed.cannot_diagnose,
            show_hospital_finder=composed.show_hospital_finder,
            show_pharmacy_finder=composed.show_pharmacy_finder,
        )

    return ChatResponse(
        reply=result.reply,
        user_id=str(user.id),
        hospitals=result.hospitals,
        pharmacies=result.pharmacies,
        specialists=result.specialists,
        suggested_department=result.suggested_department,
        cannot_diagnose=result.cannot_diagnose,
        show_hospital_finder=result.show_hospital_finder,
        show_pharmacy_finder=result.show_pharmacy_finder,
        plan=result.plan,
        features=result.features,
    )


@router.post("/assess", response_model=SymptomAssessmentResponse)
async def assess_symptoms(
    data: SymptomAssessmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orchestrator = AgentOrchestrator(db)
    assessment = await orchestrator.assess_symptoms(user, data.symptoms)
    return SymptomAssessmentResponse(
        id=str(assessment.id),
        urgency=assessment.urgency.value,
        summary=assessment.ai_summary or "",
        recommended_department=assessment.recommended_department,
        recommended_tests=assessment.recommended_tests,
        disclaimer=assessment.disclaimer,
    )
