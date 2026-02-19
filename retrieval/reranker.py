"""
Cross-encoder reranker.

Uses sentence-transformers cross-encoder/ms-marco-MiniLM-L-6-v2 to rerank
the top-10 vector search results and return only the top-5 most relevant.
"""

import logging
from functools import lru_cache
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_N_AFTER_RERANK = 5


@lru_cache(maxsize=1)
def _get_model() -> CrossEncoder:
    """Load the cross-encoder once and cache it for the process lifetime."""
    logger.info("Loading cross-encoder model '%s' ...", CROSS_ENCODER_MODEL)
    return CrossEncoder(CROSS_ENCODER_MODEL)


def rerank(query: str, candidates: list[dict], top_n: int = TOP_N_AFTER_RERANK) -> list[dict]:
    """
    Rerank candidate chunks using a cross-encoder.

    Args:
        query: the user's original question
        candidates: list of chunk dicts from vector search (each has 'text' key)
        top_n: number of top results to keep after reranking

    Returns:
        top_n chunk dicts, sorted best-first, with 'rerank_score' added
    """
    if not candidates:
        return []

    model = _get_model()

    # Build (query, passage) pairs for the cross-encoder
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)

    # Attach scores and sort descending
    for chunk, score in zip(candidates, scores):
        chunk["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return reranked[:top_n]
