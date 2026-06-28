import uuid
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIMessage
from app.ai.service import AIService
from app.config import get_settings
from app.models import KnowledgeChunk, KnowledgeDocument

settings = get_settings()


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = AIService()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self.ai.embed(texts)

    async def chunk_text(self, text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    async def index_document(
        self, title: str, content: str, category: str, language: str = "ja"
    ) -> uuid.UUID:
        doc = KnowledgeDocument(title=title, content=content, category=category, language=language)
        self.db.add(doc)
        await self.db.flush()

        chunks = await self.chunk_text(content)
        embeddings = await self.embed_texts(chunks)

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=chunk_text,
                chunk_index=i,
                embedding=embedding,
                metadata_={"category": category, "language": language},
            )
            self.db.add(chunk)

        await self.db.flush()
        return doc.id

    async def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> list[dict]:
        query_embedding = (await self.embed_texts([query]))[0]
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = """
            SELECT kc.content, kc.metadata, kd.title, kd.category,
                   1 - (kc.embedding <=> :embedding::vector) AS similarity
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kc.document_id = kd.id
            WHERE kd.is_active = true
        """
        params: dict = {"embedding": embedding_str, "top_k": top_k}

        if category:
            sql += " AND kd.category = :category"
            params["category"] = category

        sql += " ORDER BY kc.embedding <=> :embedding::vector LIMIT :top_k"

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        return [
            {
                "content": row[0],
                "metadata": row[1],
                "title": row[2],
                "category": row[3],
                "similarity": float(row[4]),
            }
            for row in rows
        ]

    async def answer_with_rag(self, query: str, language: str = "ja") -> str:
        results = await self.search(query, top_k=5)
        if not results:
            return "申し訳ございませんが、関連する情報が見つかりませんでした。" if language == "ja" else "Sorry, no relevant information found."

        context = "\n\n".join(
            f"[{r['title']} - {r['category']}]\n{r['content']}" for r in results
        )

        lang_instruction = (
            "患者と同じ言語で、知識ベースの内容に基づき正確に答えてください。推測はしないでください。"
            if language == "ja"
            else "Answer accurately based on the knowledge base in the same language as the patient. Do not guess."
        )
        messages = [
            AIMessage(
                role="system",
                content=f"You are a healthcare information assistant. Use ONLY the following knowledge to answer. {lang_instruction}\n\nKnowledge:\n{context}",
            ),
            AIMessage(role="user", content=query),
        ]

        response = await self.ai.chat(messages, temperature=0.2)
        return response.content
