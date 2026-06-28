from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import RAGIndexRequest, RAGQuery
from app.database.session import get_db
from app.rag.service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query")
async def rag_query(data: RAGQuery, db: AsyncSession = Depends(get_db)):
    service = RAGService(db)
    answer = await service.answer_with_rag(data.query, data.language)
    results = await service.search(data.query, category=data.category)
    return {"answer": answer, "sources": results}


@router.post("/index")
async def index_document(data: RAGIndexRequest, db: AsyncSession = Depends(get_db)):
    service = RAGService(db)
    doc_id = await service.index_document(data.title, data.content, data.category, data.language)
    return {"document_id": str(doc_id), "status": "indexed"}


@router.post("/search")
async def rag_search(data: RAGQuery, db: AsyncSession = Depends(get_db)):
    service = RAGService(db)
    results = await service.search(data.query, category=data.category)
    return {"results": results}
