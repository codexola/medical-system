"""Compose stable, medical-only patient responses via structured triage."""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FAQ, KnowledgeDocument, Message, SubscriptionPlan, User
from app.services.hospital import DEPARTMENT_KEYWORDS, HospitalService
from app.services.medical_triage import MedicalTriageService, TriageResult
from app.services.medication_catalog import enrich_medication_origin
from app.services.pharmacy import PharmacyService
from app.services.specialist_service import SpecialistService
from app.services.subscription import SubscriptionService
from app.services.subscription_features import has_feature

DEPARTMENT_LABELS_JA = {
    "internal_medicine": "内科",
    "cardiology": "心臓内科・循環器科",
    "neurology": "神経内科",
    "dermatology": "皮膚科",
    "dentistry": "歯科",
    "orthopedics": "整形外科",
    "pediatrics": "小児科",
    "ophthalmology": "眼科",
    "psychiatry": "精神科",
    "gastroenterology": "消化器内科",
    "otolaryngology": "耳鼻咽喉科",
    "oncology": "腫瘍科",
    "emergency": "救急",
}

DEPARTMENT_LABELS_EN = {
    "internal_medicine": "Internal Medicine",
    "cardiology": "Cardiology",
    "neurology": "Neurology",
    "dermatology": "Dermatology",
    "dentistry": "Dentistry",
    "orthopedics": "Orthopedics",
    "pediatrics": "Pediatrics",
    "ophthalmology": "Ophthalmology",
    "psychiatry": "Psychiatry",
    "gastroenterology": "Gastroenterology",
    "otolaryngology": "ENT",
    "oncology": "Oncology",
    "emergency": "Emergency",
}


@dataclass
class ComposedResponse:
    reply: str
    core_reply: str
    facility_appendix: str = ""
    hospitals: list[dict] = field(default_factory=list)
    pharmacies: list[dict] = field(default_factory=list)
    specialists: list[dict] = field(default_factory=list)
    suggested_department: Optional[str] = None
    cannot_diagnose: bool = False
    show_hospital_finder: bool = False
    show_pharmacy_finder: bool = False
    triage: Optional[TriageResult] = None


class ResponseComposer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hospitals = HospitalService(db)
        self.pharmacies = PharmacyService(db)
        self.specialists_svc = SpecialistService(db)
        self.triage = MedicalTriageService()
        self.subscriptions = SubscriptionService(db)

    @staticmethod
    def is_symptom_query(text: str) -> bool:
        return MedicalTriageService.is_medical(text)

    @staticmethod
    def wants_hospitals(text: str) -> bool:
        return MedicalTriageService.explicitly_wants_hospital(text)

    def infer_department(self, text: str) -> Optional[str]:
        lower = text.lower()
        for key, dept in DEPARTMENT_KEYWORDS.items():
            if key in lower or key in text:
                return dept
        return None

    def _dept_label(self, dept: Optional[str], lang: str) -> str:
        if not dept:
            return "総合診療" if lang == "ja" else "General care"
        labels = DEPARTMENT_LABELS_JA if lang == "ja" else DEPARTMENT_LABELS_EN
        return labels.get(dept, dept)

    def _format_hospital_summary(self, hospitals: list[dict], lang: str, dept: Optional[str]) -> str:
        if not hospitals:
            return ""

        dept_label = self._dept_label(dept, lang)
        if lang == "ja":
            lines = [f"\n\n📍 お住まいの近くの医療機関（{dept_label}）：\n"]
        else:
            lines = [f"\n\n📍 Healthcare facilities near your home ({dept_label}):\n"]

        for i, h in enumerate(hospitals[:5], 1):
            dist = f"{h['distance_km']}km" if h.get("distance_km") is not None else ""
            time_part = ""
            if h.get("travel_time_minutes"):
                time_part = f" · 約{h['travel_time_minutes']}分" if lang == "ja" else f" · ~{h['travel_time_minutes']} min"
            rating = f" · ★{h['rating']}" if h.get("rating") else ""
            phone = f"\n   📞 {h['phone']}" if h.get("phone") else ""
            route = f"\n   🚗 {h['route_summary']}" if h.get("route_summary") else ""
            reason = f"\n   → {h['reason']}" if h.get("reason") else ""
            lines.append(
                f"{i}. **{h['name']}** ({dist}{time_part}{rating})\n"
                f"   {h.get('address', '')}{phone}{route}{reason}"
            )

        return "\n".join(lines)

    def _format_pharmacy_summary(self, pharmacies: list[dict], lang: str) -> str:
        if not pharmacies:
            return ""

        if lang == "ja":
            lines = ["\n\n💊 お近くのドラッグストア・薬局（市販薬の購入先）：\n"]
        else:
            lines = ["\n\n💊 Nearby drugstores / pharmacies (for OTC medicines):\n"]

        for i, p in enumerate(pharmacies[:5], 1):
            dist = f"{p['distance_km']}km" if p.get("distance_km") is not None else ""
            phone = f"\n   📞 {p['phone']}" if p.get("phone") else ""
            route = f"\n   🚗 {p['route_summary']}" if p.get("route_summary") else ""
            lines.append(f"{i}. **{p['name']}** ({dist})\n   {p.get('address', '')}{phone}{route}")

        if lang == "ja":
            lines.append("\n※市販薬の価格は店舗により異なります。購入前に薬剤師にご相談ください。")
        else:
            lines.append("\n※OTC prices vary by store. Ask the pharmacist before purchasing.")

        return "\n".join(lines)

    def _specialist_note(self, dept: Optional[str], lang: str, stage: str) -> str:
        if stage not in ("medication", "refer_hospital"):
            return ""
        dept_label = self._dept_label(dept, lang)
        if lang == "ja":
            return (
                f"\n\n👨‍⚕️ **専門医へのご相談**\n"
                f"症状が続く場合やご不安なときは、{dept_label}の専門医にご相談されることをお勧めします。"
                f"上記の医療機関で受診・紹介をご検討ください。"
            )
        return (
            f"\n\n👨‍⚕️ **Seeing a specialist**\n"
            f"If symptoms persist or you're concerned, we recommend consulting a {dept_label} specialist "
            f"at one of the facilities listed above."
        )

    def _format_specialist_summary(self, specialists: list[dict], lang: str) -> str:
        if not specialists:
            return ""
        if lang == "ja":
            lines = ["\n\n👨‍⚕️ **おすすめの専門医（各医療機関）**\n"]
        else:
            lines = ["\n\n👨‍⚕️ **Recommended specialists**\n"]
        for i, s in enumerate(specialists[:3], 1):
            exp = s.get("experience_years")
            exp_txt = f"{exp}年の経験" if lang == "ja" and exp else (f"{exp} years experience" if exp else "")
            lines.append(
                f"{i}. **{s.get('name')}**（{s.get('rank')}・{s.get('specialty')}）\n"
                f"   所属: {s.get('hospital_name')}\n"
                f"   診療場所: {s.get('office_address', '')}\n"
                f"   📞 {s.get('phone', '病院代表へ')}\n"
                f"   {exp_txt}\n"
                f"   🚗 ルート: {s.get('route_summary', '地図アプリでご確認ください')}"
                if lang == "ja"
                else (
                    f"{i}. **{s.get('name')}** ({s.get('rank')} · {s.get('specialty')})\n"
                    f"   Hospital: {s.get('hospital_name')}\n"
                    f"   Office: {s.get('office_address', '')}\n"
                    f"   📞 {s.get('phone', 'via hospital')}\n"
                    f"   {exp_txt}\n"
                    f"   🚗 Route: {s.get('route_summary', 'see maps')}"
                )
            )
        return "\n".join(lines)

    def _build_facility_appendix(
        self,
        hospitals: list[dict],
        pharmacies: list[dict],
        specialists: list[dict],
        dept: Optional[str],
        lang: str,
        stage: str,
        include_specialist_note: bool = True,
    ) -> str:
        parts = [
            self._format_hospital_summary(hospitals, lang, dept),
            self._format_pharmacy_summary(pharmacies, lang),
            self._format_specialist_summary(specialists, lang),
        ]
        if include_specialist_note:
            parts.append(self._specialist_note(dept, lang, stage))
        appendix = "".join(p for p in parts if p)
        if appendix and lang == "ja":
            appendix += "\n\n下のカードから詳細を確認できます。"
        elif appendix:
            appendix += "\n\nSee the cards below for details."
        return appendix

    async def compose(
        self,
        user: User,
        query: str,
        lang: str,
        history: Optional[list[Message]] = None,
        hospitals: Optional[list[dict]] = None,
        pharmacies: Optional[list[dict]] = None,
        specialists: Optional[list[dict]] = None,
    ) -> ComposedResponse:
        history = history or []
        triage_result = self.triage.analyze(user, query, history, lang)

        sub = await self.subscriptions.get_active_subscription(user.id)
        if SubscriptionService.is_test_account(user) and not sub:
            sub = await self.subscriptions.activate_plan_without_payment(user, SubscriptionPlan.PREMIUM)
        plan = sub.plan if sub else SubscriptionPlan.FREE_TRIAL

        if triage_result.medication_advice and has_feature(plan, "medication_origin"):
            triage_result.medication_advice = enrich_medication_origin(
                triage_result.medication_advice, triage_result.category, lang
            )

        if triage_result.stage == "non_medical":
            core = self.triage.format_reply(triage_result, user, lang)
            return ComposedResponse(
                reply=core,
                core_reply=core,
                cannot_diagnose=False,
                show_hospital_finder=False,
                triage=triage_result,
            )

        department = triage_result.department or self.infer_department(query)
        show_hospitals = (triage_result.show_hospitals or self.wants_hospitals(query)) and has_feature(
            plan, "hospital_search"
        )
        show_pharmacies = triage_result.show_pharmacies and has_feature(plan, "pharmacy_search")
        show_directions = has_feature(plan, "directions")
        show_specialists = has_feature(plan, "specialist_details")

        if hospitals is None and show_hospitals:
            sort = "specialty" if department else "nearest"
            hospitals = await self.hospitals.filter_for_user(
                user,
                query,
                sort_by=sort,
                department=department,
                urgency=triage_result.urgency,
                limit=5,
                include_routes=show_directions,
            )

        if pharmacies is None and show_pharmacies:
            if show_directions:
                pharmacies = await self.pharmacies.recommend_for_user_with_routes(
                    user, language=lang, limit=5
                )
            else:
                pharmacies = await self.pharmacies.recommend_for_user(user, language=lang, limit=5)

        if specialists is None and show_specialists and hospitals:
            specialists = await self.specialists_svc.attach_specialists(
                user, hospitals, department, language=lang, limit=3
            )

        facility_appendix = self._build_facility_appendix(
            hospitals or [],
            pharmacies or [],
            specialists or [],
            department,
            lang,
            triage_result.stage,
            include_specialist_note=show_specialists or not specialists,
        )
        core_reply = self.triage.format_reply(triage_result, user, lang)
        reply = core_reply + facility_appendix

        return ComposedResponse(
            reply=reply,
            core_reply=core_reply,
            facility_appendix=facility_appendix,
            hospitals=hospitals or [],
            pharmacies=pharmacies or [],
            specialists=specialists or [],
            suggested_department=department,
            cannot_diagnose=triage_result.cannot_diagnose,
            show_hospital_finder=show_hospitals and bool(hospitals),
            show_pharmacy_finder=show_pharmacies and bool(pharmacies),
            triage=triage_result,
        )

    async def compose_clinic_faq(self, query: str, lang: str) -> Optional[str]:
        """Legacy clinic FAQ lookup — only for explicit operational questions."""
        import re

        ops_kw = ("診療時間", "保険", "予約", "hours", "insurance", "appointment")
        if not any(kw in query.lower() or kw in query for kw in ops_kw):
            return None

        words = [w for w in re.split(r"\s+", query) if len(w) >= 2]
        result = await self.db.execute(select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order))
        for faq in result.scalars():
            q = faq.question if lang == "ja" else (faq.question_en or faq.question)
            a = faq.answer if lang == "ja" else (faq.answer_en or faq.answer)
            if any(w in q or w in a for w in words) or any(kw in q for kw in ops_kw):
                header = (
                    "【医療機関のご案内】\n\n" if lang == "ja" else "【Healthcare facility information】\n\n"
                )
                return header + a

        doc_result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.is_active == True).limit(30)
        )
        for doc in doc_result.scalars():
            if doc.content and any(kw in doc.title or kw in doc.content for kw in ops_kw):
                return f"【{doc.title}】\n{doc.content[:600]}"
        return None
