"""
FastAPI backend — RAG From Scratch.

Endpoints:
  POST /upload  — ingest a PDF or TXT document
  POST /query   — answer a question using the RAG pipeline
  GET  /health  — liveness probe
  GET  /docs    — list all uploaded documents
"""

import io
import os
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

from ingestion.loader import load_pdf, load_txt
from ingestion.chunker import chunk_pages
from ingestion.embedder import embed_texts, embed_query
from retrieval.vectorstore import insert_chunks, search
from retrieval.reranker import rerank
from generation.generator import generate_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory registry of uploaded documents (survives only for process lifetime)
# { doc_id: { filename, chunks_stored } }
_doc_registry: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG From Scratch API starting up")
    yield
    logger.info("RAG From Scratch API shutting down")


app = FastAPI(
    title="RAG From Scratch",
    description="Production-style RAG pipeline — no LangChain, pure Python",
    version="1.0.0",
    lifespan=lifespan,
)

# Read allowed origins from CORS_ORIGINS env var (comma-separated).
# Example in .env:
#   CORS_ORIGINS=http://localhost:5173,https://your-app.vercel.app
# Falls back to "*" (open) if not set — safe for local dev.
_raw_origins = os.getenv("CORS_ORIGINS", "*")
if _raw_origins.strip() == "*":
    _allow_origins = ["*"]
else:
    _allow_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_origins != ["*"],  # credentials not allowed with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    doc_id: str | None = None


class SourceChunk(BaseModel):
    chunk_id: int | None
    text: str
    page: int | None
    source: str | None
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_stored: int
    status: str


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    chunks_stored: int


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/docs-list", response_model=list[DocumentInfo])
def list_documents():
    """Return all documents uploaded in the current session."""
    return [
        DocumentInfo(doc_id=k, filename=v["filename"], chunks_stored=v["chunks_stored"])
        for k, v in _doc_registry.items()
    ]


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Ingest a PDF or TXT file through the full pipeline:
    extract → chunk → embed → store in Zilliz.
    """
    filename = file.filename or "unknown"
    content_type = file.content_type or ""

    # Validate file type
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported.",
        )

    file_bytes = await file.read()
    logger.info("Received file '%s' (%d bytes)", filename, len(file_bytes))

    # 1. Extract text
    try:
        if filename.lower().endswith(".pdf"):
            pages = load_pdf(io.BytesIO(file_bytes), filename)
        else:
            pages = load_txt(file_bytes, filename)
    except Exception as e:
        logger.exception("Text extraction failed")
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {e}")

    if not pages:
        raise HTTPException(status_code=422, detail="No text could be extracted from the file.")

    # 2. Chunk
    chunks = chunk_pages(pages)
    if not chunks:
        raise HTTPException(status_code=422, detail="Document produced no chunks after chunking.")
    logger.info("Produced %d chunks", len(chunks))

    # 3. Embed
    try:
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
    except Exception as e:
        logger.exception("Embedding failed")
        raise HTTPException(status_code=502, detail=f"Embedding failed: {e}")

    # 4. Store in Zilliz
    doc_id = str(uuid.uuid4())
    try:
        stored = insert_chunks(chunks, embeddings, doc_id)
    except Exception as e:
        logger.exception("Vector store insert failed")
        raise HTTPException(status_code=502, detail=f"Vector store insert failed: {e}")

    _doc_registry[doc_id] = {"filename": filename, "chunks_stored": stored}

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        chunks_stored=stored,
        status="ready",
    )


@app.post("/query", response_model=QueryResponse)
def query_document(body: QueryRequest):
    """
    Answer a question using the RAG pipeline:
    embed → retrieve → rerank → generate.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Embed query
    try:
        q_embedding = embed_query(question)
    except Exception as e:
        logger.exception("Query embedding failed")
        raise HTTPException(status_code=502, detail=f"Query embedding failed: {e}")

    # 2. Vector search
    try:
        candidates = search(q_embedding, doc_id=body.doc_id)
    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=502, detail=f"Vector search failed: {e}")

    if not candidates:
        return QueryResponse(
            answer="I don't have enough information to answer this question.",
            sources=[],
        )

    # 3. Rerank
    top_chunks = rerank(question, candidates)

    # 4. Generate
    try:
        result = generate_answer(question, top_chunks)
    except Exception as e:
        logger.exception("Generation failed")
        raise HTTPException(status_code=502, detail=f"Answer generation failed: {e}")

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
    )
