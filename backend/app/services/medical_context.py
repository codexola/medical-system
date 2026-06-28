"""Gather medical context from database knowledge and public web sources."""

from __future__ import annotations

import re
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FAQ, KnowledgeDocument


async def load_db_medical_context(db: AsyncSession, query: str, lang: str) -> str:
    snippets: list[str] = []
    words = [w for w in re.split(r"\s+", query) if len(w) >= 2]

    faq_result = await db.execute(
        select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order)  # noqa: E712
    )
    for faq in faq_result.scalars():
        q = faq.question if lang == "ja" else (faq.question_en or faq.question)
        a = faq.answer if lang == "ja" else (faq.answer_en or faq.answer)
        if any(w in f"{q} {a}" for w in words) or any(w in query for w in (q[:6],) if len(q) >= 6):
            snippets.append(f"{q}: {a}")

    doc_result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.is_active == True).limit(20)  # noqa: E712
    )
    for doc in doc_result.scalars():
        if not doc.content:
            continue
        if any(w in doc.content or w in doc.title for w in words) or doc.category in ("medication", "guideline", "treatment"):
            if any(w in doc.content or w in doc.title for w in words):
                snippets.append(f"{doc.title}: {doc.content[:400]}")

    return "\n".join(snippets[:4])


async def fetch_public_medical_snippets(symptoms: str, lang: str) -> str:
    """Fetch brief public reference text (DuckDuckGo instant answers / related topics)."""
    topic = symptoms[:80].strip()
    if not topic:
        return ""

    search_q = f"{topic} 症状 対処" if lang == "ja" else f"{topic} symptoms treatment"
    snippets: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": search_q, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                abstract = (data.get("AbstractText") or "").strip()
                if abstract and len(abstract) > 30:
                    source = data.get("AbstractSource") or "public reference"
                    snippets.append(f"[{source}] {abstract[:500]}")
                for topic_item in (data.get("RelatedTopics") or [])[:3]:
                    if isinstance(topic_item, dict) and topic_item.get("Text"):
                        snippets.append(topic_item["Text"][:200])
    except Exception:
        pass

    return "\n".join(snippets[:3])
