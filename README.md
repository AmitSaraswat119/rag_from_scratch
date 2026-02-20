---
title: Rag From Scratch
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# RAG From Scratch

**A Production-Style RAG Pipeline — No LangChain, Pure Python**

By Amit Saraswat | [github.com/AmitSaraswat119](https://github.com/AmitSaraswat119)

🚀 **Live Demo:** [rag-from-scratch.vercel.app](https://rag-from-scratch.vercel.app)
🔧 **Backend API:** [amit119-rag-from-scratch.hf.space](https://amit119-rag-from-scratch.hf.space)
📖 **API Docs:** [amit119-rag-from-scratch.hf.space/docs](https://amit119-rag-from-scratch.hf.space/docs)

---

## What is this?

RAG From Scratch is a Retrieval-Augmented Generation pipeline built entirely from first principles — no LangChain, no LlamaIndex, no abstractions. Every component is implemented manually in Python, from document chunking to vector search to LLM generation.

Users upload any PDF or TXT document, then ask natural language questions. Every response includes source citations showing exactly which part of the document the answer came from.

**Why no LangChain?** Most RAG tutorials wrap everything in LangChain and call it done. This project deliberately avoids that. Building each component manually forces a deep understanding of how RAG actually works — and that understanding is what separates engineers who can debug and optimize RAG systems from those who can only run tutorials.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI |
| **PDF Extraction** | pdfplumber |
| **Embeddings** | OpenAI text-embedding-3-small |
| **Vector Database** | Zilliz Cloud (Milvus) |
| **Reranker** | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| **LLM** | OpenAI GPT-4o |
| **Frontend** | React + Tailwind CSS + Vite |
| **Backend Hosting** | Hugging Face Spaces |
| **Frontend Hosting** | Vercel |

---

## Architecture

```
Upload Flow:
  PDF/TXT → Extract → Clean → Chunk (500 words, 50 overlap)
          → Embed (OpenAI) → Store in Zilliz

Chat Flow:
  Question → Embed → Vector Search (top 10)
           → Rerank (cross-encoder, top 5)
           → Generate (GPT-4o, strict prompt)
           → Answer + Source Citations
```

---

## Project Structure

```
rag-from-scratch/
├── ingestion/
│   ├── loader.py        # PDF + TXT text extraction
│   ├── chunker.py       # Sliding window chunking
│   └── embedder.py      # OpenAI embeddings + batching
├── retrieval/
│   ├── vectorstore.py   # Zilliz connection + search
│   └── reranker.py      # Cross-encoder reranking
├── generation/
│   └── generator.py     # LLM prompt + citations
├── api/
│   └── main.py          # FastAPI endpoints
├── frontend/
│   └── src/
│       ├── App.jsx      # Tab layout
│       ├── Upload.jsx   # File upload
│       └── Chat.jsx     # Chat + source citations
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/upload` | Ingest PDF or TXT |
| `POST` | `/query` | Ask a question |
| `GET` | `/docs-list` | List uploaded documents |

### POST /upload
```json
// Request: multipart/form-data { file: <PDF or TXT> }
// Response:
{
  "doc_id": "uuid",
  "filename": "document.pdf",
  "chunks_stored": 42,
  "status": "ready"
}
```

### POST /query
```json
// Request:
{ "question": "What is RAG?", "doc_id": "uuid" }

// Response:
{
  "answer": "RAG stands for... [Source 1]",
  "sources": [
    { "chunk_id": 3, "text": "...", "page": 2, "score": 0.91 }
  ]
}
```

---

## Run Locally

### 1. Clone the repo
```bash
git clone https://github.com/AmitSaraswat119/rag-from-scratch.git
cd rag-from-scratch
```

### 2. Backend setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set environment variables
```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, ZILLIZ_URI, ZILLIZ_TOKEN
```

### 4. Start backend
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `ZILLIZ_URI` | ✅ | Zilliz Cloud cluster URI |
| `ZILLIZ_TOKEN` | ✅ | Zilliz Cloud API token |
| `LLM_MODEL` | ❌ | LLM model (default: `gpt-4o`) |
| `CORS_ORIGINS` | ❌ | Allowed origins (default: `*`) |

---

## License

MIT
