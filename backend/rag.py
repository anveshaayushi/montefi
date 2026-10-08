# rag.py — document ingestion, embedding, and retrieval for RAG
import re
import json
import datetime
import numpy as np
import google.generativeai as genai
from typing import List, Dict
from config import GEMINI_API_KEY
from document_chunk import DocumentChunk

genai.configure(api_key=GEMINI_API_KEY)

EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL   = "gemini-3.8-flash"


def _split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks, breaking on paragraph boundaries where possible."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if len(current) > overlap else current
            current = tail + "\n\n" + para
    if current:
        chunks.append(current)
    return chunks


def _embed_text(text: str) -> List[float]:
    result = genai.embed_content(model=EMBED_MODEL, content=text)
    return result["embedding"]


def ingest_document(ticker: str, title: str, text: str, section: str = "General") -> Dict:
    """Chunk a document, embed each chunk, store in the database."""
    chunks = _split_into_chunks(text)
    now = datetime.datetime.utcnow()
    stored = 0

    for chunk_text in chunks:
        labeled_text = f"[{ticker} - {section}]\n{chunk_text}"
        embedding = _embed_text(labeled_text)
        DocumentChunk.create(
            ticker=ticker.upper(),
            title=title,
            section=section,
            chunk_text=chunk_text,
            embedding=json.dumps(embedding),
            created_at=now,
        )
        stored += 1

    return {"ticker": ticker.upper(), "title": title, "chunks_stored": stored}


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve_relevant_chunks(query: str, ticker: str = None, top_k: int = 4) -> List[Dict]:
    """Embed the query, compare against stored chunks, return the most relevant ones."""
    query_embedding = np.array(_embed_text(query))

    q = DocumentChunk.select()
    if ticker:
        q = q.where(DocumentChunk.ticker == ticker.upper())

    scored = []
    for chunk in q:
        chunk_embedding = np.array(chunk.get_embedding())
        score = _cosine_similarity(query_embedding, chunk_embedding)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    return [
        {
            "ticker":     c.ticker,
            "title":      c.title,
            "section":    c.section,
            "chunk_text": c.chunk_text,
            "similarity": round(s, 4),
        }
        for s, c in top
    ]


def answer_with_rag(query: str, ticker: str = None) -> Dict:
    """Retrieve relevant chunks, then ask Gemini to answer grounded in them."""
    chunks = retrieve_relevant_chunks(query, ticker=ticker, top_k=4)

    if not chunks:
        return {
            "answer": "No relevant documents found. Try uploading a filing for this ticker first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        f"[Source: {c['title']} - {c['section']}]\n{c['chunk_text']}" for c in chunks
    )

    model = genai.GenerativeModel(GEN_MODEL)
    prompt = f"""Answer the question using ONLY the context below. If the context doesn't contain
enough information to answer, say so clearly. Cite which source section each claim comes from.

Context:
{context}

Question: {query}

Answer:"""

    response = model.generate_content(prompt)

    return {
        "answer": response.text,
        "sources": [
            {"title": c["title"], "section": c["section"], "similarity": c["similarity"]}
            for c in chunks
        ],
    }