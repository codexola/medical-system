import json
import re
import time
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIMessage
from app.ai.prompts import (
    RECEPTION_SYSTEM_PROMPT,
    SYMPTOM_ASSESSMENT_PROMPT,
    TOOL_FOLLOWUP_PROMPT,
    TRIAGE_CONTEXT_PROMPT,
)
from app.ai.service import AIService
from app.ai.chat_result import ChatResult
from app.ai.openai_provider import AIProviderError
from app.models import (
    AILog,
    ConversationMemory,
    FAQ,
    HealthCheckin,
    KnowledgeDocument,
    Message,
    MessageRole,
    SymptomAssessment,
    UrgencyLevel,
    User,
)
from app.rag.service import RAGService
from app.services.conversational_writer import ConversationalMedicalWriter
from app.services.medical_context import fetch_public_medical_snippets, load_db_medical_context
from app.services.response_composer import ResponseComposer

AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search clinic knowledge base for FAQs, insurance, treatments, hours, and policies",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query in patient's language"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_hospitals",
            "description": "Recommend nearby hospitals/clinics from the patient's registered home address based on symptoms",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {"type": "string", "description": "Patient symptoms or health concern"},
                    "urgency": {"type": "string", "enum": ["low", "medium", "high", "emergency"]},
                    "department": {"type": "string", "description": "Medical department if known"},
                },
                "required": ["symptoms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_directions",
            "description": "Get fastest and safest travel routes from patient's home to a specific hospital",
            "parameters": {
                "type": "object",
                "properties": {
                    "hospital_name": {"type": "string"},
                    "hospital_address": {"type": "string"},
                },
                "required": ["hospital_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check doctor appointment availability",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string"},
                    "date": {"type": "string"},
                    "period": {"type": "string", "enum": ["morning", "afternoon"]},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_appointment",
            "description": "Create an appointment reservation",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "symptoms": {"type": "string"},
                    "department": {"type": "string"},
                },
                "required": ["date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_health_checkin",
            "description": "Record daily health check-in data",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {"type": "integer"},
                    "symptoms": {"type": "string"},
                    "temperature": {"type": "number"},
                    "medication_taken": {"type": "boolean"},
                    "notes": {"type": "string"},
                },
            },
        },
    },
]


TOOL_KEYWORDS = (
    "病院", "クリニック", "hospital", "clinic", "予約", "appointment", "reserve",
    "道順", "ルート", "route", "directions", "空き", "availability",
)


def _needs_tools(content: str) -> bool:
    lower = content.lower()
    return any(kw in lower or kw in content for kw in TOOL_KEYWORDS)


def detect_language(text: str, fallback: str = "ja") -> str:
    if not text.strip():
        return fallback
    japanese = len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[a-zA-Z]", text))
    if japanese > latin:
        return "ja"
    if latin > japanese * 2:
        return "en"
    return fallback


class AgentOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService()
        self.rag = RAGService(db)

    def _build_user_context(self, user: User, lang: str) -> str:
        parts = []
        if user.name:
            parts.append(f"Name: {user.name}")
        if user.address:
            parts.append(f"Home address: {user.address}")
        if user.job_function:
            parts.append(f"Occupation: {user.job_function}")
        if user.allergies:
            parts.append(f"Allergies: {user.allergies}")
        if user.medical_history:
            parts.append(f"Medical history: {user.medical_history}")
        if user.latitude and user.longitude:
            parts.append(f"Home coordinates: {user.latitude}, {user.longitude}")
        if not parts:
            return ""
        header = "患者情報:" if lang == "ja" else "Patient profile:"
        return f"\n\n{header}\n" + "\n".join(parts)

    async def _load_knowledge_context(self, query: str, lang: str) -> str:
        """Load relevant FAQs and knowledge from database (no embeddings required)."""
        snippets: list[str] = []
        words = [w for w in re.split(r"\s+", query) if len(w) >= 2]

        faq_result = await self.db.execute(select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order))
        for faq in faq_result.scalars():
            q = faq.question if lang == "ja" else (faq.question_en or faq.question)
            a = faq.answer if lang == "ja" else (faq.answer_en or faq.answer)
            text = f"{q} {a}"
            if any(w in text for w in words) or any(w in query for w in [q[:4]] if len(q) >= 4):
                snippets.append(f"[FAQ] {q}\n{a}")

        doc_result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.is_active == True).limit(30)
        )
        for doc in doc_result.scalars():
            if doc.content and any(w in doc.content or w in doc.title for w in words):
                snippets.append(f"[{doc.title}]\n{doc.content[:800]}")

        if not snippets and words:
            # Broader match: return top FAQs when no keyword hit
            faq_result = await self.db.execute(
                select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order).limit(3)
            )
            for faq in faq_result.scalars():
                q = faq.question if lang == "ja" else (faq.question_en or faq.question)
                a = faq.answer if lang == "ja" else (faq.answer_en or faq.answer)
                snippets.append(f"[FAQ] {q}\n{a}")

        return "\n\n".join(snippets[:6])

    async def _fallback_from_database(self, user: User, content: str, lang: str) -> str:
        knowledge = await self._load_knowledge_context(content, lang)
        if knowledge:
            header = (
                "データベースの情報に基づきお答えします。\n\n"
                if lang == "ja"
                else "Based on our knowledge base:\n\n"
            )
            return header + knowledge
        if lang == "ja":
            return (
                f"{user.name or 'お客'}様、ご質問ありがとうございます。"
                "現在AIサービスに一時的な接続問題が発生しています。"
                "お急ぎの場合は医療機関へ直接ご相談ください。"
            )
        return (
            "Thank you for your question. We are experiencing a temporary AI service issue. "
            "Please consult a healthcare provider if urgent."
        )

    async def process_message(self, user: User, content: str, channel: str = "line") -> ChatResult:
        await self._save_message(user.id, MessageRole.USER, content, channel)

        history = await self._get_conversation_history(user, limit=50, channel=channel)
        lang = detect_language(content, user.preferred_language or "ja")
        composer = ResponseComposer(self.db)
        writer = ConversationalMedicalWriter()

        clinic_faq = await composer.compose_clinic_faq(content, lang)
        if clinic_faq and not composer.triage.is_medical(content):
            result = ChatResult(reply=clinic_faq, cannot_diagnose=False, show_hospital_finder=False)
            await self._save_message(user.id, MessageRole.ASSISTANT, result.reply, channel)
            return result

        composed = await composer.compose(user, content, lang, history=history)
        triage = composed.triage

        db_ctx = await load_db_medical_context(self.db, content, lang)
        web_ctx = ""
        if triage and triage.is_medical and triage.stage not in ("greeting", "non_medical"):
            web_ctx = await fetch_public_medical_snippets(content, lang)
        medical_context = "\n".join(filter(None, [db_ctx, web_ctx]))

        natural_reply = None
        if triage:
            natural_reply = await writer.write(user, content, history, triage, medical_context, lang)

        # Naturalize core advice only; always append local facility details
        core = natural_reply or composed.core_reply
        reply = core + composed.facility_appendix

        show_finder = composed.show_hospital_finder and bool(composed.hospitals)
        show_pharmacy = composed.show_pharmacy_finder and bool(composed.pharmacies)

        from app.services.subscription import SubscriptionService
        from app.services.subscription_features import plan_features
        from app.models import SubscriptionPlan

        sub_svc = SubscriptionService(self.db)
        sub = await sub_svc.get_active_subscription(user.id)
        plan = sub.plan if sub else SubscriptionPlan.FREE_TRIAL

        result = ChatResult(
            reply=reply,
            hospitals=composed.hospitals if show_finder else [],
            pharmacies=composed.pharmacies if show_pharmacy else [],
            specialists=composed.specialists,
            suggested_department=composed.suggested_department,
            cannot_diagnose=composed.cannot_diagnose,
            show_hospital_finder=show_finder,
            show_pharmacy_finder=show_pharmacy,
            plan=plan.value,
            features=list(plan_features(plan)),
        )
        await self._save_message(user.id, MessageRole.ASSISTANT, result.reply, channel)

        if len(history) > 8:
            try:
                await self._update_memory(user, channel)
            except AIProviderError:
                pass

        return result

    async def assess_symptoms(self, user: User, symptoms: str) -> SymptomAssessment:
        lang = detect_language(symptoms, user.preferred_language or "ja")
        lang_note = "Respond in Japanese." if lang == "ja" else "Respond in English."
        messages = [
            AIMessage(role="system", content=f"{SYMPTOM_ASSESSMENT_PROMPT}\n{lang_note}"),
            AIMessage(role="user", content=f"Patient symptoms: {symptoms}"),
        ]
        response = await self.ai.chat(messages, temperature=0.3)

        urgency = UrgencyLevel.LOW
        for level in UrgencyLevel:
            if level.value in response.content.lower():
                urgency = level
                break

        disclaimer = (
            "これは医療診断ではありません。必ず医療機関にご相談ください。"
            if lang == "ja"
            else "This is not a medical diagnosis. Please consult a healthcare provider."
        )

        assessment = SymptomAssessment(
            user_id=user.id,
            symptoms=symptoms,
            urgency=urgency,
            ai_summary=response.content,
            disclaimer=disclaimer,
        )
        self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def _execute_tools(self, user: User, function_calls: list[dict], lang: str) -> list[dict]:
        results = []
        for call in function_calls:
            name = call["name"]
            args = call.get("arguments", {})

            if name == "search_knowledge":
                try:
                    answer = await self.rag.answer_with_rag(args.get("query", ""), lang)
                except Exception:
                    answer = await self._load_knowledge_context(args.get("query", ""), lang)
                results.append({"tool": name, "result": answer})

            elif name == "recommend_hospitals":
                from app.services.hospital import HospitalService

                hospitals = await HospitalService(self.db).recommend_for_user(
                    user,
                    args.get("symptoms", ""),
                    args.get("urgency", "low"),
                    lang,
                )
                results.append({"tool": name, "result": hospitals})

            elif name == "get_directions":
                from app.services.hospital import HospitalService

                directions = await HospitalService(self.db).get_directions_to_hospital(
                    user,
                    args.get("hospital_name", ""),
                    args.get("hospital_address"),
                    language=lang,
                )
                results.append({"tool": name, "result": directions})

            elif name == "check_availability":
                from app.services.reservation import ReservationService

                doctor_id = args.get("doctor_id")
                if doctor_id:
                    target = datetime.strptime(args["date"], "%Y-%m-%d").date()
                    slots = await ReservationService(self.db).get_available_slots(
                        uuid.UUID(doctor_id), target, args.get("period")
                    )
                    results.append({"tool": name, "result": slots})

            elif name == "reserve_appointment":
                from app.services.reservation import ReservationService

                target = datetime.strptime(args["date"], "%Y-%m-%d").date()
                slot_time = datetime.strptime(args["time"], "%H:%M").time()
                doctor_id = uuid.UUID(args["doctor_id"]) if args.get("doctor_id") else None
                if doctor_id:
                    reservation = await ReservationService(self.db).create_reservation(
                        user.id, doctor_id, target, slot_time, args.get("symptoms"), args.get("department")
                    )
                    results.append({"tool": name, "result": {"id": str(reservation.id), "status": "confirmed"}})

            elif name == "record_health_checkin":
                checkin = HealthCheckin(
                    user_id=user.id,
                    checkin_date=date.today(),
                    mood=args.get("mood"),
                    symptoms=args.get("symptoms"),
                    temperature=args.get("temperature"),
                    medication_taken=args.get("medication_taken"),
                    notes=args.get("notes"),
                )
                self.db.add(checkin)
                await self.db.flush()
                results.append({"tool": name, "result": "checkin recorded"})

        return results

    async def _save_message(self, user_id: uuid.UUID, role: MessageRole, content: str, channel: str) -> None:
        self.db.add(Message(user_id=user_id, role=role, content=content, channel=channel))
        await self.db.flush()

    async def _get_conversation_history(
        self, user: User, limit: int = 20, channel: str | None = None
    ) -> list[Message]:
        q = select(Message).where(Message.user_id == user.id)
        if channel:
            q = q.where(Message.channel == channel)
        if channel == "web" and user.chat_cleared_at:
            q = q.where(Message.created_at > user.chat_cleared_at)
        result = await self.db.execute(q.order_by(Message.created_at.desc()).limit(limit))
        return list(reversed(result.scalars().all()))

    async def _get_user_memory(self, user: User, channel: str = "web") -> Optional[str]:
        result = await self.db.execute(
            select(ConversationMemory)
            .where(ConversationMemory.user_id == user.id)
            .order_by(ConversationMemory.updated_at.desc())
            .limit(1)
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return None
        if channel == "web" and user.chat_cleared_at and memory.updated_at <= user.chat_cleared_at:
            return None
        return memory.summary

    async def _update_memory(self, user: User, channel: str = "web") -> None:
        history = await self._get_conversation_history(user, limit=30, channel=channel)
        if not history:
            return
        conv_text = "\n".join(f"{m.role.value}: {m.content}" for m in history)
        response = await self.ai.chat(
            [
                AIMessage(role="system", content="Summarize key patient facts from this conversation."),
                AIMessage(role="user", content=conv_text),
            ],
            temperature=0.3,
        )
        result = await self.db.execute(
            select(ConversationMemory).where(ConversationMemory.user_id == user.id).limit(1)
        )
        memory = result.scalar_one_or_none()
        if memory:
            memory.summary = response.content
            memory.updated_at = datetime.now(timezone.utc)
        else:
            self.db.add(ConversationMemory(user_id=user.id, summary=response.content))
        await self.db.flush()

    async def _log_ai_call(self, user_id: uuid.UUID, response, agent: str, latency_ms: int) -> None:
        self.db.add(
            AILog(
                user_id=user_id,
                provider=response.provider,
                model=response.model,
                agent=agent,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
                latency_ms=latency_ms,
                function_calls=response.function_calls or None,
            )
        )
        await self.db.flush()
