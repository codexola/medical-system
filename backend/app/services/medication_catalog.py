"""OTC medication reference with approximate retail prices (Japan, 2024–2025)."""

from __future__ import annotations

import re
from typing import Optional

# Approximate OTC price ranges in JPY (tax included, typical drugstore)
OTC_MEDICATIONS: dict[str, dict] = {
    "acetaminophen": {
        "names_ja": ("アセトアミノフェン", "タイレノール", "カロナール"),
        "names_en": ("acetaminophen", "tylenol"),
        "products_ja": [
            ("タイレノールA 500mg", "20錠", "約900〜1,200円"),
            ("カロナールS 200mg", "12包", "約600〜900円"),
        ],
        "products_en": [
            ("Acetaminophen 500 mg tablets", "20 tabs", "approx. ¥900–1,200"),
        ],
        "dose_ja": "成人：1回500mg、1日3回まで（食後）",
        "dose_en": "Adults: 500 mg per dose, up to 3× daily (after meals)",
        "usage_ja": "熱・痛みがあるときに服用。空腹時でも比較的安全ですが、胃が弱い方は食後が安心です。1日の上限を超えないでください。",
        "usage_en": "Take for fever or pain. Generally safe on an empty stomach; take after food if your stomach is sensitive. Do not exceed daily limits.",
        "manufacturer_ja": "第一三共ヘルスケア（タイレノール）/ 大正製薬（カロナール）",
        "origin_ja": "日本国内製造（国内販売用市販薬）",
        "manufacturer_en": "Daiichi Sankyo Healthcare / Taisho Pharmaceutical",
        "origin_en": "Manufactured in Japan (domestic OTC)",
    },
    "ibuprofen": {
        "names_ja": ("イブプロフェン", "ブルフェン", "イブ"),
        "names_en": ("ibuprofen", "advil"),
        "products_ja": [
            ("イブA錠 200mg", "12錠", "約600〜900円"),
            ("ブルフェンA 200mg", "24錠", "約800〜1,100円"),
        ],
        "products_en": [
            ("Ibuprofen 200 mg tablets", "12 tabs", "approx. ¥600–900"),
        ],
        "dose_ja": "成人：1回200mg、1日3回まで（必ず食後）",
        "dose_en": "Adults: 200 mg per dose, up to 3× daily (with food)",
        "usage_ja": "痛み・発熱時に食後服用。胃への負担を減らすため、なるべく食直後に。長期連用は避けてください。",
        "usage_en": "Take after meals for pain or fever. Avoid long-term continuous use.",
        "manufacturer_ja": "エスエス製薬（イブ）/ 久光製薬（ブルフェン）",
        "origin_ja": "日本国内製造",
        "manufacturer_en": "SS Pharmaceutical / Hisamitsu",
        "origin_en": "Manufactured in Japan",
    },
    "loratadine": {
        "names_ja": ("ロラタジン", "クラリチン", "アレグラ"),
        "names_en": ("loratadine", "claritin", "allegra", "fexofenadine"),
        "products_ja": [
            ("アレグラFX 60mg", "12錠", "約1,200〜1,600円"),
            ("クラリチンEX 10mg", "12錠", "約1,000〜1,400円"),
        ],
        "products_en": [
            ("Antihistamine tablets (e.g. fexofenadine)", "12 tabs", "approx. ¥1,200–1,600"),
        ],
        "dose_ja": "パッケージ記載どおり、1日1〜2回",
        "dose_en": "Follow package directions, usually 1–2× daily",
    },
    "cetirizine": {
        "names_ja": ("セチリジン", "ザイザル", "アレジオン"),
        "names_en": ("cetirizine", "zyrtec"),
        "products_ja": [
            ("ザイザルEX 10mg", "10錠", "約1,100〜1,500円"),
            ("アレジオン10 10mg", "12錠", "約900〜1,300円"),
        ],
        "products_en": [
            ("Cetirizine 10 mg", "10 tabs", "approx. ¥1,100–1,500"),
        ],
        "dose_ja": "成人：1日1回1錠",
        "dose_en": "Adults: 1 tablet once daily",
    },
    "dextromethorphan": {
        "names_ja": ("デキストロメトルファン", "ストナ", "ベンザブロック"),
        "names_en": ("dextromethorphan", "cough syrup"),
        "products_ja": [
            ("ストナ去痰カプセル", "24カプセル", "約900〜1,300円"),
            ("新セキリック液", "120ml", "約800〜1,200円"),
        ],
        "products_en": [
            ("OTC cough suppressant syrup", "120 ml", "approx. ¥800–1,200"),
        ],
        "dose_ja": "パッケージ記載どおり",
        "dose_en": "Follow package directions",
    },
    "sleep_aid": {
        "names_ja": ("ドリエル", "睡眠改善薬", "イブクイック"),
        "names_en": ("diphenhydramine", "sleep aid", "doxylamine"),
        "products_ja": [
            ("ドリエルα 12錠", "12錠", "約1,000〜1,400円"),
        ],
        "products_en": [
            ("OTC sleep aid tablets", "12 tabs", "approx. ¥1,000–1,400"),
        ],
        "dose_ja": "就寝前に1回、短期間のみ（2週間以内）",
        "dose_en": "One dose before bed, short-term only (within 2 weeks)",
    },
    "antacid": {
        "names_ja": ("制酸剤", "ガスター", "太田胃散"),
        "names_en": ("antacid", "gaviscon"),
        "products_ja": [
            ("ガスター10 20錠", "20錠", "約900〜1,300円"),
            ("太田胃散", "48包", "約1,200〜1,800円"),
        ],
        "products_en": [
            ("Antacid tablets", "20 tabs", "approx. ¥900–1,300"),
        ],
        "dose_ja": "食後・就寝前にパッケージ記載どおり",
        "dose_en": "After meals / before bed per package",
    },
}


def _detect_meds_in_text(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for key, info in OTC_MEDICATIONS.items():
        names = info["names_ja"] + info["names_en"]
        if any(n.lower() in lower or n in text for n in names):
            found.append(key)
    return found


def enrich_medication_advice(advice: str, category: Optional[str], lang: str) -> str:
    """Append OTC product names and approximate prices when medication advice is given."""
    if not advice:
        return advice

    keys = _detect_meds_in_text(advice)
    if not keys and category:
        category_defaults = {
            "fever": ["acetaminophen"],
            "headache": ["acetaminophen", "ibuprofen"],
            "cough_cold": ["acetaminophen", "dextromethorphan"],
            "hay_fever": ["loratadine", "cetirizine"],
            "skin": ["loratadine"],
            "stomach": ["antacid"],
            "general": [],
        }
        keys = category_defaults.get(category, [])

    if not keys:
        return advice

    if lang == "ja":
        lines = ["\n\n【市販薬の目安（ドラッグストア）】"]
        for key in keys[:4]:
            info = OTC_MEDICATIONS[key]
            lines.append(f"・{info['dose_ja']}")
            for name, size, price in info["products_ja"][:2]:
                lines.append(f"  - {name}（{size}）… {price}")
        lines.append("※価格は店舗・地域により異なります。薬剤師にご相談ください。")
    else:
        lines = ["\n\n【OTC price guide (drugstores)】"]
        for key in keys[:4]:
            info = OTC_MEDICATIONS[key]
            lines.append(f"· {info['dose_en']}")
            for name, size, price in info["products_en"][:2]:
                lines.append(f"  - {name} ({size}) … {price}")
        lines.append("※Prices vary by store and region. Ask a pharmacist for guidance.")

    return advice + "\n".join(lines)


def enrich_medication_origin(advice: str, category: Optional[str], lang: str) -> str:
    """Append manufacturer and usage details (premium feature)."""
    if not advice:
        return advice
    keys = _detect_meds_in_text(advice)
    if not keys and category:
        category_defaults = {
            "fever": ["acetaminophen"],
            "headache": ["acetaminophen", "ibuprofen"],
            "cough_cold": ["acetaminophen", "dextromethorphan"],
            "hay_fever": ["loratadine", "cetirizine"],
            "skin": ["loratadine"],
            "stomach": ["antacid"],
        }
        keys = category_defaults.get(category, [])
    if not keys:
        return advice

    if lang == "ja":
        lines = ["\n\n【お薬の使い方・製造元】"]
        for key in keys[:3]:
            info = OTC_MEDICATIONS[key]
            lines.append(f"・{info.get('usage_ja', info['dose_ja'])}")
            lines.append(f"  製造販売元: {info.get('manufacturer_ja', '国内メーカー')}")
            lines.append(f"  製造・由来: {info.get('origin_ja', '日本')}")
    else:
        lines = ["\n\n【Usage & manufacturer】"]
        for key in keys[:3]:
            info = OTC_MEDICATIONS[key]
            lines.append(f"· {info.get('usage_en', info['dose_en'])}")
            lines.append(f"  Manufacturer: {info.get('manufacturer_en', 'Domestic brand')}")
            lines.append(f"  Origin: {info.get('origin_en', 'Japan')}")
    return advice + "\n".join(lines)


def medication_keywords_in_text(text: str) -> list[str]:
    """Return Japanese/English drug names found in text (for AI validation)."""
    found: list[str] = []
    for info in OTC_MEDICATIONS.values():
        for n in info["names_ja"]:
            if n in text:
                found.append(n)
        for n in info["names_en"]:
            if n.lower() in text.lower():
                found.append(n)
    return found
