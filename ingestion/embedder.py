"""
Embedder — calls OpenAI text-embedding-3-small directly.

Handles batching (max 100 texts per request) and exponential-backoff retries
on rate-limit errors. No wrapper libraries used.
"""

import os
import time
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100
MAX_RETRIES = 5


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings.  Returns a list of float vectors in the same order.
    Automatically batches and retries on rate-limit errors.
    """
    client = get_client()
    all_embeddings: list[list[float]] = []

    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch = texts[batch_start : batch_start + BATCH_SIZE]
        embeddings = _embed_batch(client, batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]


def _embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed one batch with exponential-backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )
            # response.data is ordered to match input
            return [item.embedding for item in response.data]
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                wait = 2 ** attempt
                logger.warning("Rate limit hit — retrying in %ds (attempt %d/%d)", wait, attempt + 1, MAX_RETRIES)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Failed to embed batch after {MAX_RETRIES} retries")
