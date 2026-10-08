# rag_routes.py — document upload and RAG Q&A endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from rag import ingest_document, answer_with_rag

router = APIRouter(tags=["RAG"])


class IngestRequest(BaseModel):
    ticker:  str
    title:   str
    text:    str
    section: str = "General"


class RagQueryRequest(BaseModel):
    query:  str
    ticker: Optional[str] = None


@router.post("/documents/ingest")
def ingest(data: IngestRequest):
    try:
        return ingest_document(data.ticker, data.title, data.text, data.section)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/documents/ask")
def ask(data: RagQueryRequest):
    try:
        return answer_with_rag(data.query, data.ticker)
    except Exception as e:
        raise HTTPException(500, detail=str(e))