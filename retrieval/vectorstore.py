"""
Vector store — Zilliz Cloud (Milvus-compatible).

Handles:
  - Collection creation with schema (auto-creates if not exists)
  - Inserting chunks + embeddings with metadata
  - Cosine similarity search with optional doc_id filter
  - Deleting all vectors for a given doc_id
"""

import os
import logging
from pymilvus import (
    MilvusClient,
    DataType,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "rag_chunks"
EMBEDDING_DIM = 1536
TOP_K_RETRIEVE = 10   # how many to fetch before reranking


def _get_client() -> MilvusClient:
    uri = os.getenv("ZILLIZ_URI")
    token = os.getenv("ZILLIZ_TOKEN")
    if not uri or not token:
        raise RuntimeError("ZILLIZ_URI and ZILLIZ_TOKEN must be set in environment")
    return MilvusClient(uri=uri, token=token)


def _ensure_collection(client: MilvusClient) -> None:
    """Create collection if it doesn't already exist."""
    if client.has_collection(COLLECTION_NAME):
        return

    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    schema.add_field("doc_id", DataType.VARCHAR, max_length=256)
    schema.add_field("source", DataType.VARCHAR, max_length=512)
    schema.add_field("page", DataType.INT64)
    schema.add_field("chunk_id", DataType.INT64)
    schema.add_field("char_start", DataType.INT64)
    schema.add_field("char_end", DataType.INT64)
    schema.add_field("text", DataType.VARCHAR, max_length=4096)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )
    logger.info("Created Zilliz collection '%s'", COLLECTION_NAME)


def insert_chunks(chunks: list[dict], embeddings: list[list[float]], doc_id: str) -> int:
    """
    Insert chunk records + their embedding vectors into Zilliz.

    Args:
        chunks: output of chunker — list of chunk dicts
        embeddings: parallel list of float vectors
        doc_id: unique document identifier

    Returns:
        Number of records inserted
    """
    client = _get_client()
    _ensure_collection(client)

    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append(
            {
                "id": _make_id(doc_id, chunk["chunk_id"]),
                "embedding": emb,
                "doc_id": doc_id,
                "source": chunk["source"],
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "text": chunk["text"][:4000],  # guard against max_length
            }
        )

    client.insert(collection_name=COLLECTION_NAME, data=rows)
    logger.info("Inserted %d chunks for doc_id='%s'", len(rows), doc_id)
    return len(rows)


def search(query_embedding: list[float], doc_id: str | None = None, top_k: int = TOP_K_RETRIEVE) -> list[dict]:
    """
    Retrieve top-k most similar chunks by cosine similarity.

    Args:
        query_embedding: embedded query vector
        doc_id: optional filter — if given, search only within this document
        top_k: number of results to return

    Returns:
        list of result dicts: {chunk_id, doc_id, source, page, text, score, char_start, char_end}
    """
    client = _get_client()
    _ensure_collection(client)

    filter_expr = f'doc_id == "{doc_id}"' if doc_id else None

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        anns_field="embedding",
        search_params={"metric_type": "COSINE"},
        limit=top_k,
        filter=filter_expr,
        output_fields=["chunk_id", "doc_id", "source", "page", "text", "char_start", "char_end"],
    )

    hits = []
    for hit in results[0]:
        entity = hit.get("entity", {})
        hits.append(
            {
                "chunk_id": entity.get("chunk_id"),
                "doc_id": entity.get("doc_id"),
                "source": entity.get("source"),
                "page": entity.get("page"),
                "text": entity.get("text"),
                "char_start": entity.get("char_start"),
                "char_end": entity.get("char_end"),
                "score": hit.get("distance", 0.0),
            }
        )
    return hits


def delete_doc(doc_id: str) -> None:
    """Delete all chunks belonging to a document."""
    client = _get_client()
    _ensure_collection(client)
    client.delete(
        collection_name=COLLECTION_NAME,
        filter=f'doc_id == "{doc_id}"',
    )
    logger.info("Deleted all chunks for doc_id='%s'", doc_id)


def _make_id(doc_id: str, chunk_id: int) -> int:
    """Create a stable integer primary key from doc_id + chunk_id."""
    return abs(hash(f"{doc_id}_{chunk_id}")) % (2**31)
