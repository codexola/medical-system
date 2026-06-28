"""Structured medical triage for stable, symptom-focused chat responses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.models import Message, MessageRole, User
from app.services.medication_catalog import enrich_medication_advice

# ---------------------------------------------------------------------------
# Symptom categories with follow-up questions and stage-based guidance
# ---------------------------------------------------------------------------

FOLLOWUP = {
    "fever": {
        "ja": [
            ("temperature", "現在の体温は何度くらいですか？（例：37.5度、38度以上）"),
            ("duration", "いつから発熱が続いていますか？（例：今日から、2日前から）"),
            ("associated", "咳、のどの痛み、呼吸困難、頭痛、吐き気など、他に気になる症状はありますか？"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("temperature", "What is your current temperature? (e.g. 99°F, above 100.4°F)"),
            ("duration", "How long have you had the fever? (e.g. since today, for 2 days)"),
            ("associated", "Do you have cough, sore throat, breathing difficulty, headache, or nausea?"),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
    "headache": {
        "ja": [
            ("severity", "頭痛の強さを1〜10で教えてください（10が最も強い）"),
            ("duration", "いつから頭痛がありますか？突然始まりましたか？"),
            ("associated", "吐き気、視界の異常、首のこわばり、発熱はありますか？"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("severity", "Rate your headache from 1–10 (10 is worst)."),
            ("duration", "When did it start? Did it come on suddenly?"),
            ("associated", "Do you have nausea, vision changes, stiff neck, or fever?"),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
    "cough_cold": {
        "ja": [
            ("duration", "咳や風邪の症状はいつから続いていますか？"),
            ("fever", "発熱はありますか？あれば何度くらいですか？"),
            ("associated", "痰の色、呼吸困難、胸の痛み、のどの痛みはありますか？"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("duration", "How long have you had cough or cold symptoms?"),
            ("fever", "Do you have a fever? If so, how high?"),
            ("associated", "Any colored phlegm, breathing difficulty, chest pain, or sore throat?"),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
    "stomach": {
        "ja": [
            ("location", "お腹のどのあたりが痛みますか？（上腹部、下腹部、全体など）"),
            ("duration", "いつから症状がありますか？"),
            ("associated", "吐き気、下痢、血便、発熱はありますか？"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("location", "Where is the pain? (upper abdomen, lower abdomen, all over)"),
            ("duration", "When did the symptoms start?"),
            ("associated", "Do you have nausea, diarrhea, bloody stool, or fever?"),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
    "skin": {
        "ja": [
            ("appearance", "発疹やかゆみの様子を教えてください（赤い、水ぶくれ、広がっているなど）"),
            ("duration", "いつから症状がありますか？"),
            ("associated", "発熱、呼吸困難、顔や口の腫れはありますか？"),
            ("medications_allergies", "最近新しいお薬を飲み始めましたか？薬のアレルギーはありますか？"),
        ],
        "en": [
            ("appearance", "Describe the rash or itch (red, blisters, spreading, etc.)"),
            ("duration", "When did it start?"),
            ("associated", "Any fever, breathing difficulty, or swelling of face/lips?"),
            ("medications_allergies", "Did you start any new medication recently? Any drug allergies?"),
        ],
    },
    "hay_fever": {
        "ja": [
            ("duration", "花粉の症状はいつから続いていますか？"),
            ("associated", "目のかゆみ、鼻水、くしゃみ、のどの痛みはどれがありますか？"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("duration", "How long have you had pollen allergy symptoms?"),
            ("associated", "Do you have itchy eyes, runny nose, sneezing, or sore throat?"),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
    "general": {
        "ja": [
            ("symptoms", "具体的にどのような症状がありますか？（痛み、発熱、息切れなど）"),
            ("duration", "いつから症状が続いていますか？"),
            ("severity", "症状の強さを1〜10で教えてください（10が最も強い）"),
            ("medications_allergies", "現在服用中のお薬や、薬のアレルギーはありますか？"),
        ],
        "en": [
            ("symptoms", "What specific symptoms do you have? (pain, fever, shortness of breath, etc.)"),
            ("duration", "How long have you had these symptoms?"),
            ("severity", "Rate severity from 1–10 (10 is worst)."),
            ("medications_allergies", "Are you taking any medications or do you have drug allergies?"),
        ],
    },
}

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "fever": ("発熱", "熱", "高熱", "fever", "temperature", "体温"),
    "headache": ("頭痛", "頭が痛", "headache", "migraine"),
    "cough_cold": ("咳", "風邪", "鼻水", "くしゃみ", "のど", "喉", "cough", "cold", "sore throat", "runny nose"),
    "stomach": ("腹痛", "お腹", "胃", "下痢", "吐", "stomach", "abdominal", "nausea", "diarrhea", "vomit"),
    "skin": ("かゆ", "痒", "発疹", "湿疹", "rash", "itch", "hives", "skin"),
    "hay_fever": ("花粉症", "花粉", "hay fever", "pollen", "目がかゆ", "鼻水", "くしゃみ"),
}

DEPARTMENT_MAP = {
    "fever": "internal_medicine",
    "headache": "neurology",
    "cough_cold": "internal_medicine",
    "stomach": "gastroenterology",
    "skin": "dermatology",
    "hay_fever": "otolaryngology",
    "general": "internal_medicine",
}

EMERGENCY_PATTERNS = (
    r"胸.*痛", r"chest pain", r"呼吸.*困難", r"息.*でき", r"can.t breathe",
    r"意識.*(ない|もう)", r"unconscious", r"大量.*出血", r"severe bleeding",
    r"片側.*(しび|麻)", r"stroke", r"突然.*(激|強).*痛",
)

GREETING_PATTERNS = (
    r"^(こんにちは|おはよう|こんばんは|はじめまして|hello|hi|hey|good morning|good evening)[\s!。、!?]*$",
    r"^(やあ|どうも)[\s!。、]*$",
)

HOSPITAL_EXPLICIT = (
    "病院", "クリニック", "医院", "近くの", "おすすめの病院", "hospital", "clinic", "nearby", "recommend",
)

MEDICAL_KEYWORDS = (
    "痛", "熱", "咳", "吐", "痒", "腫", "血", "息", "動悸", "めまい", "しびれ",
    "症状", "体調", "心配", "具合", "調子", "病気", "薬", "受診", "診察", "病院",
    "クリニック", "発熱", "頭痛", "腹痛", "風邪", "アレルギ", "感染", "治療", "診断",
    "不眠", "眠れ", "睡眠", "うつ", "鬱", "糖尿病", "高血圧", "花粉症", "喘息",
    "pain", "fever", "cough", "symptom", "ache", "hurt", "nausea", "rash",
    "headache", "dizzy", "medication", "medicine", "hospital", "clinic", "doctor",
    "health", "medical", "treatment", "diagnosis", "prescription", "insomnia", "anxiety",
)

NON_MEDICAL_PATTERNS = (
    r"^(こんにちは|hello|hi|hey)[\s!。]*$",
    r"^(ありがと|thank you|thanks)[\s!。]*$",
    r"(天気|weather|株|stock|bitcoin|programming|コード|python|javascript)",
    r"(レシピ|recipe|cooking)(?!.*(アレル|食中毒|消化))",
)

TEMP_RE = re.compile(r"(\d{2}(?:\.\d)?)\s*度|(\d{2}(?:\.\d)?)\s*°")
DURATION_RE = re.compile(
    r"(\d+)\s*(日|週|時間|day|days|week|hour|hours)|今日|昨日|today|yesterday|先週",
    re.I,
)
SEVERITY_RE = re.compile(
    r"(?:^|[^\d])([1-9]|10)\s*(?:/10|点|くらい|程度)|(?:強|弱|moderate|mild|severe)",
    re.I,
)

# Asked only when giving medication advice — not required before evaluation
OPTIONAL_FOLLOWUP_KEYS = frozenset({"medications_allergies"})

STATED_DIAGNOSIS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "insomnia": ("不眠", "眠れない", "insomnia", "sleep"),
    "hypertension": ("高血圧", "hypertension", "blood pressure"),
    "diabetes": ("糖尿病", "diabetes", "血糖", "blood sugar"),
    "depression": ("うつ", "鬱", "depression", "気分が落ち"),
    "gastritis": ("胃炎", "gastritis", "胃もたれ"),
    "allergy": ("アレルギー", "allergy", "アナフィラキシー"),
    "hay_fever": ("花粉症", "hay fever", "pollen"),
    "asthma": ("喘息", "asthma"),
    "migraine": ("片頭痛", "migraine"),
}

DIAGNOSIS_MENTION_RE = re.compile(
    r"(と診断|と言われ|といわれ|診断され|診断を受け|病名は|doctor said|diagnosed with|told I have)",
    re.I,
)

CATEGORY_EMPATHY_JA = {
    "fever": "発熱が続いているのですね。つらいと思います。",
    "headache": "頭痛が気になるのですね。お辛いでしょう。",
    "cough_cold": "咳や風邪の症状があるのですね。",
    "stomach": "お腹の調子が優れないのですね。",
    "skin": "お肌の症状が気になるのですね。",
    "general": "お話しくださりありがとうございます。",
}

CATEGORY_EMPATHY_EN = {
    "fever": "A fever can be really draining — I'm glad you reached out.",
    "headache": "Headaches can be tough to deal with.",
    "cough_cold": "Cough and cold symptoms are no fun.",
    "stomach": "Stomach trouble can really wear you down.",
    "skin": "Skin symptoms can be worrying.",
    "general": "Thank you for sharing what's going on.",
}

ALLERGY_NOTE_JA = "\n\n※現在服用中のお薬やアレルギーがあれば、お知らせください。お薬の選択に大切です。"
ALLERGY_NOTE_EN = "\n\n※Please let me know any medications or allergies — that helps me guide you safely."


@dataclass
class TriageResult:
    is_medical: bool
    category: Optional[str] = None
    department: Optional[str] = None
    stage: str = "gathering"  # gathering | medication | refer_hospital | emergency | non_medical
    next_question: Optional[str] = None
    collected: dict = field(default_factory=dict)
    medication_advice: Optional[str] = None
    referral_reason: Optional[str] = None
    urgency: str = "low"
    show_hospitals: bool = False
    show_pharmacies: bool = False
    cannot_diagnose: bool = True
    stated_diagnosis: Optional[str] = None
    patient_summary: Optional[str] = None


class MedicalTriageService:
    @staticmethod
    def is_greeting(text: str) -> bool:
        t = text.strip()
        return any(re.match(p, t, re.I) for p in GREETING_PATTERNS)

    @staticmethod
    def explicitly_wants_hospital(text: str) -> bool:
        lower = text.lower()
        return any(kw in text or kw in lower for kw in HOSPITAL_EXPLICIT)

    @staticmethod
    def is_emergency(text: str) -> bool:
        lower = text.lower()
        return any(re.search(p, text, re.I) or re.search(p, lower, re.I) for p in EMERGENCY_PATTERNS)

    @staticmethod
    def is_medical(text: str) -> bool:
        if MedicalTriageService.is_emergency(text):
            return True
        lower = text.lower()
        if any(re.search(p, text, re.I) or re.search(p, lower, re.I) for p in NON_MEDICAL_PATTERNS):
            # Still medical if symptom keywords present
            if not any(kw in text or kw in lower for kw in MEDICAL_KEYWORDS):
                return False
        return any(kw in text or kw in lower for kw in MEDICAL_KEYWORDS)

    @staticmethod
    def detect_category(text: str, history_text: str = "") -> str:
        combined = f"{history_text} {text}"
        lower = combined.lower()
        best = "general"
        best_score = 0
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined or kw in lower)
            if score > best_score:
                best_score = score
                best = cat
        return best

    @staticmethod
    def _detect_stated_diagnosis(text: str) -> Optional[str]:
        lower = text.lower()
        for label, keywords in STATED_DIAGNOSIS_KEYWORDS.items():
            if not any(kw in text or kw in lower for kw in keywords):
                continue
            if (
                DIAGNOSIS_MENTION_RE.search(text)
                or any(kw in text for kw in ("治療中", "薬を飲", "通院", "悩んで", "困って"))
                or any(kw in lower for kw in ("on medication", "being treated", "struggling with"))
            ):
                return label
        return None

    @staticmethod
    def _diagnosis_guidance(diagnosis: str, lang: str) -> Optional[str]:
        guides_ja = {
            "insomnia": (
                "まず就寝前のスマホを控え、室温を涼しく保つとよいです。"
                "短期間なら市販の睡眠改善薬（ドリエル等）も選択肢ですが、2週間以上続く場合は精神科・心療内科の受診をお勧めします。"
            ),
            "hypertension": (
                "減塩・適度な運動・服薬遵守が基本です。"
                "血圧計で記録をつけ、めまい・胸の痛み・激しい頭痛があればすぐ受診してください。"
            ),
            "diabetes": (
                "食事内容・運動・処方薬の継続が大切です。"
                "のどが渇く・尿量増加・意識もうろつきがあれば、早めに受診をお願いします。"
            ),
            "depression": (
                "まずは信頼できる人や専門医に相談することが第一歩です。"
                "自分を責めず、睡眠と食事をできる範囲で整えてください。緊急のつらさがある場合はいつでも相談窓口へ。"
            ),
            "gastritis": (
                "刺激の少ない食事・少量ずつ・禁煙禁酒を心がけてください。"
                "制酸剤や胃粘膜保護薬が市販でもあります。血便・激痛・吐血があればすぐ受診を。"
            ),
            "allergy": (
                "原因の回避と、医師の指示どおりのお薬が基本です。"
                "呼吸困難・喉の腫れ・全身の蕁麻疹は緊急受診のサインです。"
            ),
            "hay_fever": (
                "外出後の洗顔・うがい、メガネ着用、市販の抗ヒスタミン薬（アレグラ、ザイザル等）が役立ちます。"
                "症状が強い場合は耳鼻咽喉科で処方薬の相談を。"
            ),
            "asthma": (
                "吸入薬は医師の指示どおり継続し、発作時の対応も確認しておきましょう。"
                "息苦しさが普段と違うときは迷わず受診してください。"
            ),
            "migraine": (
                "暗い静かな場所で休み、早めの鎮痛がコツです。"
                "月に数回以上・吐き気や視界異常を伴う場合は神経内科の受診をお勧めします。"
            ),
        }
        guides_en = {
            "insomnia": "For insomnia: limit screens before bed, keep the room cool. Short-term OTC sleep aids may help; see psychiatry if it lasts 2+ weeks.",
            "hypertension": "For blood pressure: low salt, exercise, take prescribed meds. Record readings; seek care for dizziness, chest pain, or severe headache.",
            "diabetes": "For diabetes: diet, activity, and medication adherence matter. Seek care for extreme thirst, frequent urination, or confusion.",
            "depression": "Your feelings matter. Reach out to someone you trust or a specialist. Prioritize sleep and meals; use crisis lines if you feel unsafe.",
            "gastritis": "For stomach irritation: bland small meals, avoid alcohol/smoking. Antacids may help; urgent care for bloody stool or severe pain.",
            "allergy": "Avoid triggers and follow prescribed treatment. Emergency care for breathing difficulty, throat swelling, or widespread hives.",
            "hay_fever": "Rinse face after going out, consider antihistamines; see ENT for stronger prescriptions if needed.",
            "asthma": "Use inhalers as directed. Seek care if breathing feels worse than usual.",
            "migraine": "Rest in a dark quiet room; treat early. See neurology if attacks are frequent or include vision changes.",
        }
        guides = guides_ja if lang == "ja" else guides_en
        return guides.get(diagnosis)

    @staticmethod
    def _empathy_opener(category: Optional[str], stated_diagnosis: Optional[str], lang: str) -> str:
        if stated_diagnosis and lang == "ja":
            labels = {
                "insomnia": "不眠", "hypertension": "高血圧", "diabetes": "糖尿病",
                "depression": "うつ", "gastritis": "胃炎", "allergy": "アレルギー",
                "hay_fever": "花粉症", "asthma": "喘息", "migraine": "片頭痛",
            }
            label = labels.get(stated_diagnosis, "そのご病気")
            return f"{label}でお悩みなのですね。一緒に整理していきましょう。"
        if stated_diagnosis:
            return f"I understand you're dealing with {stated_diagnosis.replace('_', ' ')}. Let's work through this together."
        cat = category or "general"
        empathy = CATEGORY_EMPATHY_JA if lang == "ja" else CATEGORY_EMPATHY_EN
        return empathy.get(cat, empathy["general"])

    @staticmethod
    def _display_collected_value(key: str, value: str, lang: str) -> str:
        if value == "none reported":
            labels = {
                "associated": ("付随症状は特にない", "no other symptoms reported"),
                "medications_allergies": ("お薬・アレルギー情報なし", "no medication/allergy info yet"),
            }
            pair = labels.get(key, ("特になし", "none reported"))
            return pair[0] if lang == "ja" else pair[1]
        return value

    @staticmethod
    def _summarize_patient_message(message: str, collected: dict, lang: str) -> Optional[str]:
        parts = []
        if collected.get("temperature"):
            parts.append(f"体温{collected['temperature']}度" if lang == "ja" else f"temp {collected['temperature']}")
        if collected.get("duration"):
            parts.append(collected["duration"])
        if collected.get("severity"):
            parts.append(collected["severity"])
        if collected.get("associated"):
            parts.append(
                MedicalTriageService._display_collected_value("associated", collected["associated"], lang)
            )
        if parts:
            if lang == "ja":
                return "「" + "、".join(parts[:4]) + "」と伺いました。"
            return "So far I understand: " + ", ".join(parts[:4]) + "."
        if len(message.strip()) > 12:
            snippet = message.strip()[:60] + ("…" if len(message) > 60 else "")
            return f"「{snippet}」についてですね。" if lang == "ja" else f"About: {snippet}"
        return None

    @staticmethod
    def _facility_flags(stage: str, urgency: str) -> tuple[bool, bool]:
        show_hospitals = stage in ("medication", "refer_hospital", "emergency")
        show_pharmacies = stage in ("medication", "refer_hospital")
        return show_hospitals, show_pharmacies

    def _finalize_medication(
        self, meds: Optional[str], category: Optional[str], collected: dict, lang: str
    ) -> Optional[str]:
        if not meds:
            return None
        enriched = enrich_medication_advice(meds, category, lang)
        return self._append_allergy_note(enriched, collected, lang)

    @staticmethod
    def _append_allergy_note(advice: str, collected: dict, lang: str) -> str:
        if collected.get("medications_allergies"):
            return advice
        note = ALLERGY_NOTE_JA if lang == "ja" else ALLERGY_NOTE_EN
        return advice + note

    @staticmethod
    def _user_text(history: list[Message], current: str) -> str:
        parts = [m.content for m in history if m.role == MessageRole.USER]
        parts.append(current)
        return "\n".join(parts)

    @staticmethod
    def _conversation_text(history: list[Message], current: str) -> str:
        parts = [m.content for m in history if m.role in (MessageRole.USER, MessageRole.ASSISTANT)]
        parts.append(current)
        return "\n".join(parts)

    @staticmethod
    def _extract_collected(conv: str, category: str, history: Optional[list[Message]] = None) -> dict:
        collected: dict[str, str] = {}
        lower = conv.lower()
        lang = "ja"  # field keys are language-neutral

        temp_match = TEMP_RE.search(conv)
        if temp_match:
            collected["temperature"] = temp_match.group(1) or temp_match.group(2) or ""

        if re.search(r"38|39|40|100\.|101\.|102\.", conv):
            collected["high_fever"] = "yes"
        if re.search(r"37\.[0-9]|37度|微熱", conv):
            collected["low_fever"] = "yes"

        dur = DURATION_RE.search(conv)
        if dur:
            collected["duration"] = dur.group(0)

        sev = SEVERITY_RE.search(conv)
        if sev:
            collected["severity"] = sev.group(0)

        associated_flags = []
        associated_checks = (
            ("咳", r"咳"),
            ("呼吸", r"呼吸"),
            ("吐", r"吐"),
            ("下痢", r"下痢"),
            ("血", r"(吐血|血便|血尿|鼻血|便に血|血の混じ)"),
            ("視界", r"視界"),
            ("首", r"首(が|の)?(痛|凝|こり)"),
            ("cough", r"\bcough"),
            ("breath", r"breath"),
            ("nausea", r"nausea"),
            ("diarrhea", r"diarrhea"),
            ("blood", r"\bblood"),
        )
        for label, pattern in associated_checks:
            neg_patterns = (
                rf"{label}(は|が)?(ありません|ない|なし|いません)",
                rf"no\s+{label}" if label in ("cough", "breath", "nausea", "diarrhea", "blood") else None,
            )
            if any(re.search(p, conv, re.I) for p in neg_patterns if p):
                continue
            if re.search(pattern, conv, re.I):
                associated_flags.append(label)
        if re.search(r"他に|ほかに|それ以外|特に.*(ない|なし)|no other|nothing else", conv, re.I):
            collected["associated"] = "none reported"
        elif re.search(
            r"(咳|のど|呼吸|吐|下痢).{0,6}(ない|なし|ありません|いません)|no (cough|breathing|nausea)",
            conv,
            re.I,
        ):
            collected["associated"] = "none reported"
        elif associated_flags:
            collected["associated"] = ", ".join(associated_flags)

        if re.search(r"薬|アレルギ|medication|allerg|服用|飲んで", conv, re.I):
            collected["medications_allergies"] = "mentioned"
        elif re.search(r"(特に)?(ない|なし|ありません|none|no)\s*(です|。)?", conv, re.I):
            if history and any(
                re.search(r"薬|アレルギ|medication|allerg", m.content, re.I)
                for m in history if m.role == MessageRole.ASSISTANT
            ):
                collected["medications_allergies"] = "none reported"
            elif re.search(r"咳|熱|痛|症状|fever|cough|pain", conv, re.I):
                if re.search(r"他に|ほかに|それ以外|no other|nothing else", conv, re.I):
                    if "associated" not in collected:
                        collected["associated"] = "none reported"

        if category == "stomach" and re.search(r"上|下|全体|upper|lower", conv, re.I):
            collected["location"] = "mentioned"

        if category == "skin" and re.search(r"赤|水ぶくれ|広|red|blister|spread", conv, re.I):
            collected["appearance"] = "mentioned"

        if re.search(r"症状|痛|熱|symptom|pain|fever", conv, re.I):
            collected["symptoms"] = "mentioned"

        # Map prior assistant questions to user answers for stable multi-turn flow
        if history:
            questions = FOLLOWUP.get(category, FOLLOWUP["general"])
            q_list = questions.get("ja", questions["ja"])
            for i, msg in enumerate(history):
                if msg.role != MessageRole.ASSISTANT or i + 1 >= len(history):
                    continue
                reply = history[i + 1]
                if reply.role != MessageRole.USER:
                    continue
                for key, question in q_list:
                    if key in collected:
                        continue
                    marker = question[:12]
                    if marker in msg.content or question in msg.content:
                        collected[key] = reply.content.strip()[:200]

        return collected

    @staticmethod
    def _missing_question(category: str, collected: dict, lang: str) -> Optional[str]:
        questions = FOLLOWUP.get(category, FOLLOWUP["general"])[lang]
        for key, question in questions:
            if key in OPTIONAL_FOLLOWUP_KEYS:
                continue
            if key not in collected:
                return question
        return None

    @staticmethod
    def _parse_temperature(collected: dict, conv: str) -> Optional[float]:
        temp_match = TEMP_RE.search(conv)
        if temp_match:
            val = temp_match.group(1) or temp_match.group(2)
            if val:
                return float(val)
        if collected.get("high_fever"):
            return 38.5
        if collected.get("low_fever"):
            return 37.5
        return None

    @staticmethod
    def _evaluate_fever(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        temp = MedicalTriageService._parse_temperature(collected, conv)
        has_breathing = bool(re.search(
            r"呼吸困難|息苦し|息が.*(苦|でき)|breathing difficulty|shortness of breath|can.t breathe",
            conv, re.I,
        ))
        duration = collected.get("duration", "")

        if has_breathing or (temp and temp >= 39.5):
            reason = (
                "高熱または呼吸に関する症状があるため、速やかな受診が必要です。"
                if lang == "ja"
                else "High fever or breathing symptoms require prompt medical evaluation."
            )
            return "refer_hospital", None, reason, "high"

        long_duration = bool(re.search(r"[3-9]\s*日|[3-9]\s*day|1\s*週|week", duration, re.I))
        if temp and temp >= 38.0 and long_duration:
            meds = (
                "解熱剤（アセトアミノフェン500mg、1日3回まで）と水分補給・安静を。"
                "3日以上続く場合は内科を受診してください。"
                if lang == "ja"
                else "Acetaminophen 500mg up to 3× daily, fluids, rest. See internal medicine if fever persists 3+ days."
            )
            return "medication", meds, None, "medium"

        if temp and temp >= 37.5:
            meds = (
                "【この段階で検討できる対処】\n"
                "・解熱剤：アセトアミノフェン（例：タイレノールA 1回500mg、1日3回まで）\n"
                "　※イブプロフェンは胃への負担があるため、空腹時は避けてください\n"
                "・水分・電解質をこまめに補給し、安静にしてください\n"
                "・48時間経っても改善しない、または38度以上が続く場合は受診してください"
                if lang == "ja"
                else (
                    "【Care at this stage】\n"
                    "· Antipyretic: Acetaminophen (e.g. 500 mg, up to 3× daily)\n"
                    "· Stay hydrated and rest\n"
                    "· See a doctor if no improvement in 48 h or fever ≥38°C persists"
                )
            )
            return "medication", meds, None, "low"

        if temp and temp < 37.5:
            meds = (
                "【この段階で検討できる対処】\n"
                "・微熱の場合はまず水分補給と安静を心がけてください\n"
                "・必要に応じてアセトアミノフェン（解熱剤）を検討できます\n"
                "・症状が悪化する場合は医療機関を受診してください"
                if lang == "ja"
                else (
                    "【Care at this stage】\n"
                    "· For low-grade fever: rest and hydration first\n"
                    "· Acetaminophen if needed\n"
                    "· Seek care if symptoms worsen"
                )
            )
            return "medication", meds, None, "low"

        return "medication", (
            "【この段階で検討できる対処】\n"
            "・まず解熱剤としてアセトアミノフェン（タイレノールA 500mg、1日3回まで）を検討できます\n"
            "・水分と休息を心がけてください\n"
            "・体温がわかれば、より具体的なアドバイスができますので教えてください"
            if lang == "ja"
            else (
                "【Care at this stage】\n"
                "· Consider acetaminophen 500 mg up to 3× daily\n"
                "· Rest and hydrate\n"
                "· Share your temperature if you can for more specific guidance"
            )
        ), None, "low"

    @staticmethod
    def _evaluate_headache(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        sudden = bool(re.search(r"突然|急に|sudden|worst", conv, re.I))
        severe = bool(re.search(r"[789]|10\s*点|severe|激しい|強い", conv, re.I))
        neck = bool(re.search(r"首.*(こわ|硬|stiff)", conv, re.I))
        vision = bool(re.search(r"視界|vision|見え", conv, re.I))

        if sudden or severe or neck or vision:
            reason = (
                "突然の激しい頭痛、首のこわばり、視界異常がある場合は、緊急の受診が必要です。"
                if lang == "ja"
                else "Sudden severe headache with neck stiffness or vision changes needs urgent care."
            )
            return "refer_hospital", None, reason, "high"

        if collected.get("severity") or collected.get("duration"):
            meds = (
                "【この段階で検討できる対処】\n"
                "・鎮痛剤：アセトアミノフェン 500mg、またはイブプロフェン 200mg（食後）\n"
                "・暗く静かな場所で休息、こまめな水分補給\n"
                "・24時間以上改善しない、または吐き気・視界異常が出た場合は受診してください"
                if lang == "ja"
                else (
                    "【Care at this stage】\n"
                    "· Analgesic: Acetaminophen 500 mg or ibuprofen 200 mg (with food)\n"
                    "· Rest in a quiet, dark room; stay hydrated\n"
                    "· See a doctor if no improvement in 24 h or new nausea/vision changes"
                )
            )
            return "medication", meds, None, "low"

        return "medication", (
            "まず暗い静かな場所で休み、水分を取ってください。アセトアミノフェン500mgも検討できます。"
            if lang == "ja"
            else "Rest in a quiet dark room, stay hydrated. Acetaminophen 500mg may help."
        ), None, "low"

    @staticmethod
    def _evaluate_cough_cold(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        breathing = bool(re.search(r"呼吸困難|息苦し|息が", conv, re.I))
        blood_phlegm = bool(re.search(r"血.*痰|blood", conv, re.I))
        long_duration = bool(re.search(r"[24][0-9]\s*日|[2-9]\s*week|2週", conv, re.I))

        if breathing or blood_phlegm:
            reason = (
                "呼吸困難や血痰がある場合は、速やかに受診してください。"
                if lang == "ja"
                else "Breathing difficulty or bloody sputum requires prompt medical care."
            )
            return "refer_hospital", None, reason, "high"

        if long_duration:
            meds = (
                "咳が2週間以上続く場合は受診を。それまでは去痰剤・のど飴・水分補給と安静を。"
                if lang == "ja"
                else "Cough 2+ weeks warrants a visit. Until then: expectorant, lozenges, fluids, rest."
            )
            return "medication", meds, None, "medium"

        if collected.get("duration") or collected.get("associated"):
            meds = (
                "のど飴・去痰剤・抗ヒスタミン薬と水分補給・安静を。3日以上続く・悪化する場合は受診を。"
                if lang == "ja"
                else "Lozenges, expectorant, antihistamine, fluids, rest. See a doctor if 3+ days or worsening."
            )
            return "medication", meds, None, "low"

        return "medication", (
            "まず安静と水分補給を。のど飴や去痰剤も検討できます。"
            if lang == "ja"
            else "Rest, fluids, lozenges or expectorant may help."
        ), None, "low"

    @staticmethod
    def _evaluate_stomach(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        blood = bool(re.search(r"血便|吐血|blood|black stool|黒い便", conv, re.I))
        severe = bool(re.search(r"[789]|10|severe|激しい|耐え", conv, re.I))

        if blood or severe:
            reason = (
                "血便・激しい腹痛・吐血がある場合は、速やかに救急受診してください。"
                if lang == "ja"
                else "Bloody stool, severe abdominal pain, or vomiting blood requires urgent care."
            )
            return "refer_hospital", None, reason, "high"

        if collected.get("location") and collected.get("duration"):
            meds = (
                "制酸剤・整腸剤、水分補給、軽い食事と安静を。24時間以上続く・痛みが強くなる場合は受診を。"
                if lang == "ja"
                else "Antacids, intestinal aids, fluids, light meals, rest. See a doctor if 24h+ or worsening."
            )
            return "medication", meds, None, "low"

        return "medication", (
            "まず安静と温かい飲み物で。軽い胃もたれなら制酸剤も。悪化したら受診を。"
            if lang == "ja"
            else "Rest, warm drinks, antacids for mild indigestion. See a doctor if worsening."
        ), None, "low"

    @staticmethod
    def _evaluate_skin(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        swelling = bool(re.search(r"顔.*腫|口.*腫|喉.*腫|swelling.*(face|lip)", conv, re.I))
        spreading = bool(re.search(r"全身|広が|spread|whole body", conv, re.I))

        if swelling or spreading:
            reason = (
                "顔・口の腫れや全身の発疹は緊急受診が必要な場合があります。"
                if lang == "ja"
                else "Facial swelling or spreading rash may need urgent care."
            )
            return "refer_hospital", None, reason, "high"

        if collected.get("appearance") and collected.get("duration"):
            meds = (
                "抗ヒスタミン薬（ロラタジン等）、患部を清潔に。48時間以上続く場合は皮膚科へ。"
                if lang == "ja"
                else "Antihistamine (e.g. loratadine), keep area clean. See dermatology if 48h+."
            )
            return "medication", meds, None, "low"

        return "medication", (
            "かゆみがあれば抗ヒスタミン薬を。掻かず清潔に保ってください。"
            if lang == "ja"
            else "Antihistamine for itch; keep area clean, don't scratch."
        ), None, "low"

    @staticmethod
    def _evaluate_hay_fever(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        guide = MedicalTriageService._diagnosis_guidance("hay_fever", lang)
        return "medication", guide, None, "low"

    @staticmethod
    def _evaluate_general(collected: dict, conv: str, lang: str) -> tuple[str, Optional[str], Optional[str], str]:
        if len(collected) >= 1:
            meds = (
                "【この段階で検討できる対処】\n"
                "・安静と水分補給を心がけてください\n"
                "・解熱・鎮痛ならアセトアミノフェン500mg（1日3回まで）が選択肢です\n"
                "・持病やアレルギーがある方は薬剤師にご相談ください\n"
                "・症状が強くなる・長引く場合は専門医の受診をお勧めします"
                if lang == "ja"
                else (
                    "【Care at this stage】\n"
                    "· Rest and stay hydrated\n"
                    "· Acetaminophen 500 mg up to 3× daily may help for pain/fever\n"
                    "· Ask a pharmacist if you have chronic conditions or allergies\n"
                    "· See a specialist if symptoms worsen or persist"
                )
            )
            return "medication", meds, None, "low"
        return "gathering", None, None, "low"

    def analyze(
        self,
        user: User,
        message: str,
        history: list[Message],
        lang: str,
    ) -> TriageResult:
        if self.is_emergency(message):
            return TriageResult(
                is_medical=True,
                category="general",
                department="emergency",
                stage="emergency",
                urgency="emergency",
                show_hospitals=True,
                cannot_diagnose=True,
                referral_reason=(
                    "緊急の症状です。119番または最寄りの救急へ。"
                    if lang == "ja"
                    else "Emergency symptoms — call 119 or go to the ER."
                ),
            )

        ongoing_medical = bool(history) and self.is_medical(self._user_text(history, message))

        if self.is_greeting(message) and not ongoing_medical:
            return TriageResult(is_medical=True, stage="greeting", urgency="low", cannot_diagnose=False)

        if not self.is_medical(message):
            if not ongoing_medical:
                return TriageResult(is_medical=False, stage="non_medical", cannot_diagnose=False)

        conv = self._conversation_text(history, message)
        user_conv = self._user_text(history, message)
        stated_diagnosis = self._detect_stated_diagnosis(conv)
        category = self.detect_category(message, conv)
        department = DEPARTMENT_MAP.get(category, "internal_medicine")
        collected = self._extract_collected(conv, category, history)
        patient_summary = self._summarize_patient_message(message, collected, lang)

        if stated_diagnosis:
            diag_guide = self._diagnosis_guidance(stated_diagnosis, lang)
            has_acute_workup = category != "general" and (
                collected.get("severity") or collected.get("duration") or collected.get("temperature")
            )
            acute_red_flags = re.search(
                r"めまい|息切れ|胸.*痛|意識|激しい|悪化|blood|dizz|chest pain|shortness",
                user_conv,
                re.I,
            )
            if diag_guide and not has_acute_workup and not acute_red_flags:
                show_h, show_p = self._facility_flags("medication", "low")
                return TriageResult(
                    is_medical=True,
                    category=category,
                    department=department,
                    stage="medication",
                    collected=collected,
                    medication_advice=self._finalize_medication(diag_guide, category, collected, lang),
                    urgency="low",
                    cannot_diagnose=True,
                    stated_diagnosis=stated_diagnosis,
                    patient_summary=patient_summary,
                    show_hospitals=show_h,
                    show_pharmacies=show_p,
                )
            if diag_guide and acute_red_flags:
                urgent = (
                    "いまのめまいや体調の変化は、血圧やお薬の影響の可能性もあります。今日中にかかりつけ医へご相談ください。"
                    if lang == "ja"
                    else "New dizziness or similar changes may relate to blood pressure or medication — contact your doctor today."
                )
                show_h, show_p = self._facility_flags("refer_hospital", "medium")
                return TriageResult(
                    is_medical=True,
                    category=category,
                    department=department,
                    stage="refer_hospital",
                    collected=collected,
                    medication_advice=self._finalize_medication(diag_guide, category, collected, lang),
                    referral_reason=urgent,
                    urgency="medium",
                    cannot_diagnose=True,
                    stated_diagnosis=stated_diagnosis,
                    patient_summary=patient_summary,
                    show_hospitals=show_h,
                    show_pharmacies=show_p,
                )

        next_q = self._missing_question(category, collected, lang)
        if next_q:
            return TriageResult(
                is_medical=True,
                category=category,
                department=department,
                stage="gathering",
                next_question=next_q,
                collected=collected,
                urgency="low",
                cannot_diagnose=True,
                stated_diagnosis=stated_diagnosis,
                patient_summary=patient_summary,
            )

        evaluators = {
            "fever": self._evaluate_fever,
            "headache": self._evaluate_headache,
            "cough_cold": self._evaluate_cough_cold,
            "stomach": self._evaluate_stomach,
            "skin": self._evaluate_skin,
            "hay_fever": self._evaluate_hay_fever,
            "general": self._evaluate_general,
        }
        stage, meds, referral, urgency = evaluators.get(category, self._evaluate_general)(
            collected, user_conv, lang
        )
        meds = self._finalize_medication(meds, category, collected, lang)

        show_hospitals, show_pharmacies = self._facility_flags(stage, urgency)

        return TriageResult(
            is_medical=True,
            category=category,
            department=department,
            stage=stage,
            collected=collected,
            medication_advice=meds,
            referral_reason=referral,
            urgency=urgency,
            show_hospitals=show_hospitals,
            show_pharmacies=show_pharmacies,
            cannot_diagnose=True,
            stated_diagnosis=stated_diagnosis,
            patient_summary=patient_summary,
        )

    def format_reply(
        self,
        triage: TriageResult,
        user: User,
        lang: str,
        hospital_summary: str = "",
    ) -> str:
        name = user.name or ("お客様" if lang == "ja" else "there")
        empathy = self._empathy_opener(triage.category, triage.stated_diagnosis, lang)

        if triage.stage == "greeting":
            if lang == "ja":
                return f"こんにちは、{name}さん。今日はどんな症状が気になりますか？ゆっくりで大丈夫ですよ。"
            return f"Hello, {name}. What's on your mind today? Take your time — I'm here to help."

        if triage.stage == "non_medical":
            if lang == "ja":
                return f"{name}さん、こちらは健康・症状のご相談用です。今の体調で気になることはありますか？"
            return f"{name}, I'm here for health questions. Is there anything about how you're feeling that you'd like to talk about?"

        if triage.stage == "emergency":
            if lang == "ja":
                base = f"{name}さん、それはとても心配です。{triage.referral_reason or ''} 落ち着いて、119番または最寄りの救急へ向かってください。"
            else:
                base = f"{name}, that sounds urgent. {triage.referral_reason or ''} Please stay calm and call 119 or go to the nearest ER."
            return f"{base}\n{hospital_summary}".strip() if hospital_summary else base

        if triage.stage == "gathering" and triage.next_question:
            parts = [empathy]
            if triage.patient_summary:
                parts.append(triage.patient_summary)
            if lang == "ja":
                parts.append(f"差し支えなければ、{triage.next_question}")
            else:
                parts.append(f"May I ask: {triage.next_question}")
            return "".join(parts)

        if triage.stage == "medication" and triage.medication_advice:
            parts = [empathy]
            if triage.patient_summary:
                parts.append(triage.patient_summary)
            advice = triage.medication_advice
            if lang == "ja":
                if advice.startswith("【"):
                    parts.append(f"\n\n{advice}")
                else:
                    parts.append(f"\n\n【この段階で検討できる対処】\n{advice}")
                parts.append("\n\n症状が悪化したり、不安なことがあればいつでもお知らせください。")
            else:
                parts.append(f"\n\n{triage.medication_advice}")
                parts.append("\n\nIf anything worsens or you're unsure, just let me know.")
            return "".join(parts)

        if triage.stage == "refer_hospital" and triage.referral_reason:
            if lang == "ja":
                base = f"{empathy}"
                if triage.patient_summary:
                    base += triage.patient_summary
                if triage.medication_advice:
                    advice = triage.medication_advice
                    if advice.startswith("【"):
                        base += f"\n\n{advice}"
                    else:
                        base += f"\n\n【この段階で検討できる対処】\n{advice}"
                base += f"\n\n{name}さん、{triage.referral_reason}"
                if hospital_summary:
                    return f"{base}\n{hospital_summary}"
                return base
            base = f"{empathy}{triage.patient_summary or ''}\n\n{name}, {triage.referral_reason}"
            return f"{base}\n{hospital_summary}".strip() if hospital_summary else base

        if lang == "ja":
            return f"{empathy}もう少し詳しく教えていただけますか？"
        return f"{empathy}Could you tell me a bit more about how you're feeling?"
