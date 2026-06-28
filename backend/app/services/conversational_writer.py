"""Turn structured triage facts into short, natural conversational replies via OpenAI."""

from __future__ import annotations

from typing import Optional

from app.ai.base import AIMessage
from app.ai.openai_provider import AIProviderError
from app.ai.service import AIService
from app.models import Message, MessageRole, User
from app.services.medical_triage import MedicalTriageService, TriageResult
from app.services.medication_catalog import medication_keywords_in_text

NATURALIZE_SYSTEM_JA = """あなたは経験豊富で温かい医療相談アシスタントです。患者が話しかけてくる親しい専門家のように、正確でやさしい日本語（です・ます調）で返答してください。

【最重要ルール】
1. 臨床メモのお薬名・用量・価格目安・受診の目安は一字一句変えず正確に伝える
2. 診断は下さない。対処・市販薬・受診の目安のみ
3. 患者の症状・診断名を必ず一度言及してから回答する
4. 4〜8文。共感 → 具体的な市販薬アドバイス → 必要なら短い質問
5. 質問は1つだけ。すでに答えてくれたことは聞き直さない
6. 軽症は必ず具体的な市販薬（商品名・用量）を提案する。「医師に相談してください」だけで終わらせない
7. 重症・緊急のときのみ救急・受診を強調する
8. 近くの病院・薬局の情報はシステムが別途添付するので、本文では繰り返さなくてよい

【トーン】
- 患者が退屈やイライラを感じないよう、温かく要点を押さえる
- ロボットのような「わかりました。」だけで始めない"""

NATURALIZE_SYSTEM_EN = """You are a warm, experienced healthcare assistant. Reply like a caring professional in natural English.

CRITICAL RULES:
1. Preserve drug names, doses, price estimates, and referral thresholds exactly
2. Do not diagnose — offer care steps and OTC options only
3. Acknowledge the patient's symptoms or stated diagnosis first
4. 4–8 sentences: empathy → specific OTC advice → one question if needed
5. At most ONE follow-up question; never re-ask answered items
6. For mild cases, always suggest specific OTC medicines by name — never end with only "see a doctor"
7. Recommend ER/hospital only for severe/emergency cases
8. Local hospital/pharmacy lists are appended separately — do not duplicate them"""


class ConversationalMedicalWriter:
    def __init__(self):
        self.ai = AIService()
        self.triage_svc = MedicalTriageService()

    def _facts_block(self, triage: TriageResult, context: str, lang: str) -> str:
        lines = [
            f"stage={triage.stage}",
            f"urgency={triage.urgency}",
            f"category={triage.category or 'general'}",
        ]
        if triage.stated_diagnosis:
            lines.append(f"patient_stated_diagnosis={triage.stated_diagnosis}")
        if triage.patient_summary:
            lines.append(f"acknowledge: {triage.patient_summary}")
        if triage.next_question:
            lines.append(f"must_ask_one_question: {triage.next_question}")
        if triage.medication_advice:
            lines.append(f"preserve_exactly_treatment_guidance:\n{triage.medication_advice}")
        if triage.referral_reason:
            lines.append(f"referral_guidance: {triage.referral_reason}")
        if triage.collected:
            lines.append(f"known_facts: {triage.collected}")
        if context:
            lines.append(f"reference_data:\n{context[:1500]}")
        return "\n".join(lines)

    async def write(
        self,
        user: User,
        message: str,
        history: list[Message],
        triage: TriageResult,
        medical_context: str,
        lang: str,
    ) -> Optional[str]:
        system = NATURALIZE_SYSTEM_JA if lang == "ja" else NATURALIZE_SYSTEM_EN
        facts = self._facts_block(triage, medical_context, lang)
        name = user.name or ("お客様" if lang == "ja" else "there")

        messages: list[AIMessage] = [
            AIMessage(
                role="system",
                content=f"{system}\n\n患者名: {name}\n\n【臨床メモ — この内容を正確に反映すること】\n{facts}",
            )
        ]

        for msg in history[-12:]:
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                messages.append(AIMessage(role=msg.role.value, content=msg.content))

        messages.append(AIMessage(role="user", content=message))

        try:
            response = await self.ai.chat(messages, temperature=0.25)
            text = (response.content or "").strip()
            if len(text) < 15:
                return None
            # Reject if AI dropped medication guidance on medication stage
            if triage.stage == "medication" and triage.medication_advice:
                expected = medication_keywords_in_text(triage.medication_advice)
                if expected and not any(k in text or k.lower() in text.lower() for k in expected):
                    return None
            return text
        except AIProviderError:
            return None

    def fallback(self, triage: TriageResult, user: User, lang: str, hospital_summary: str = "") -> str:
        return self.triage_svc.format_reply(triage, user, lang, hospital_summary)
