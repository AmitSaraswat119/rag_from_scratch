"""
LLM Generator.

Constructs a strict RAG prompt and calls OpenAI GPT-4o (default) or
Anthropic Claude. Returns the answer text and a list of cited source indices.

No hallucination: the prompt explicitly instructs the model to say
"I don't have enough information" when the answer is not in the provided context.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
MAX_CONTEXT_CHUNKS = 5


def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    """
    Generate an answer grounded in the provided context chunks.

    Args:
        query: the user's question
        context_chunks: top-N reranked chunks, each with 'text', 'page', 'source', 'chunk_id'

    Returns:
        {
          "answer": str,
          "sources": [ {chunk_id, text, page, source, score} ]
        }
    """
    if not context_chunks:
        return {
            "answer": "I don't have enough information to answer this question.",
            "sources": [],
        }

    context_str = _build_context(context_chunks)
    prompt = _build_prompt(query, context_str)

    answer_text = _call_openai(prompt)

    sources = [
        {
            "chunk_id": c.get("chunk_id"),
            "text": c.get("text", ""),
            "page": c.get("page"),
            "source": c.get("source"),
            "score": round(c.get("rerank_score", c.get("score", 0.0)), 4),
        }
        for c in context_chunks
    ]

    return {"answer": answer_text, "sources": sources}


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Source {i + 1}] (File: {chunk.get('source', 'unknown')}, Page: {chunk.get('page', '?')})\n"
            f"{chunk.get('text', '')}"
        )
    return "\n\n---\n\n".join(parts)


def _build_prompt(query: str, context: str) -> str:
    return f"""You are a precise question-answering assistant.

Answer the user's question ONLY using the provided context below.

Rules:
1. Base your answer entirely on the context. Do not use prior knowledge.
2. Cite which source(s) you used by referencing [Source N] in your answer.
3. If the answer cannot be found in the context, respond with exactly:
   "I don't have enough information to answer this question."
4. Be concise and accurate.

Context:
{context}

Question: {query}

Answer:"""


def _call_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
